import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.models.database_schema import Participant, UserStatus
from src.utils.message_templates import MessageTemplates

logger = logging.getLogger(__name__)

class SignupHandler:
    """Handles user signup process"""
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        db_manager = context.bot_data.get('db_manager')
        
        # Check if user is already registered
        participant = db_manager.get_participant(user.id)
        
        if participant:
            if participant.status == UserStatus.APPROVED.value:
                await update.message.reply_text(
                    f"👋 Hello {participant.full_name}!\n\n"
                    "You're already registered and approved for the refreshment rotation.\n"
                    "You'll receive notifications when it's your turn."
                )
            elif participant.status == UserStatus.PENDING.value:
                await update.message.reply_text(
                    f"Hello {participant.full_name}!\n\n"
                    "Your registration is pending admin approval.\n"
                    "You'll be notified once an admin reviews your request."
                )
            else:
                await update.message.reply_text(
                    "Your account is currently inactive. Please contact an admin."
                )
        else:
            # New user - store state and ask for name
            context.user_data['awaiting_name'] = True
            await update.message.reply_text(
                "Welcome to the Refreshment Rotation Bot! 🎉\n\n"
                "To get started, please tell me your full name.\n"
                "This will be used to identify you in the rotation schedule."
            )
    
    async def handle_name_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user's name input"""
        if not context.user_data.get('awaiting_name'):
            return
        
        user = update.effective_user
        full_name = update.message.text.strip()
        
        # Validate name
        if len(full_name) < 2:
            await update.message.reply_text(
                "Please provide a valid full name (at least 2 characters)."
            )
            return
        
        if len(full_name) > 100:
            await update.message.reply_text(
                "Name is too long. Please provide a name under 100 characters."
            )
            return
        
        # Create participant
        db_manager = context.bot_data.get('db_manager')
        participant = Participant(
            telegram_id=user.id,
            full_name=full_name,
            status=UserStatus.PENDING.value
        )
        
        if db_manager.add_participant(participant):
            # Clear state
            context.user_data['awaiting_name'] = False
            
            # Notify user
            await update.message.reply_text(
                f"Thank you, {full_name}! ✅\n\n"
                "Your registration has been submitted for admin approval.\n"
                "You'll be notified once an admin reviews your request."
            )
            
            # Notify admins
            await self._notify_admins_of_new_user(context, participant)
            
            logger.info(f"New user registered: {full_name} (ID: {user.id})")
        else:
            await update.message.reply_text(
                "An error occurred during registration. Please try again or contact an admin."
            )
    
    async def _notify_admins_of_new_user(self, context: ContextTypes.DEFAULT_TYPE, participant: Participant):
        """Send approval request to all admins"""
        config = context.bot_data.get('config')
        
        # Create inline keyboard for approval
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{participant.telegram_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{participant.telegram_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            "🔔 **New User Registration**\n\n"
            f"**Name:** {participant.full_name}\n"
            f"**Telegram ID:** {participant.telegram_id}\n"
            f"**Status:** Pending Approval\n\n"
            "Please review and approve or reject this registration."
        )
        
        # Send to all admins
        for admin_id in config.admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"Sent approval request to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")