"""
Contains handlers for non-command messages and chat member updates.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.message_service import MessageService
from bot.utils.markdown_utils import markdownify

logger = logging.getLogger(__name__)


class MessageHandlers:
    """
    Encapsulates handlers for incoming text messages and chat member status updates.

    Handles storing regular messages and managing the bot's status (e.g., joining/
    leaving chats) based on chat member updates.
    """
    
    def __init__(self, message_service: MessageService):
        """
        Initializes the message handlers with the message service.
        
        Args:
            message_service: Instance of MessageService for storing message history.
        """
        self.message_service = message_service
        self.bot = None  # Will be set later
    
    def set_bot(self, bot):
        """
        Sets the bot instance for markdown formatting.
        
        Args:
            bot: Instance of SummaryBot to access send_markdown_message
        """
        self.bot = bot
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles incoming regular text messages (not commands).
        
        Stores the received message using the MessageService for future analysis
        (e.g., generating summaries).
        
        Args:
            update: The Telegram update containing the message.
            context: The callback context.
        """
        # Store the message for history
        await self.message_service.store_message(update, context)
        
        # Additional message processing could be added here in the future
        # For example, detecting questions, analyzing sentiment, etc.
    
    async def handle_new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles updates when new members are added to a chat.
        
        If the bot itself is added to a new chat, it sends a welcome message
        and adds the chat ID to the list of active chats in `context.bot_data`.
        
        Args:
            update: The Telegram update for new chat members.
            context: The callback context.
        """
        # Check if the bot itself was added
        new_members = update.message.new_chat_members
        bot_id = context.bot.id
        
        for member in new_members:
            if member.id == bot_id:
                # Bot was added to a new chat
                chat_id = update.effective_chat.id
                
                # Add this chat to active chats list
                if 'active_chats' not in context.bot_data:
                    context.bot_data['active_chats'] = []
                
                if chat_id not in context.bot_data['active_chats']:
                    context.bot_data['active_chats'].append(chat_id)
                
                # Send a welcome message
                welcome_text = (
                    "👋 Hello everyone! I've been added to this group.\n\n"
                    "I'm an AI-powered chat assistant. I can summarize messages, "
                    "verify facts, answer questions, and more.\n\n"
                    "I'll automatically post a daily summary between 20:00-22:00 London time.\n\n"
                    "Type /help to see what I can do!"
                )
                
                if self.bot:
                    await self.bot.send_markdown_message(chat_id, welcome_text, context)
                else:
                    await update.message.reply_text(
                        markdownify(welcome_text),
                        parse_mode="MarkdownV2"
                    )
                return
    
    async def handle_left_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles updates when a member leaves or is removed from a chat.
        
        If the bot itself is removed from a chat, it removes the chat ID from the
        list of active chats in `context.bot_data` and cleans up any associated
        data stored in `context.chat_data`.
        
        Args:
            update: The Telegram update for a left chat member.
            context: The callback context.
        """
        # Check if the bot was removed
        left_member = update.message.left_chat_member
        bot_id = context.bot.id
        
        if left_member and left_member.id == bot_id:
            # Bot was removed from chat
            chat_id = update.effective_chat.id
            
            # Remove this chat from active chats list
            if 'active_chats' in context.bot_data and chat_id in context.bot_data['active_chats']:
                context.bot_data['active_chats'].remove(chat_id)
                
                # Clean up any stored data for this chat
                chat_data_keys = list(context.chat_data.keys())
                for key in chat_data_keys:
                    del context.chat_data[key] 