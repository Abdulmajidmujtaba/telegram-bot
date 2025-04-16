"""Configuration settings for the Telegram bot."""
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Time settings
SUMMARY_TIMEZONE = pytz.timezone("Europe/London")
SUMMARY_START_HOUR = 20
SUMMARY_END_HOUR = 22

# OpenAI model settings
GPT_MODEL = "gpt-4.1"
SUMMARY_MODEL = "gpt-4.1-mini"
PROOF_MODEL = "gpt-4.1"
COMMENT_MODEL = "gpt-4.1-nano"

# AI response settings
CONCISE_RESPONSES = True  # Set to True for brief AI responses, False for more detailed responses

# Message history settings
MAX_MESSAGE_HISTORY = 2000
SUMMARY_HOURS = 24

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 