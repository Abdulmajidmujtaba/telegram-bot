"""Utility functions used across the Telegram bot modules."""
import datetime
from typing import Dict, Any, List, Optional
from bot.config import SUMMARY_TIMEZONE
import re
from bot.utils.markdown_utils import markdownify, telegramify, standardize


def format_timestamp(timestamp: float) -> str:
    """
    Formats a Unix timestamp into a human-readable string (YYYY-MM-DD HH:MM:SS)
    using the configured SUMMARY_TIMEZONE.
    
    Args:
        timestamp: The Unix timestamp (float or int).
        
    Returns:
        A string representing the date and time in the format '%Y-%m-%d %H:%M:%S'.
    """
    dt = datetime.datetime.fromtimestamp(timestamp, SUMMARY_TIMEZONE)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncates a string to a maximum length, appending "..." if truncated.
    
    Args:
        text: The input string.
        max_length: The maximum desired length of the output string.
        
    Returns:
        The original string if its length is <= max_length, otherwise the
        truncated string ending with "...".
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def escape_markdown(text: str) -> str:
    """
    Escapes special Markdown characters within a string for classic Markdown (not MarkdownV2).

    Prepends a backslash (\\) to characters like '_', '*', '`', and '[' to prevent
    them from being interpreted as Markdown formatting.
    
    Args:
        text: The input string potentially containing Markdown characters.
        
    Returns:
        A string with special Markdown characters escaped.
    """
    # List of all special characters that need to be escaped in classic Markdown
    escape_chars = '_*`['
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)


def escape_markdownv2(text: str) -> str:
    """
    Escapes raw text to be compatible with Telegram's MarkdownV2 format.
    
    Use this when you just need to escape plain text without any markdown 
    formatting.
    
    Args:
        text: The input text to escape.
        
    Returns:
        Text with all special characters escaped for MarkdownV2.
    """
    # For raw text with no markdown formatting intended
    special_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in special_chars else c for c in text)


def format_message_for_summary(message: Dict[str, Any]) -> str:
    """
    Formats a message dictionary into a string suitable for AI summary context.

    Expected format: "[YYYY-MM-DD HH:MM:SS] UserName: Message Text"
    
    Args:
        message: A dictionary representing a message, expected to have 'user',
                 'text', and 'timestamp' keys.
        
    Returns:
        A formatted string representation of the message.
    """
    user = message.get('user', 'Unknown')
    text = message.get('text', '')
    timestamp = message.get('timestamp', 0)
    
    time_str = format_timestamp(timestamp)
    return f"[{time_str}] {user}: {text}"


def filter_messages_by_time(
    messages: List[Dict[str, Any]], 
    hours: Optional[int] = None,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None
) -> List[Dict[str, Any]]:
    """
    Filters a list of message dictionaries based on a specified time range.

    Uses the message 'timestamp' key for filtering. Timestamps are interpreted
    using the `SUMMARY_TIMEZONE`.
    
    Time range can be specified by:
    1. `hours`: Look back N hours from the current time.
    2. `start_time` and `end_time`: Explicit datetime objects (timezone-aware recommended).
    
    If `hours` is provided, it overrides `start_time` and `end_time`.
    If no time arguments are given, defaults to the last 24 hours.
    
    Args:
        messages: A list of message dictionaries, each expected to have a 'timestamp' key.
        hours: Optional. Number of hours to look back from now.
        start_time: Optional. The earliest time for messages to include.
        end_time: Optional. The latest time for messages to include.
        
    Returns:
        A new list containing only the messages that fall within the specified time range.
    """
    # Set up time filters
    now = datetime.datetime.now(SUMMARY_TIMEZONE)
    
    if hours is not None:
        cutoff_time = now - datetime.timedelta(hours=hours)
        start_time = cutoff_time
        end_time = now
    elif start_time is None and end_time is None:
        # Default to last 24 hours if no time parameters provided
        start_time = now - datetime.timedelta(hours=24)
        end_time = now
    
    # Filter messages
    filtered_messages = []
    for msg in messages:
        timestamp = msg.get('timestamp', 0)
        msg_time = datetime.datetime.fromtimestamp(timestamp, SUMMARY_TIMEZONE)
        
        if start_time and msg_time < start_time:
            continue
        if end_time and msg_time > end_time:
            continue
            
        filtered_messages.append(msg)
    
    return filtered_messages 