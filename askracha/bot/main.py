"""
Main entry point for the Discord bot.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from config import load_config, validate_startup_config, ConfigurationError
from logger import setup_logging


async def main():
    """Main entry point for the Discord bot."""
    try:
        # Load environment variables from .env file if it exists
        env_file = bot_dir / '.env'
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        # Validate and load configuration
        config = validate_startup_config()
        
        # Set up logging
        bot_logger = setup_logging(config.log_level)
        logger = logging.getLogger(__name__)
        
        logger.info("🤖 Starting Discord Bot for AskRacha Integration")
        logger.info(f"📡 API URL: {config.askracha_api_url}")
        logger.info(f"⏱️  API Timeout: {config.api_timeout}s")
        logger.info(f"🔄 Retry Attempts: {config.retry_attempts}")
        
        # TODO: Initialize and start the Discord bot
        # This will be implemented in task 4
        logger.info("✅ Bot initialization complete")
        
        # Keep the bot running
        logger.info("🚀 Bot is now running...")
        
        # For now, just wait indefinitely
        # In the actual implementation, this will be replaced with bot.run()
        while True:
            await asyncio.sleep(1)
            
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Bot shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())