"""
Main entry point for the Discord bot.
"""
import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from config import load_config, validate_startup_config, ConfigurationError
from logger import setup_logging
from api_client import APIClient
from message_processor import MessageProcessor
from bot import DiscordBot


class BotRunner:
    """Manages the bot lifecycle and graceful shutdown."""
    
    def __init__(self):
        self.bot = None
        self.shutdown_event = asyncio.Event()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Initiate graceful shutdown."""
        self.shutdown_event.set()
    
    async def run(self):
        """Run the bot with proper lifecycle management."""
        logger = logging.getLogger(__name__)
        
        try:
            # Load environment variables from .env file if it exists
            env_file = bot_dir / '.env'
            if env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(env_file)
            
            # Validate and load configuration
            config = validate_startup_config()
            
            # Set up logging
            setup_logging(config.log_level)
            
            logger.info("🤖 Starting Discord Bot for AskRacha Integration")
            logger.info(f"📡 API URL: {config.askracha_api_url}")
            logger.info(f"⏱️  API Timeout: {config.api_timeout}s")
            logger.info(f"🔄 Retry Attempts: {config.retry_attempts}")
            logger.info(f"📝 Max Response Length: {config.max_response_length}")
            
            # Initialize components
            api_client = APIClient(
                api_url=config.askracha_api_url,
                timeout=config.api_timeout,
                retry_attempts=config.retry_attempts,
                retry_delay=config.retry_delay
            )
            
            message_processor = MessageProcessor(
                max_response_length=config.max_response_length
            )
            
            # Initialize Discord bot
            self.bot = DiscordBot(config, api_client, message_processor)
            
            logger.info("✅ Bot components initialized")
            logger.info("🚀 Starting Discord bot...")
            
            # Set up signal handlers for graceful shutdown
            if sys.platform != 'win32':
                signal.signal(signal.SIGINT, self.signal_handler)
                signal.signal(signal.SIGTERM, self.signal_handler)
            
            # Start the bot
            bot_task = asyncio.create_task(self.bot.start_bot())
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            
            # Wait for either the bot to finish or shutdown signal
            done, pending = await asyncio.wait(
                [bot_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Check if bot task completed with an error
            if bot_task in done:
                try:
                    await bot_task
                except Exception as e:
                    logger.error(f"Bot task failed: {e}")
                    raise
            
        except ConfigurationError as e:
            print(f"❌ Configuration Error: {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            logger.info("🛑 Bot shutdown requested via keyboard interrupt")
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}", exc_info=True)
            return 1
        finally:
            # Ensure graceful cleanup
            if self.bot:
                try:
                    await self.bot.close_bot()
                except Exception as e:
                    logger.error(f"Error during bot cleanup: {e}")
            
            logger.info("👋 Bot shutdown complete")
        
        return 0


async def main():
    """Main entry point for the Discord bot."""
    runner = BotRunner()
    exit_code = await runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())