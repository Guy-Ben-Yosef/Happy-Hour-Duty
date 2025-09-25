import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.auth.auth_manager import AuthManager

logger = logging.getLogger(__name__)

class HelpHandler:
    """Handles help command and provides role-based command information"""
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command with role-based responses"""
        user_id = update.effective_user.id
        config_manager = context.bot_data.get('config_manager')
        db_manager = context.bot_data.get('db_manager')
        
        # Determine user role
        user_role = self._get_user_role(user_id, config_manager, db_manager)
        
        # Generate appropriate help message
        if user_role == "admin":
            help_text = self._get_admin_help()
        elif user_role == "participant":
            help_text = self._get_participant_help()
        elif user_role == "pending":
            help_text = self._get_pending_help()
        else:
            help_text = self._get_unregistered_help()
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    def _get_user_role(self, user_id: int, config_manager, db_manager) -> str:
        """Determine user's role"""
        if config_manager and config_manager.is_admin(user_id):
            return "admin"
        
        if db_manager:
            participant = db_manager.get_participant(user_id)
            if participant:
                if participant.status == "approved":
                    return "participant"
                elif participant.status == "pending":
                    return "pending"
                else:
                    return "inactive"
        
        return "unregistered"
    
    def _get_unregistered_help(self) -> str:
        """Help for unregistered users"""
        return (
            "🤖 **RefBot - Refreshment Rotation Bot**\n\n"
            "Welcome! This bot manages weekly refreshment duty assignments.\n\n"
            "**Available Commands:**\n"
            "• `/start` - Register for the refreshment rotation\n"
            "• `/help` - Show this help message\n\n"
            "**Getting Started:**\n"
            "1. Use `/start` to begin registration\n"
            "2. Provide your full name when prompted\n"
            "3. Wait for admin approval\n"
            "4. Receive notifications when it's your turn!\n\n"
            "📞 Contact an administrator if you need assistance."
        )
    
    def _get_pending_help(self) -> str:
        """Help for users pending approval"""
        return (
            "⏳ **Your Registration is Pending**\n\n"
            "Thanks for registering! Your account is awaiting admin approval.\n\n"
            "**Available Commands:**\n"
            "• `/help` - Show this help message\n\n"
            "**What's Next:**\n"
            "• An administrator will review your registration\n"
            "• You'll be notified once approved\n"
            "• After approval, you'll be added to the rotation\n\n"
            "📞 Contact an administrator if you have questions."
        )
    
    def _get_participant_help(self) -> str:
        """Help for approved participants"""
        return (
            "✅ **RefBot - You're an Approved Participant**\n\n"
            "You're part of the refreshment rotation! Here's what you need to know:\n\n"
            "**Available Commands:**\n"
            "• `/help` - Show this help message\n\n"
            "**How It Works:**\n"
            "🔔 **Notifications:** You'll receive a message when it's your turn\n"
            "⏰ **Response Time:** You have 24 hours to confirm or decline\n"
            "✅ **Confirm:** Click the confirm button if you can bring refreshments\n"
            "❌ **Decline:** Click decline if you can't (duty goes to next person)\n\n"
            "**Important Notes:**\n"
            "• The bot will automatically find someone else if you decline\n"
            "• You stay in the rotation for future weeks\n"
            "• Meeting day is usually Wednesday\n"
            "• Notifications are sent on Thursday mornings\n\n"
            "📞 Contact an administrator if you have questions or issues."
        )
    
    def _get_admin_help(self) -> str:
        """Help for administrators"""
        participant_section = self._get_participant_help().replace("✅ **RefBot - You're an Approved Participant**", "**As a Participant**")
        
        return (
            "👮 **RefBot - Administrator Commands**\n\n"
            "**User Management:**\n"
            "• `/list_users` - Show all participants and their status\n"
            "• `/remove_user <ID>` - Remove a user from rotation\n\n"
            "**Rotation Management:**\n"
            "• `/admin_status` - View current rotation status\n"
            "• `/assign <ID>` - Manually assign duty to specific user\n"
            "• `/adjust_date YYYY-MM-DD` - Change next meeting date\n"
            "• `/reset_round` - Reset current round (clear skipped list)\n\n"
            "**Testing & Maintenance:**\n"
            "• `/trigger_weekly` - Manually trigger weekly notification\n"
            "• `/help` - Show this help message\n\n"
            "**How to Use Commands:**\n"
            "• Replace `<ID>` with actual Telegram user ID\n"
            "• Use `/list_users` to find user IDs\n"
            "• Dates must be in YYYY-MM-DD format\n\n"
            "**Automatic Features:**\n"
            "🔄 Weekly notifications sent every Thursday at 10:00 AM\n"
            "📅 Default meeting day: Wednesday\n"
            "⏰ Users have 24 hours to respond\n"
            "🚨 Escalation alerts sent if everyone declines\n\n"
            "---\n\n" +
            participant_section
        )