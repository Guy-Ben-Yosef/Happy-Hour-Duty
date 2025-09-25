import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from src.config import ConfigManager
from src.database.db_manager import DatabaseManager
from src.schedule.scheduler import WeeklyScheduler
from typing import Optional

class RefBot:
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
        self.logger.info("Setting up RefBot...")
        
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
        
        self.logger.info("RefBot setup complete")
    
    def _register_handlers(self):
        """Register all command and message handlers"""
        from src.handlers.signup_handler import SignupHandler
        from src.handlers.admin_commands import AdminCommandHandler
        from src.handlers.callback_handlers import CallbackHandler
        
        # Initialize handlers
        signup_handler = SignupHandler()
        admin_handler = AdminCommandHandler()
        callback_handler = CallbackHandler()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", signup_handler.start_command))
        
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