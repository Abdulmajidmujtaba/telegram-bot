"""
Provides a service layer for interacting with the Telegram Bot API.

Encapsulates bot initialization, command/message handling, task scheduling,
and integration with AI and message storage services.
(Note: Contains functionality potentially duplicated in other modules like `bot.main`).
"""
import logging
import datetime
import asyncio
from typing import List, Callable, Dict, Any, Optional

from telegram import Update, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeDefault
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

from bot.config import TELEGRAM_BOT_TOKEN, SUMMARY_TIMEZONE, SUMMARY_START_HOUR, SUMMARY_END_HOUR
from bot.services.ai_service import AIService
from bot.services.message_service import MessageService

logger = logging.getLogger(__name__)

class TelegramService:
    """
    Manages the core operations of the Telegram bot application.

    Initializes the `python-telegram-bot` Application, sets up command scopes,
    registers handlers, schedules jobs, and contains the main run loop.
    """
    
    def __init__(self):
        """
        Initializes the Telegram Application, AI service, and Message service.
        Also initializes a dictionary to hold references to scheduled tasks.
        """
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.ai_service = AIService()
        self.message_service = MessageService()
        
        # Dictionary to store scheduled tasks
        self.scheduled_tasks = {}
    
    async def setup_commands(self) -> None:
        """
        Sets the list of available bot commands for different chat scopes.

        Defines separate command lists for private chats and group chats and sets
        them using `set_my_commands` with appropriate scopes.
        """
        # Commands for private chats
        private_commands = [
            BotCommand("start", "Start interacting with the bot"),
            BotCommand("help", "Display help menu")
        ]
        
        # Commands for group chats
        group_commands = [
            BotCommand("start", "Start interacting with the bot"),
            BotCommand("help", "Display help menu"),
            BotCommand("summary", "Summarize the last 24h of messages"),
            BotCommand("proof", "Verify a statement for truthfulness"),
            BotCommand("comment", "Comment on the current discussion"),
            BotCommand("gpt", "Answer a question using AI")
        ]
        
        # Set commands for different scopes
        await self.application.bot.set_my_commands(
            private_commands,
            scope=BotCommandScopeDefault()
        )
        
        await self.application.bot.set_my_commands(
            group_commands,
            scope=BotCommandScopeAllGroupChats()
        )
    
    def register_handlers(self) -> None:
        """
        Registers handlers for commands, regular text messages, and errors.

        Connects command strings (e.g., "start") and message filters (e.g., TEXT)
        to their corresponding handler methods within this service class.
        """
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("summary", self.summary_command))
        self.application.add_handler(CommandHandler("proof", self.proof_command))
        self.application.add_handler(CommandHandler("comment", self.comment_command))
        self.application.add_handler(CommandHandler("gpt", self.gpt_command))
        
        # Message handler for storing messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    def schedule_daily_summaries(self) -> None:
        """
        Schedules a recurring job to potentially send daily summaries.

        The job runs hourly (`interval=3600`) to check if the current time is within
        the designated summary window.
        """
        self.application.job_queue.run_repeating(
            self.send_scheduled_summaries,
            interval=3600,  # Check every hour
            first=0
        )
    
    async def send_scheduled_summaries(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Sends daily summaries to active chats if within the configured time window.

        Called hourly by the job queue. Checks the current time against
        `SUMMARY_START_HOUR` and `SUMMARY_END_HOUR`. If within the window,
        iterates through `context.bot_data['active_chats']`, generates summaries
        using `AIService`, and sends them, ensuring only one summary per chat per day.
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
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /start command.

        Sends a welcome message and registers the chat ID in `context.bot_data['active_chats']`.
        """
        chat_id = update.effective_chat.id
        
        # Add this chat to active chats list
        if 'active_chats' not in context.bot_data:
            context.bot_data['active_chats'] = []
            
        if chat_id not in context.bot_data['active_chats']:
            context.bot_data['active_chats'].append(chat_id)
        
        welcome_text = (
            "👋 Hello! I'm an AI-powered chat assistant. "
            "I can summarize messages, verify facts, answer questions, and more.\n\n"
            "Add me to a group chat and grant me admin rights to use all my features. "
            "Type /help to see what I can do!"
        )
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /help command.

        Displays a formatted user guide detailing bot usage and available commands.
        """
        help_text = (
            "🤖 *Bot User Guide* 🤖\n\n"
            "➠ Add the bot to your group chat and grant it administrator rights.\n"
            "➠ Between 20:00 - 22:00 (London Time) the bot will automatically publish "
            "a chat summary by analyzing the last 24 hours of messages using AI.\n"
            "➠ The bot cannot view messages posted before it was added to the chat.\n"
            "➠ You can use manual commands in the chat (see below).\n\n"
            "*Available Commands*\n"
            "/start - start interacting with the bot\n"
            "/help - display this menu\n\n"
            "*Group Chat Commands*\n"
            "/summary - prepare a summary of the group's messages from the last 24h\n"
            "/proof - ↩️ verify a statement for truthfulness\n"
            "/comment - comment on the current discussion topic\n"
            "/gpt - ↩️ answer a question using AI\n\n"
            "↩️ — commands should be sent as replies to user (not bot) messages posted after the bot was added to the chat"
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /summary command.

        Retrieves recent messages using `MessageService`, generates a summary using
        `AIService`, and sends it back. Works directly without requiring a reply.
        """
        progress_message = await update.message.reply_text(
            "Generating summary... This might take a moment.",
            reply_to_message_id=update.message.message_id
        )
        
        try:
            # Get recent messages
            messages = await self.message_service.get_recent_messages(
                update.effective_chat, 
                context
            )
            
            if not messages:
                await progress_message.edit_text("No recent messages found to summarize.")
                return
                
            # Generate summary
            summary = await self.ai_service.generate_summary(messages)
            
            # Send summary
            await progress_message.edit_text(
                f"📊 *Group Chat Summary*\n\n{summary}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't generate a summary at this time.")
    
    async def proof_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /proof command.

        Extracts the statement from the replied-to message, verifies it using
        `AIService`, and sends the result. Requires reply to a user message.
        """
        # Check if this is a reply to a message
        if not update.message.reply_to_message or update.message.reply_to_message.from_user.is_bot:
            await update.message.reply_text(
                "Please use this command as a reply to a user message containing a statement to verify.",
                reply_to_message_id=update.message.message_id
            )
            return
            
        statement = update.message.reply_to_message.text
        
        progress_message = await update.message.reply_text(
            f"Verifying the statement: \"{statement}\"... This might take a moment.",
            reply_to_message_id=update.message.message_id
        )
        
        try:
            # Verify statement
            result = await self.ai_service.verify_statement(statement)
            
            # Send verification result
            await progress_message.edit_text(
                f"✅ *Fact Check*\n\nStatement: \"{statement}\"\n\n{result}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error verifying statement: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't verify that statement at this time.")
    
    async def comment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /comment command.

        Retrieves recent messages (context) using `MessageService`, generates a comment
        using `AIService`, and sends it.
        """
        progress_message = await update.message.reply_text(
            "Analyzing the discussion and generating a comment... This might take a moment.",
            reply_to_message_id=update.message.message_id
        )
        
        try:
            # Get recent messages for context
            messages = await self.message_service.get_recent_messages(
                update.effective_chat, 
                context,
                hours=1  # Get messages from the last hour for context
            )
            
            if not messages:
                await progress_message.edit_text("I don't see any recent messages to comment on.")
                return
                
            # Generate comment
            comment = await self.ai_service.generate_comment(messages)
            
            # Send comment
            await progress_message.edit_text(
                f"💬 *AI Commentary*\n\n{comment}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error generating comment: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't generate a comment at this time.")
    
    async def gpt_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /gpt command.

        Extracts the question from the replied-to message, gets an answer using
        `AIService`, and sends it back. Requires reply to a user message.
        """
        # Check if this is a reply to a message
        if not update.message.reply_to_message or update.message.reply_to_message.from_user.is_bot:
            await update.message.reply_text(
                "Please use this command as a reply to a user message containing a question to answer.",
                reply_to_message_id=update.message.message_id
            )
            return
            
        question = update.message.reply_to_message.text
        
        progress_message = await update.message.reply_text(
            f"Answering: \"{question}\"... This might take a moment.",
            reply_to_message_id=update.message.message_id
        )
        
        try:
            # Answer question
            answer = await self.ai_service.answer_question(question)
            
            # Send answer
            await progress_message.edit_text(
                f"🤖 *AI Response*\n\nQuestion: \"{question}\"\n\n{answer}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't answer that question at this time.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles regular incoming text messages (non-commands).

        Stores the message using `MessageService`.
        """
        # Store message in history
        await self.message_service.store_message(update, context)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Logs errors encountered by the bot handlers.

        Registered via `application.add_error_handler`.
        """
        logger.error(f"Update {update} caused error: {context.error}")
        
    async def run(self) -> None:
        """
        Sets up, initializes, and runs the Telegram bot application indefinitely.

        Calls setup methods (`setup_commands`, `register_handlers`,
        `schedule_daily_summaries`), starts the application and its polling mechanism,
        and then blocks until a signal (like SIGINT) is received for graceful shutdown.
        Ensures proper application stop and shutdown in a finally block.
        """
        # Setup commands
        await self.setup_commands()
        
        # Register handlers
        self.register_handlers()
        
        # Schedule daily summaries
        self.schedule_daily_summaries()
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Bot started successfully!")
        
        # Keep the bot running
        try:
            await self.application.updater.stop_on_signal()
        finally:
            await self.application.stop()
            await self.application.shutdown() 