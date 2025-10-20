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
GPT_MODEL = "o3"
SUMMARY_MODEL = "gpt-4.1-mini"
PROOF_MODEL = "gpt-4.1"
COMMENT_MODEL = "gpt-4.1-nano"

# Image analysis settings
IMAGE_ANALYSIS_MODEL = os.getenv("IMAGE_ANALYSIS_MODEL", GPT_MODEL)
IMAGE_ANALYSIS_REASONING_EFFORT = os.getenv("IMAGE_ANALYSIS_REASONING_EFFORT", "medium")
IMAGE_ANALYSIS_TOOLS = []
IMAGE_ANALYSIS_INCLUDE_FIELDS = ["reasoning.encrypted_content", "web_search_call.action.sources"]
IMAGE_ANALYSIS_STORE_RESPONSES = False
IMAGE_ANALYSIS_TEXT_FORMAT = {"type": "text"}

# AI response settings
CONCISE_RESPONSES = True  # Set to True for brief AI responses, False for more detailed responses

# Message history settings
MAX_MESSAGE_HISTORY = 2000
SUMMARY_HOURS = 24

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 
