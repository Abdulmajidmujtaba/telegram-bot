"""
Contains handlers for user-initiated commands (e.g., /start, /help, /summary).
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import AIService
from bot.services.message_service import MessageService
from telegram.constants import ParseMode
from bot.utils.markdown_utils import markdownify, telegramify
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.main import SummaryBot

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
        self.bot = None  # Will be set later
    
    def set_bot(self, bot: 'SummaryBot'):
        """
        Sets the bot instance for markdown formatting.
        
        Args:
            bot: Instance of SummaryBot to access send_markdown_message
        """
        self.bot = bot
    
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
        
        if self.bot:
            await self.bot.send_markdown_message(chat_id, welcome_text, context)
        else:
            formatted_text = markdownify(welcome_text)
            await update.message.reply_text(formatted_text, parse_mode="MarkdownV2")
    
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
                "/analyze - analyze an image or chart\n"
                "/reset - reset the ongoing image analysis conversation\n\n"
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
                "/analyze - analyze an image or chart\n"
                "/reset - reset the ongoing image analysis conversation\n\n"
                "Note: The bot can only access messages sent after it was added to the chat."
            )
        if self.bot:
            await self.bot.send_markdown_message(update.effective_chat.id, help_text, context)
        else:
            formatted_text = markdownify(help_text)
            await update.message.reply_text(formatted_text, parse_mode="MarkdownV2")
    
    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /summary command.
        Generates and sends a summary of recent messages in the chat.
        Works directly without requiring a reply to a message.
        Summarizes messages for the whole group chat.
        """
        progress_message = await update.message.reply_text(
            markdownify("Generating summary... This might take a moment."),
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
                await progress_message.edit_text(
                    markdownify("No recent messages found to summarize."), 
                    parse_mode="MarkdownV2"
                )
                return
                
            # Generate summary
            summary = await self.ai_service.generate_summary(messages)
            
            # Send summary
            summary_text = f"📊 Group Chat Summary\n\n{summary}"
            if self.bot:
                await self.bot.send_markdown_message(update.effective_chat.id, summary_text, context)
                await progress_message.delete()
            else:
                await progress_message.edit_text(
                    markdownify(summary_text),
                    parse_mode="MarkdownV2"
                )
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            await progress_message.edit_text(
                markdownify("Sorry, I couldn't generate a summary at this time."), 
                parse_mode="MarkdownV2"
            )
    
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
                markdownify("Please provide a statement to verify. Examples:\n"
                "1. Reply to a message with /proof\n"
                "2. Type /proof followed by the statement to verify"),
                reply_to_message_id=update.message.message_id,
                parse_mode="MarkdownV2"
            )
            return
            
        progress_message = await update.message.reply_text(
            markdownify(f"Verifying the statement: \"{statement}\"... This might take a moment."),
            reply_to_message_id=update.message.message_id,
            parse_mode="MarkdownV2"
        )
        
        try:
            # Verify statement
            result = await self.ai_service.verify_statement(statement)
            
            # Send verification result
            fact_check_text = f"✅ Fact Check\n\nStatement: \"{statement}\"\n\n{result}"
            if self.bot:
                await self.bot.send_markdown_message(update.effective_chat.id, fact_check_text, context)
                await progress_message.delete()
            else:
                await progress_message.edit_text(
                    markdownify(fact_check_text),
                    parse_mode="MarkdownV2"
                )
            
        except Exception as e:
            logger.error(f"Error verifying statement: {str(e)}")
            await progress_message.edit_text(
                markdownify("Sorry, I couldn't verify that statement at this time."),
                parse_mode="MarkdownV2"
            )
    
    async def comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /comment command.
        Analyzes the recent discussion (last hour) and generates an AI comment.
        Can be used directly without replying to a message.
        """
        progress_message = await update.message.reply_text(
            markdownify("Analyzing the discussion and generating a comment... This might take a moment."),
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
                await progress_message.edit_text(
                    markdownify("I don't see any recent messages to comment on."), 
                    parse_mode="MarkdownV2"
                )
                return
                
            # Generate comment
            comment = await self.ai_service.generate_comment(messages)
            
            # Send comment
            comment_text = f"💬 AI Commentary\n\n{comment}"
            if self.bot:
                await self.bot.send_markdown_message(update.effective_chat.id, comment_text, context)
                await progress_message.delete()
            else:
                await progress_message.edit_text(
                    markdownify(comment_text),
                    parse_mode="MarkdownV2"
                )
            
        except Exception as e:
            logger.error(f"Error generating comment: {str(e)}")
            await progress_message.edit_text(
                markdownify("Sorry, I couldn't generate a comment at this time."), 
                parse_mode="MarkdownV2"
            )
    
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
                markdownify("Please provide a question to answer. Examples:\n"
                "1. Reply to a message with /gpt\n"
                "2. Type /gpt followed by your question"),
                reply_to_message_id=update.message.message_id,
                parse_mode="MarkdownV2"
            )
            return
            
        progress_message = await update.message.reply_text(
            markdownify(f"Thinking about: \"{question}\"... This might take a moment."),
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
            
            # Generate answer
            answer = await self.ai_service.answer_question(question, messages)
            
            # Send answer
            response_text = f"🤖 AI Response\n\nQuestion: \"{question}\"\n\n{answer}"
            if self.bot:
                await self.bot.send_markdown_message(update.effective_chat.id, response_text, context)
                await progress_message.delete()
            else:
                await progress_message.edit_text(
                    markdownify(response_text),
                    parse_mode="MarkdownV2"
                )
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            await progress_message.edit_text(
                markdownify("Sorry, I couldn't answer that question at this time."),
                parse_mode="MarkdownV2"
            )
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /analyze command for analyzing images or charts.
        Can be used as a reply to an image or with an image caption.
        """
        if not update.message.photo and not update.message.reply_to_message:
            await update.message.reply_text(
                markdownify("Please attach an image to analyze or reply to an image with /analyze"),
                reply_to_message_id=update.message.message_id,
                parse_mode="MarkdownV2"
            )
            return
            
        # Get the photo to analyze
        target_message = update.message if update.message.photo else update.message.reply_to_message
        if not target_message.photo:
            await update.message.reply_text(
                markdownify("I can only analyze images. Please send an image or reply to an image."),
                reply_to_message_id=update.message.message_id,
                parse_mode="MarkdownV2"
            )
            return
            
        progress_message = await update.message.reply_text(
            markdownify("Analyzing the image... This might take a moment."),
            reply_to_message_id=update.message.message_id,
            parse_mode="MarkdownV2"
        )
        
        try:
            # Get the file
            photo = target_message.photo[-1]  # Get highest resolution
            file = await context.bot.get_file(photo.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Get the caption/command text if any
            caption = ""
            if update.message.caption:
                parts = update.message.caption.split(' ', 1)
                if len(parts) > 1:
                    caption = parts[1].strip()
            elif update.message.text:
                parts = update.message.text.split(' ', 1)
                if len(parts) > 1:
                    caption = parts[1].strip()
            elif target_message.caption:
                caption = target_message.caption.strip()

            user_id = update.effective_user.id if update.effective_user else None
            conversation_id = self.ai_service.build_image_conversation_id(
                update.effective_chat.id,
                user_id
            )
                    
            # Analyze the image
            analysis = await self.ai_service.analyze_image(file_bytes, caption, conversation_id)
            
            # Send the analysis result
            analysis_text = f"🖼️ Image Analysis\n\n{analysis}\n\n_Disclaimer: This is not financial advice._"
            if self.bot:
                await self.bot.send_markdown_message(update.effective_chat.id, analysis_text, context)
                await progress_message.delete()
            else:
                await progress_message.edit_text(
                    markdownify(analysis_text),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in /analyze: {str(e)}")
            await progress_message.edit_text(
                markdownify("Sorry, I couldn't analyze the image at this time."),
                parse_mode="MarkdownV2"
            )

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /reset command to clear a user's image analysis conversation history.
        """
        user_id = update.effective_user.id if update.effective_user else None
        conversation_id = self.ai_service.build_image_conversation_id(
            update.effective_chat.id,
            user_id
        )

        await self.ai_service.reset_image_conversation(conversation_id)

        confirmation_text = "Image analysis conversation history cleared."
        if self.bot:
            await self.bot.send_markdown_message(update.effective_chat.id, confirmation_text, context)
        else:
            await update.message.reply_text(
                markdownify(confirmation_text),
                parse_mode="MarkdownV2"
            )
