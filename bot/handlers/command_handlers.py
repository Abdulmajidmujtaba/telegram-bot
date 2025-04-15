"""
Contains handlers for user-initiated commands (e.g., /start, /help, /summary).
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import AIService
from bot.services.message_service import MessageService

logger = logging.getLogger(__name__)


class CommandHandlers:
    """
    Encapsulates handlers for all bot commands.

    Each method corresponds to a command the user can issue to the bot.
    It utilizes the AI and Message services to fulfill command requests.
    """
    
    def __init__(self, ai_service: AIService, message_service: MessageService):
        """
        Initializes the command handlers with necessary services.
        
        Args:
            ai_service: An instance of AIService for AI-related tasks.
            message_service: An instance of MessageService for accessing message history.
        """
        self.ai_service = ai_service
        self.message_service = message_service
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /start command.
        Sends a welcome message and registers the chat ID for potential future use
        (like scheduled summaries).
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
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /help command.
        Displays a detailed user guide including available commands and usage instructions.
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
            "/summary - ↩️ prepare a summary of the last 24h user messages\n"
            "/proof - ↩️ verify a statement for truthfulness\n"
            "/comment - comment on the current discussion topic\n"
            "/gpt - ↩️ answer a question using AI\n\n"
            "↩️ — commands should be sent as replies to user (not bot) messages posted after the bot was added to the chat"
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /summary command.
        Generates and sends a summary of recent messages in the chat.
        Requires the command to be sent as a reply to any message in the chat.
        """
        # Check if this is a reply to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "Please use this command as a reply to any message in the chat.",
                reply_to_message_id=update.message.message_id
            )
            return
            
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
                f"📊 *Message Summary*\n\n{summary}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't generate a summary at this time.")
    
    async def proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /proof command.
        Verifies the truthfulness of the statement in the replied-to message using AI.
        Requires the command to be sent as a reply to a user message.
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
    
    async def comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /comment command.
        Analyzes the recent discussion (last hour) and generates an AI comment.
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
    
    async def gpt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /gpt command.
        Answers the question in the replied-to message using AI.
        Requires the command to be sent as a reply to a user message.
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