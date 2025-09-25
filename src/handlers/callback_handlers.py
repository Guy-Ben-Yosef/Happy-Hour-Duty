import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.handlers.approval_handler import ApprovalHandler
from src.handlers.response_handler import ResponseHandler
from src.auth.auth_manager import AuthManager

logger = logging.getLogger(__name__)

class CallbackHandler:
    """Central handler for all callback queries from inline buttons"""
    
    def __init__(self):
        self.approval_handler = ApprovalHandler()
        self.response_handler = ResponseHandler()
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route callback queries to appropriate handlers"""
        query = update.callback_query
        data = query.data
        
        logger.debug(f"Received callback: {data} from user {update.effective_user.id}")
        
        # Parse callback data
        if data.startswith("approve_"):
            # Admin approval
            await self._handle_admin_action(update, context, data, True)
        elif data.startswith("reject_"):
            # Admin rejection
            await self._handle_admin_action(update, context, data, False)
        elif data == "confirm_duty":
            # Participant confirms duty
            await self.response_handler.handle_confirmation(update, context)
        elif data == "decline_duty":
            # Participant declines duty
            await self.response_handler.handle_decline(update, context)
        else:
            await query.answer("Unknown action")
    
    async def _handle_admin_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str, approved: bool):
        """Handle admin approval/rejection actions"""
        # Check if user is admin
        config_manager = context.bot_data.get('config_manager')
        if not config_manager.is_admin(update.effective_user.id):
            await update.callback_query.answer("Unauthorized: Admin access required")
            return
        
        # Extract user ID from callback data
        try:
            if approved:
                user_id = int(data.replace("approve_", ""))
            else:
                user_id = int(data.replace("reject_", ""))
            
            await self.approval_handler.handle_approval(update, context, user_id, approved)
        except ValueError:
            logger.error(f"Invalid callback data: {data}")
            await update.callback_query.answer("Invalid data format")