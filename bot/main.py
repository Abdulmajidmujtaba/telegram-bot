"""
Main module for the Telegram Summary Bot.

This module defines the main `SummaryBot` class, responsible for:
- Initializing the Telegram bot application.
- Setting up command and message handlers.
- Scheduling periodic tasks (like daily summaries).
- Handling graceful shutdown.

It also contains the main asynchronous `main` function that runs the bot.
"""
import asyncio
import logging
import datetime
import pytz
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from bot.config import TELEGRAM_BOT_TOKEN, LOG_LEVEL, LOG_FORMAT
from bot.services.ai_service import AIService
from bot.services.message_service import MessageService
from bot.handlers.command_handlers import CommandHandlers
from bot.handlers.message_handlers import MessageHandlers
from bot.config import SUMMARY_TIMEZONE, SUMMARY_START_HOUR, SUMMARY_END_HOUR

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL)
)

logger = logging.getLogger(__name__)


class SummaryBot:
    """
    Orchestrates the Telegram Summary Bot's operations.

    Initializes services, sets up handlers, configures commands, schedules jobs,
    and manages the bot's lifecycle.
    """
    
    def __init__(self):
        """
        Initializes the bot application, services, and handlers.

        Configures the Telegram Application builder with specific timeouts
        for network operations (connect, read, write, pool).
        Instantiates AI and message services, and command/message handlers.
        """
        # Set up application with better connect/read timeouts
        builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
        
        # Set connection and read timeouts for bot requests
        builder.connect_timeout(20)   # 20 seconds for connection
        builder.read_timeout(30)      # 30 seconds for read
        builder.write_timeout(30)     # 30 seconds for write
        builder.pool_timeout(30)      # 30 seconds for connection pool
        
        self.application = builder.build()
        
        # Initialize services
        self.ai_service = AIService()
        self.message_service = MessageService()
        
        # Initialize handlers
        self.command_handlers = CommandHandlers(self.ai_service, self.message_service)
        self.message_handlers = MessageHandlers(self.message_service)
    
    async def setup_commands(self):
        """
        Sets the list of available commands for the bot in the Telegram interface.

        These commands appear in the menu when users interact with the bot.
        """
        commands = [
            BotCommand("start", "Start interacting with the bot"),
            BotCommand("help", "Display help menu"),
            BotCommand("summary", "Summarize the last 24h of messages"),
            BotCommand("proof", "Verify a statement for truthfulness"),
            BotCommand("comment", "Comment on the current discussion"),
            BotCommand("gpt", "Answer a question using AI")
        ]
        
        await self.application.bot.set_my_commands(commands)
    
    def register_handlers(self):
        """
        Registers command, message, and chat member update handlers.

        Connects user commands (e.g., /summary) and message types (text,
        new members) to their respective handler functions.
        Also registers a global error handler.
        """
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.command_handlers.start))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help))
        self.application.add_handler(CommandHandler("summary", self.command_handlers.summary))
        self.application.add_handler(CommandHandler("proof", self.command_handlers.proof))
        self.application.add_handler(CommandHandler("comment", self.command_handlers.comment))
        self.application.add_handler(CommandHandler("gpt", self.command_handlers.gpt))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.message_handlers.handle_text_message
        ))
        
        # Chat member handlers
        self.application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS, 
            self.message_handlers.handle_new_chat_members
        ))
        
        self.application.add_handler(MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER, 
            self.message_handlers.handle_left_chat_member
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    def schedule_daily_summaries(self):
        """
        Schedules a recurring job to check for sending daily summaries.

        The job runs hourly to check if the current time falls within the
        configured summary window (SUMMARY_START_HOUR to SUMMARY_END_HOUR).
        """
        self.application.job_queue.run_repeating(
            self.send_scheduled_summaries,
            interval=3600,  # Check every hour
            first=0
        )
    
    async def send_scheduled_summaries(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Sends daily summaries to active chats during the configured time window.

        This method is called periodically by the job queue. It checks the current
        time against the configured SUMMARY_START_HOUR and SUMMARY_END_HOUR.
        If within the window, it iterates through active chats, generates a summary
        for the past 24 hours (if one hasn't been sent today), and sends it.
        """
        now = datetime.datetime.now(SUMMARY_TIMEZONE)
        
        # Check if it's summary time
        if SUMMARY_START_HOUR <= now.hour < SUMMARY_END_HOUR:
            # Get list of chats where the bot is active
            chat_ids = context.bot_data.get('active_chats', [])
            
            for chat_id in chat_ids:
                try:
                    # Check if we already sent a summary today
                    last_summary = context.bot_data.get(f'last_summary_{chat_id}', None)
                    if last_summary and last_summary.date() == now.date():
                        continue
                    
                    # Get chat object
                    chat = await context.bot.get_chat(chat_id)
                    
                    # Get recent messages
                    messages = await self.message_service.get_recent_messages(chat, context)
                    
                    if messages:
                        # Generate summary
                        summary = await self.ai_service.generate_summary(messages)
                        
                        # Send summary
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"📅 *Daily Summary ({now.strftime('%Y-%m-%d')})*\n\n{summary}",
                            parse_mode="Markdown"
                        )
                        
                        # Update last summary time
                        context.bot_data[f'last_summary_{chat_id}'] = now
                        
                except Exception as e:
                    logger.error(f"Error sending scheduled summary to chat {chat_id}: {str(e)}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Logs errors caused by updates.

        This function is registered as the default error handler for the
        Telegram application.
        """
        logger.error(f"Update {update} caused error: {context.error}")


async def main():
    """
    Initializes and runs the Telegram Summary Bot.

    Creates the SummaryBot instance, sets up commands, registers handlers,
    schedules jobs, and starts the bot's polling loop.
    Handles graceful shutdown based on the `shutdown_event`.
    """
    bot = SummaryBot()
    
    try:
        # Import the shutdown event from run.py
        from run import shutdown_event
        
        # Initialize and start the bot
        await bot.setup_commands()
        bot.register_handlers()
        bot.schedule_daily_summaries()
        
        # Start the application
        await bot.application.initialize()
        await bot.application.start()
        
        # Configure the updater with more resilient settings
        bot.application.updater.bootstrap_retries = 5
        # Start polling with shorter polling interval and graceful shutdown
        await bot.application.updater.start_polling(
            poll_interval=1.0,  # Check for updates every second
            timeout=10,         # Timeout for long polling
            bootstrap_retries=5,  # Number of retries if bootstrapping fails
            read_timeout=10,    # Read timeout for getting updates
            write_timeout=10,   # Write timeout for webhook
            connect_timeout=10, # Connection timeout
            pool_timeout=10     # Pool timeout
        )
        
        logger.info("Bot started successfully!")
        
        # Wait for shutdown signal
        try:
            # Wait for shutdown signal with periodic checks to ensure we can exit
            while not shutdown_event.is_set():
                try:
                    # Wait with timeout to check shutdown_event periodically
                    await asyncio.wait_for(shutdown_event.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Just continue the loop
                    continue
        except asyncio.CancelledError:
            logger.info("Main task cancelled")
    except Exception as e:
        logger.error(f"Error during bot initialization: {str(e)}")
        raise
    finally:
        logger.info("Shutting down bot...")
        # Ensure we always clean up properly with timeout
        try:
            # Stop the updater first (with timeout)
            if hasattr(bot, 'application') and hasattr(bot.application, 'updater'):
                shutdown_task = asyncio.create_task(bot.application.updater.stop())
                try:
                    await asyncio.wait_for(shutdown_task, timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning("Updater stop timed out")
            
            # Stop the application (with timeout)
            if hasattr(bot, 'application'):
                shutdown_task = asyncio.create_task(bot.application.stop())
                try:
                    await asyncio.wait_for(shutdown_task, timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning("Application stop timed out")
                
                # Final shutdown (with timeout)
                shutdown_task = asyncio.create_task(bot.application.shutdown())
                try:
                    await asyncio.wait_for(shutdown_task, timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning("Application shutdown timed out")
                    
            logger.info("Bot has been shut down")
        except Exception as e:
            logger.error(f"Error during bot shutdown: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user. Exiting...")
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}") 