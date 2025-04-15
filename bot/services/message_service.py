"""
Provides services for managing and accessing the in-memory Telegram message history
stored within the bot's context data (`context.chat_data`).
"""
import logging
import datetime
from typing import List, Dict, Any, Optional

from telegram import Update, Chat
from telegram.ext import ContextTypes

from bot.config import SUMMARY_HOURS, MAX_MESSAGE_HISTORY

logger = logging.getLogger(__name__)

class MessageService:
    """
    Handles storing new messages and retrieving historical messages from the
    `context.chat_data['message_history']` list for a given chat.

    Provides methods to get recent messages within a time window and to get
    messages from a specific user.
    """
    
    @staticmethod
    async def get_recent_messages(
        chat: Chat, 
        context: ContextTypes.DEFAULT_TYPE, 
        hours: int = SUMMARY_HOURS, 
        limit: int = MAX_MESSAGE_HISTORY
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent messages from the chat's in-memory history.

        Filters messages stored in `context.chat_data['message_history']` based on
        the specified time window (`hours`) and returns up to `limit` messages.
        
        Args:
            chat: The chat object (used primarily for context, history is in `context`).
            context: The callback context containing `chat_data`.
            hours: The number of hours to look back for messages.
            limit: The maximum number of messages to retrieve from the end of the history.
            
        Returns:
            A list of dictionaries, each containing 'user', 'text', and 'timestamp'.
            Returns an empty list if history is empty or an error occurs.
        """
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
            
            # In a real implementation, you would use Telegram's getHistory method
            # or a similar approach to retrieve messages.
            # For now, we'll access the bot's message history that it has seen
            # stored in the context.chat_data dictionary
            
            if not context.chat_data.get('message_history'):
                context.chat_data['message_history'] = []
                
            # Filter messages by time
            recent_messages = []
            for msg in context.chat_data['message_history'][-limit:]:
                msg_time = datetime.datetime.fromtimestamp(msg.get('timestamp', 0))
                if msg_time >= cutoff_time:
                    recent_messages.append({
                        'user': msg.get('user', 'Unknown'),
                        'text': msg.get('text', ''),
                        'timestamp': msg.get('timestamp', 0)
                    })
            
            return recent_messages
            
        except Exception as e:
            logger.error(f"Error retrieving message history: {str(e)}")
            return []
    
    @staticmethod
    async def store_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Stores a new text message in the chat's in-memory history.

        Appends a dictionary containing message details (user, user_id, text,
        timestamp, message_id) to `context.chat_data['message_history']`.
        Skips messages that have no text content or are sent by the bot itself.
        Enforces the `MAX_MESSAGE_HISTORY` limit by truncating older messages.
        
        Args:
            update: The update object containing the message.
            context: The callback context where the history is stored.
        """
        # Skip messages without text or from the bot itself
        message = update.effective_message
        if not message or not message.text or message.from_user.is_bot:
            return
            
        if not context.chat_data.get('message_history'):
            context.chat_data['message_history'] = []
            
        # Add message to history
        context.chat_data['message_history'].append({
            'user': message.from_user.first_name,
            'user_id': message.from_user.id,
            'text': message.text,
            'timestamp': message.date.timestamp(),
            'message_id': message.message_id
        })
        
        # Limit history size to avoid excessive memory usage
        if len(context.chat_data['message_history']) > MAX_MESSAGE_HISTORY:
            context.chat_data['message_history'] = context.chat_data['message_history'][-MAX_MESSAGE_HISTORY:]
    
    @staticmethod
    async def get_user_messages(
        chat: Chat, 
        context: ContextTypes.DEFAULT_TYPE, 
        user_id: int,
        hours: Optional[int] = None, 
        limit: int = MAX_MESSAGE_HISTORY
    ) -> List[Dict[str, Any]]:
        """
        Retrieves messages from a specific user within the chat's in-memory history.

        Filters messages in `context.chat_data['message_history']` by the specified
        `user_id`. Optionally filters by time (`hours`) and limits the result size.
        
        Args:
            chat: The chat object (used primarily for context).
            context: The callback context containing `chat_data`.
            user_id: The Telegram user ID to filter messages by.
            hours: Optional. If provided, only messages within this past N hours are returned.
            limit: The maximum number of messages to retrieve from the end of the history.
            
        Returns:
            A list of message dictionaries from the specified user, each containing
            'user', 'text', and 'timestamp'. Returns an empty list on errors or no history.
        """
        try:
            cutoff_time = None
            if hours:
                cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
                
            if not context.chat_data.get('message_history'):
                return []
                
            # Filter messages by user and time
            user_messages = []
            for msg in context.chat_data['message_history'][-limit:]:
                if msg.get('user_id') == user_id:
                    if cutoff_time:
                        msg_time = datetime.datetime.fromtimestamp(msg.get('timestamp', 0))
                        if msg_time < cutoff_time:
                            continue
                    
                    user_messages.append({
                        'user': msg.get('user', 'Unknown'),
                        'text': msg.get('text', ''),
                        'timestamp': msg.get('timestamp', 0)
                    })
            
            return user_messages
            
        except Exception as e:
            logger.error(f"Error retrieving user message history: {str(e)}")
            return [] 