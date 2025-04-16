"""
Markdown utilities for formatting text to be sent via Telegram.

This module provides wrapper functions around the telegramify-markdown library
to ensure consistent markdown formatting across the application.
"""
import telegramify_markdown
import telegramify_markdown.customize as customize


# Configure telegramify-markdown
customize.strict_markdown = False  # Allow __underline__ to be rendered as underline
customize.cite_expandable = True   # Enable expandable citation


def markdownify(text: str) -> str:
    """
    Convert raw Markdown text to Telegram's MarkdownV2 format.
    
    This function should be used for static text that doesn't need
    to be split or contain code blocks with interpreters.
    
    Args:
        text: Raw markdown text
        
    Returns:
        Text formatted for Telegram's MarkdownV2 parser
    """
    return telegramify_markdown.markdownify(text)


def telegramify(text: str) -> list[str]:
    """
    Convert raw Markdown text to Telegram's MarkdownV2 format
    and split it into chunks if needed.
    
    Use this for longer text that might need to be split into
    multiple messages or contains code blocks that should be
    rendered differently.
    
    Args:
        text: Raw markdown text
        
    Returns:
        List of text chunks formatted for Telegram's MarkdownV2 parser
    """
    return telegramify_markdown.telegramify(text)


def standardize(text: str) -> str:
    """
    Convert unstandardized Telegram's MarkdownV2 format to standardized format.
    
    Use this when you're writing MarkdownV2 format text directly and want
    to ensure it's properly formatted for Telegram.
    
    Args:
        text: Unstandardized MarkdownV2 text
        
    Returns:
        Standardized MarkdownV2 text
    """
    return telegramify_markdown.standardize(text) 