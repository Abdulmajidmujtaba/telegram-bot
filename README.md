# Telegram Summary Bot

An AI-powered bot for creating summaries of messages in group chats using Telegram and OpenAI.

## Features

- 📅 **Daily Summaries**: Automatically generate a brief overview of chat discussions from the last 24 hours.
- 👤 **Individual Summaries**: Create a summary of messages from a specific user.
- 🤖 **ChatGPT**: Answer questions in the chat using OpenAI models.
- ✅ **Fact-Checking**: Confirm or refute statements posted in the chat.
- 🗣️ **AI Commentary**: Comment on the current discussion in the chat.
- 📚 **FAQ**: Provide information on frequently asked questions.
- 🔥 **Post Roasting**: Leave entertaining comments on channel posts.

## Setup

1. Clone this repository
2. Install requirements: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run the bot: `python -m bot.main`

## Bot Usage

- Add the bot to your group chat and grant it administrator rights.
- Between 20:00 - 22:00 (London Time), the bot will automatically publish a chat summary.
- The bot cannot view messages posted before it was added to the chat.

## Available Commands

- `/start` - Start interacting with the bot
- `/help` - Display help menu
- `/summary` - Prepare a summary of the last 24h user messages (reply to a message)
- `/proof` - Verify a statement for truthfulness (reply to a message)
- `/comment` - Comment on the current discussion topic
- `/gpt` - Answer a question using AI (reply to a message)

Commands marked with reply functionality should be sent as replies to user messages posted after the bot was added to the chat. 