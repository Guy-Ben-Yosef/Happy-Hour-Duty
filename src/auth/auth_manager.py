from typing import List, Optional
from telegram import Update
from src.config import ConfigManager
from src.database.db_manager import DatabaseManager
from functools import wraps

class AuthManager:
    """Manages authentication and authorization for the bot"""
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return self.config_manager.is_admin(user_id)
    
    def is_approved_participant(self, user_id: int) -> bool:
        """Check if user is an approved participant"""
        participant = self.db_manager.get_participant(user_id)
        return participant is not None and participant.status == "approved"
    
    def is_registered(self, user_id: int) -> bool:
        """Check if user is registered (any status)"""
        return self.db_manager.get_participant(user_id) is not None
    
    def get_user_role(self, user_id: int) -> str:
        """Get user's role"""
        if self.is_admin(user_id):
            return "admin"
        elif self.is_approved_participant(user_id):
            return "participant"
        elif self.is_registered(user_id):
            return "pending"
        else:
            return "unregistered"

def admin_required(func):
    """Decorator to require admin privileges for a command"""
    @wraps(func)
    async def wrapper(self, update: Update, context, *args, **kwargs):
        config_manager = context.bot_data.get('config_manager')
        user_id = update.effective_user.id
        
        if not config_manager or not config_manager.is_admin(user_id):
            await update.message.reply_text(
                "❌ This command is restricted to administrators only."
            )
            return
        
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def participant_required(func):
    """Decorator to require approved participant status for a command"""
    @wraps(func)
    async def wrapper(self, update: Update, context, *args, **kwargs):
        db_manager = context.bot_data.get('db_manager')
        user_id = update.effective_user.id
        
        participant = db_manager.get_participant(user_id)
        if not participant or participant.status != "approved":
            await update.message.reply_text(
                "❌ This command is only available to approved participants."
            )
            return
        
        return await func(self, update, context, *args, **kwargs)
    return wrapper