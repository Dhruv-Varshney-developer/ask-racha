# Discord Bot for AskRacha Integration

This Discord bot integrates with the AskRacha RAG API to provide automated support responses to community members in Discord channels.

## Features

- Responds to @racha mentions with intelligent answers
- Integrates with existing AskRacha RAG API
- Handles errors gracefully with user-friendly messages
- Comprehensive logging and monitoring
- Configurable through environment variables
- Resilient with automatic reconnection and retry logic

## Setup

### Prerequisites

- Python 3.8 or higher
- Discord bot token from Discord Developer Portal
- Running AskRacha API instance

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy the environment configuration:

```bash
cp .env.example .env
```

3. Edit `.env` file with your configuration:

```bash
# Required
DISCORD_TOKEN=your_discord_bot_token_here

# Optional (defaults shown)
ASKRACHA_API_URL=http://localhost:5000
API_TIMEOUT=10
MAX_RESPONSE_LENGTH=2000
LOG_LEVEL=INFO
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
```

### Running the Bot

```bash
python main.py
```

## Configuration

All configuration is managed through environment variables:

| Variable              | Required | Default                 | Description                     |
| --------------------- | -------- | ----------------------- | ------------------------------- |
| `DISCORD_TOKEN`       | Yes      | -                       | Discord bot token               |
| `ASKRACHA_API_URL`    | No       | `http://localhost:5000` | AskRacha API base URL           |
| `API_TIMEOUT`         | No       | `10`                    | API request timeout (seconds)   |
| `MAX_RESPONSE_LENGTH` | No       | `2000`                  | Max Discord message length      |
| `LOG_LEVEL`           | No       | `INFO`                  | Logging level                   |
| `RETRY_ATTEMPTS`      | No       | `3`                     | API retry attempts              |
| `RETRY_DELAY`         | No       | `1.0`                   | Delay between retries (seconds) |

## Usage

1. Invite the bot to your Discord server with appropriate permissions
2. Mention the bot with your question: `@racha How do I upload files to Storacha?`
3. The bot will respond with an AI-generated answer from the knowledge base

## Logging

The bot creates structured JSON logs in the `logs/` directory:

- `bot.log` - All bot operations and events
- `error.log` - Error-level events only

Logs include:

- Bot lifecycle events (startup, shutdown, reconnection)
- Message processing (questions, responses, timing)
- API communication (requests, responses, errors)
- Performance metrics

## Architecture

The bot consists of several key components:

- **config.py** - Configuration management with validation
- **logger.py** - Structured logging system
- **api_client.py** - HTTP client for AskRacha API
- **message_processor.py** - Message parsing and formatting
- **bot.py** - Main Discord bot client
- **main.py** - Application entry point

## Error Handling

The bot handles various error scenarios gracefully:

- API unavailability - Friendly error message
- Request timeouts - Timeout notification
- Invalid questions - Clarification prompt
- Discord API errors - Automatic retry and reconnection
- Rate limiting - Automatic queue management

## Contributing

When implementing new features:

1. Follow the existing code structure and patterns
2. Add comprehensive logging for debugging
3. Include error handling for all failure scenarios
4. Write unit tests for new functionality
5. Update documentation as needed
