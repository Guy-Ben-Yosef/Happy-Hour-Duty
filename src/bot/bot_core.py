import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from src.config import ConfigManager
from src.database.db_manager import DatabaseManager
from src.schedule.scheduler import WeeklyScheduler
from typing import Optional

class HappyHourDutyBot:
    """Main bot class that coordinates all bot functionality"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_bot_config()
        self.db_manager = DatabaseManager(self.config.database_file_path)
        self.application: Optional[Application] = None
        self.scheduler: Optional[WeeklyScheduler] = None
        
        # Configure logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO if self.config.environment == "production" else logging.DEBUG
        )
        self.logger = logging.getLogger(__name__)
    
    async def setup(self):
        """Set up the bot application and handlers"""
        self.logger.info("Setting up Happy Hour Duty Bot...")
        
        # Create application with proper async context
        self.application = Application.builder().token(self.config.bot_token).build()
        
        # Initialize scheduler
        self.scheduler = WeeklyScheduler(self.application, self.config, self.db_manager)
        
        # Store shared objects in bot_data
        self.application.bot_data['config'] = self.config
        self.application.bot_data['config_manager'] = self.config_manager
        self.application.bot_data['db_manager'] = self.db_manager
        self.application.bot_data['scheduler'] = self.scheduler
        
        # Register handlers
        self._register_handlers()
        
        # Initialize the application
        await self.application.initialize()
        
        # Initialize the scheduler
        await self.scheduler.initialize()
        
        self.logger.info("Happy Hour Duty Bot setup complete")
    
    def _register_handlers(self):
        """Register all command and message handlers"""
        from src.handlers.signup_handler import SignupHandler
        from src.handlers.admin_commands import AdminCommandHandler
        from src.handlers.callback_handlers import CallbackHandler
        from src.handlers.help_handler import HelpHandler
        
        # Initialize handlers
        signup_handler = SignupHandler()
        admin_handler = AdminCommandHandler()
        callback_handler = CallbackHandler()
        help_handler = HelpHandler()
        
        # Register basic command handlers (these have priority)
        self.application.add_handler(CommandHandler("start", signup_handler.start_command))
        self.application.add_handler(CommandHandler("help", help_handler.help_command))
        
        # Register admin command handlers
        self.application.add_handler(CommandHandler("admin_status", admin_handler.admin_status))
        self.application.add_handler(CommandHandler("adjust_date", admin_handler.adjust_date))
        self.application.add_handler(CommandHandler("assign", admin_handler.assign))
        self.application.add_handler(CommandHandler("remove_user", admin_handler.remove_user))
        self.application.add_handler(CommandHandler("list_users", admin_handler.list_users))
        
        # Additional admin commands for testing
        self.application.add_handler(CommandHandler("trigger_weekly", admin_handler.trigger_weekly))
        self.application.add_handler(CommandHandler("reset_round", admin_handler.reset_round))
        
        # Register callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))
        
        # Register message handler for text messages (this should be last to avoid conflicts)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, signup_handler.handle_message)
        )
        
        self.logger.info("All handlers registered successfully")
    
    async def run(self):
        """Start the bot and keep it running"""
        await self.setup()
        
        try:
            # Start the application
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("Happy Hour Duty Bot is running...")
            
            # Keep the bot running until interrupted
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Error running bot: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the bot"""
        self.logger.info("Shutting down Happy Hour Duty Bot...")
        
        if self.scheduler:
            self.scheduler.shutdown()
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        self.logger.info("Happy Hour Duty bot shutdown complete")