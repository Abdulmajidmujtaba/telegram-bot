"""
Contains handlers for user-initiated commands (e.g., /start, /help, /summary).
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import AIService
from bot.services.message_service import MessageService
from telegram.constants import ParseMode
from bot.utils.helpers import escape_markdown

logger = logging.getLogger(__name__)


class CommandHandlers:
    """
    Method corresponds to a command the user can issue to the bot.
    It utilizes the AI and Message services to fulfill command requests.
    """
    
    def __init__(self, ai_service: AIService, message_service: MessageService):
        """
        Command handlers with necessary services.
        
        Args:
            ai_service: Instance of AIService for AI-related tasks.
            message_service: Instance of MessageService for accessing message history.
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
            "👋 Hello! I'm an AI chat assistant. "
            "I can summarize messages, verify facts, answer questions, and more.\n\n"
            "Add me to a group chat and grant me admin rights to use all my features. "
            "Type /help to see what I can do!"
        )
        
        await update.message.reply_text(welcome_text, parse_mode="MarkdownV2")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /help command.
        Displays a detailed user guide including available commands and usage instructions.
        In group chats, does not show the /start command.
        """
        chat_type = update.effective_chat.type
        if chat_type == "private":
            help_text = (
                "🤖 *Bot User Guide* 🤖\n\n"
                "➠ Add the bot to your group chat and grant it administrator rights.\n"
                "➠ Between 20:00 - 22:00 (London Time) the bot will automatically publish "
                "a chat summary by analyzing the last 24 hours of messages using AI.\n"
                "➠ The bot cannot view messages posted before it was added to the chat.\n"
                "➠ You can use commands directly in the chat (see below).\n\n"
                "*Available Commands*\n"
                "/start - start interacting with the bot\n"
                "/help - display this menu\n\n"
                "*Group Chat Commands*\n"
                "/summary - prepare a summary of the group's messages from the last 24h\n"
                "/proof [statement] - verify a statement for truthfulness (use as reply)\n"
                "/comment - comment on the current discussion topic\n"
                "/gpt [question] - answer a question using AI (use as reply)\n"
                "/analyze - analyze an image or chart\n\n"
                "Note: The bot can only access messages sent after it was added to the chat."
            )
        else:
            help_text = (
                "🤖 *Bot User Guide* 🤖\n\n"
                "➠ Add the bot to your group chat and grant it administrator rights.\n"
                "➠ Between 20:00 - 22:00 (London Time) the bot will automatically publish "
                "a chat summary by analyzing the last 24 hours of messages using AI.\n"
                "➠ The bot cannot view messages posted before it was added to the chat.\n"
                "➠ You can use commands directly in the chat (see below).\n\n"
                "*Available Commands*\n"
                "/help - display this menu\n\n"
                "*Group Chat Commands*\n"
                "/summary - prepare a summary of the group's messages from the last 24h\n"
                "/proof [statement] - verify a statement for truthfulness (use as reply)\n"
                "/comment - comment on the current discussion topic\n"
                "/gpt [question] - answer a question using AI (use as reply)\n"
                "/analyze - analyze an image or chart\n\n"
                "Note: The bot can only access messages sent after it was added to the chat."
            )
        await update.message.reply_text(help_text, parse_mode="MarkdownV2")
    
    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /summary command.
        Generates and sends a summary of recent messages in the chat.
        Works directly without requiring a reply to a message.
        Summarizes messages for the whole group chat.
        """
        progress_message = await update.message.reply_text(
            "Generating summary... This might take a moment.",
            reply_to_message_id=update.message.message_id,
            parse_mode="MarkdownV2"
        )
        
        try:
            # Get recent messages
            messages = await self.message_service.get_recent_messages(
                update.effective_chat, 
                context
            )
            
            if not messages:
                await progress_message.edit_text("No recent messages found to summarize.", parse_mode="MarkdownV2")
                return
                
            # Generate summary
            summary = await self.ai_service.generate_summary(messages)
            
            # Send summary
            await progress_message.edit_text(
                f"📊 *Group Chat Summary*\n\n{escape_markdown(summary)}",
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't generate a summary at this time.", parse_mode="MarkdownV2")
    
    async def proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /proof command.
        Verifies the truthfulness of the statement provided in the command text.
        If used as a reply to a message, verifies that message instead.
        """
        statement = None
        
        # Check if this is a reply to a message
        if update.message.reply_to_message and not update.message.reply_to_message.from_user.is_bot:
            statement = update.message.reply_to_message.text
        else:
            # Extract statement from command text: /proof This is a statement
            command_parts = update.message.text.split(' ', 1)
            if len(command_parts) > 1:
                statement = command_parts[1].strip()
        
        if not statement:
            await update.message.reply_text(
                "Please provide a statement to verify. Examples:\n"
                "1. Reply to a message with /proof\n"
                "2. Type /proof followed by the statement to verify",
                reply_to_message_id=update.message.message_id,
                parse_mode="MarkdownV2"
            )
            return
            
        progress_message = await update.message.reply_text(
            f"Verifying the statement: \"{statement}\"... This might take a moment.",
            reply_to_message_id=update.message.message_id,
            parse_mode="MarkdownV2"
        )
        
        try:
            # Verify statement
            result = await self.ai_service.verify_statement(statement)
            
            # Send verification result
            await progress_message.edit_text(
                f"✅ *Fact Check*\n\nStatement: \"{escape_markdown(statement)}\"\n\n{escape_markdown(result)}",
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            logger.error(f"Error verifying statement: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't verify that statement at this time.", parse_mode="MarkdownV2")
    
    async def comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /comment command.
        Analyzes the recent discussion (last hour) and generates an AI comment.
        Can be used directly without replying to a message.
        """
        progress_message = await update.message.reply_text(
            "Analyzing the discussion and generating a comment... This might take a moment.",
            reply_to_message_id=update.message.message_id,
            parse_mode="MarkdownV2"
        )
        
        try:
            # Get recent messages for context
            messages = await self.message_service.get_recent_messages(
                update.effective_chat, 
                context,
                hours=1  # Get messages from the last hour for context
            )
            
            if not messages:
                await progress_message.edit_text("I don't see any recent messages to comment on.", parse_mode="MarkdownV2")
                return
                
            # Generate comment
            comment = await self.ai_service.generate_comment(messages)
            
            # Send comment
            await progress_message.edit_text(
                f"💬 *AI Commentary*\n\n{escape_markdown(comment)}",
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            logger.error(f"Error generating comment: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't generate a comment at this time.", parse_mode="MarkdownV2")
    
    async def gpt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /gpt command.
        Answers the question provided in the command text.
        If used as a reply to a message, answers that message instead.
        """
        question = None
        
        # Check if this is a reply to a message
        if update.message.reply_to_message and not update.message.reply_to_message.from_user.is_bot:
            question = update.message.reply_to_message.text
        else:
            # Extract question from command text: /gpt What is the meaning of life?
            command_parts = update.message.text.split(' ', 1)
            if len(command_parts) > 1:
                question = command_parts[1].strip()
        
        if not question:
            await update.message.reply_text(
                "Please provide a question to answer. Examples:\n"
                "1. Reply to a message with /gpt\n"
                "2. Type /gpt followed by your question",
                reply_to_message_id=update.message.message_id,
                parse_mode="MarkdownV2"
            )
            return
            
        progress_message = await update.message.reply_text(
            f"Answering: \"{question}\"... This might take a moment.",
            reply_to_message_id=update.message.message_id,
            parse_mode="MarkdownV2"
        )
        
        try:
            # Answer question
            answer = await self.ai_service.answer_question(question)
            
            # Send answer
            await progress_message.edit_text(
                f"🤖 *AI Response*\n\nQuestion: \"{escape_markdown(question)}\"\n\n{escape_markdown(answer)}",
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't answer that question at this time.", parse_mode="MarkdownV2")
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /analyze command for image/chart analysis.
        Users can send a photo with the /analyze command as a caption, or reply to a photo with /analyze and instructions.
        The bot will analyze the image using the user's instructions and return feedback (not financial advice).
        """
        user = update.effective_user.first_name if update.effective_user else "User"
        message = update.message
        photo = None
        instructions = None

        # Case 1: /analyze as a reply to a photo
        if message.reply_to_message and message.reply_to_message.photo:
            photo = message.reply_to_message.photo[-1]  # Get highest resolution
            # Instructions from the /analyze command text
            command_parts = message.text.split(' ', 1)
            instructions = command_parts[1].strip() if len(command_parts) > 1 else "Analyze this chart."
        # Case 2: /analyze sent as caption to a photo
        elif message.photo:
            photo = message.photo[-1]
            instructions = message.caption or "Analyze this chart."
        else:
            await message.reply_text(
                "Please send /analyze as a caption to a photo, or reply to a photo with /analyze and your instructions.",
                reply_to_message_id=message.message_id,
                parse_mode="MarkdownV2"
            )
            return

        progress_message = await message.reply_text(
            "Analyzing the image... This might take a moment.",
            reply_to_message_id=message.message_id,
            parse_mode="MarkdownV2"
        )

        try:
            # Download the photo from Telegram
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()
            # Analyze the image using AIService
            analysis = await self.ai_service.analyze_image(bytes(image_bytes), instructions)
            # Send the analysis result
            await progress_message.edit_text(
                f"🖼️ *Image Analysis*\n\n{escape_markdown(analysis)}\n\n_Disclaimer: This is not financial advice._",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.error(f"Error in /analyze: {str(e)}")
            await progress_message.edit_text("Sorry, I couldn't analyze the image at this time.", parse_mode="MarkdownV2") 