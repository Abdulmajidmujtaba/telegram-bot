# Telegram Summary Bot

An AI-powered Telegram bot that summarizes group chat discussions, answers questions, fact-checks statements, provides AI commentary, and analyzes images or charts using OpenAI models (including GPT-4 Vision).

## Features

- **Daily Summaries**: Automatically generates a summary of the last 24 hours of chat messages, posted daily between 20:00 and 22:00 London time.
- **On-Demand Summaries**: Instantly summarize recent chat activity with a command.
- **Individual Summaries**: Summarize messages from a specific user.
- **Fact-Checking**: Verify the truthfulness of statements using AI.
- **AI Q&A**: Ask questions and get answers from OpenAI's models.
- **AI Commentary**: Get insightful or witty comments on ongoing discussions.
- **Image/Chart Analysis**: Analyze uploaded images or charts with your custom instructions (no financial advice).
- **Post Roasting**: Entertaining, light-hearted comments on posts.

## Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### 2. Install Dependencies
Make sure you have Python 3.8+ installed. Then run:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
```
Edit `.env` and set:
- `TELEGRAM_BOT_TOKEN` (from BotFather)
- `OPENAI_API_KEY` (from OpenAI)

### 4. Run the Bot
Start the bot with:
```bash
python run.py
```

- The bot will log to the console. Use `Ctrl+C` to stop it gracefully.

## Usage

### Adding the Bot
- Add the bot to your group chat and grant it administrator rights.
- The bot can only see messages sent after it was added.

### Daily Summaries
- The bot automatically posts a summary of the last 24 hours of messages between 20:00 and 22:00 (London time).

### Available Commands

| Command                | Description                                                                                 |
|------------------------|---------------------------------------------------------------------------------------------|
| `/start`               | Start interacting with the bot (registers the chat for daily summaries)                     |
| `/help`                | Show help and usage instructions                                                            |
| `/summary`             | Summarize the last 24 hours of messages in the group                                        |
| `/proof [statement]`   | Fact-check a statement (can also be used as a reply to a message)                           |
| `/comment`             | Get an AI-generated comment on the current discussion                                       |
| `/gpt [question]`      | Ask a question and get an AI answer (can also be used as a reply to a message)              |
| `/analyze`             | Analyze an image or chart (see below for usage)                                             |

#### How to Use `/analyze`
- **Send a photo with `/analyze` as the caption and your instructions.**
- **Or, reply to a photo with `/analyze [your instructions]`.**
- The bot will analyze the image/chart and reply with feedback based on your instructions.
- _Disclaimer: The analysis is for informational purposes only and is not financial advice._

All commands can be used directly or as replies to messages. When used as replies, the bot will analyze the replied message content.

## Environment Variables

Your `.env` file should look like this:
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPENAI_API_KEY=your-openai-api-key
```

## Requirements
- Python 3.8+
- See `requirements.txt` for Python dependencies

## Notes
- The bot only processes messages it has seen since being added to the chat.
- For best results, ensure the bot has permission to read all messages in the group.
- Logging output is printed to the console for monitoring and debugging.

## License
MIT License 