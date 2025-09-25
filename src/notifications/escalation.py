import logging
from typing import List
from telegram.ext import Application
from src.config import BotConfig
from src.database.db_manager import DatabaseManager
from src.notifications.notifier import NotificationManager

logger = logging.getLogger(__name__)

class EscalationHandler:
    """Handles escalation scenarios when no one can take duty"""
    
    def __init__(self, application: Application, config: BotConfig, db_manager: DatabaseManager):
        self.application = application
        self.config = config
        self.db_manager = db_manager
        self.notifier = NotificationManager(application, db_manager)
    
    async def check_and_escalate(self) -> bool:
        """
        Check if escalation is needed and handle it
        Returns True if escalated, False otherwise
        """
        schedule = self.db_manager.get_schedule()
        
        # Check if all participants have been exhausted
        if not schedule.rotation_list:
            logger.warning("No participants in rotation list")
            await self.escalate("No participants in rotation list")
            return True
        
        if len(schedule.skipped_this_round) >= len(schedule.rotation_list):
            logger.warning("All participants have declined or timed out")
            await self.escalate("All participants have declined or timed out")
            return True
        
        return False
    
    async def escalate(self, reason: str):
        """Escalate to admins with specific reason"""
        schedule = self.db_manager.get_schedule()
        meeting_date = schedule.next_meeting_date or "TBD"
        
        # Send detailed escalation message
        message = (
            "⚠️ **URGENT: Escalation Required**\n\n"
            f"**Meeting Date:** {meeting_date}\n"
            f"**Reason:** {reason}\n\n"
            "**Current Status:**\n"
        )
        
        # Add skipped participants info
        if schedule.skipped_this_round:
            message += f"• {len(schedule.skipped_this_round)} participants declined/timed out\n"
            
            # List who declined
            declined_names = []
            for user_id in schedule.skipped_this_round[:5]:  # Show first 5
                participant = self.db_manager.get_participant(user_id)
                if participant:
                    declined_names.append(participant.full_name)
            
            if declined_names:
                message += f"• Declined by: {', '.join(declined_names)}"
                if len(schedule.skipped_this_round) > 5:
                    message += f" and {len(schedule.skipped_this_round) - 5} others"
                message += "\n"
        
        message += "\n**Action Required:** Please manually assign someone or adjust the schedule."
        
        # Send to all admins
        for admin_id in self.config.admin_ids:
            try:
                await self.application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Escalation sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send escalation to admin {admin_id}: {e}")