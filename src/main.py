"""
Telegram Happy Hour Duty Bot
Main entry point for the application
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot.bot_core import RefBot
from src.utils.logger import setup_logging

def main():
    """Main entry point"""
    # Set up logging
    log_file = os.getenv("LOG_FILE", "logs/happy_hour_duty.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level=log_level, log_file=log_file)
    
    logger.info("="*50)
    logger.info("Starting Happy Hour Duty Bot")
    logger.info("="*50)
    
    try:
        # Create bot
        bot = RefBot()
        
        async def start_bot():
            await bot.setup()
            await bot.application.start()
            await bot.application.updater.start_polling()
            
            try:
                # Keep the bot running until interrupted
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            
            # Cleanup
            await bot.application.stop()
            await bot.application.shutdown()
        
        # Run the bot
        asyncio.run(start_bot())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()