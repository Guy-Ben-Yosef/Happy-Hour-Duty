import logging
from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from telegram.error import TelegramError
from src.database.db_manager import DatabaseManager
from src.models.database_schema import Participant
from src.utils.message_templates import MessageTemplates
from src.utils.datetime_utils import format_date, parse_date

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages all bot notifications"""
    
    def __init__(self, application: Application, db_manager: DatabaseManager):
        self.application = application
        self.db_manager = db_manager
        self.bot = application.bot
    
    async def send_duty_notification(self, participant: Participant, meeting_date: str) -> bool:
        """Send duty assignment notification to participant"""
        try:
            # Parse and format date
            date_obj = parse_date(meeting_date)
            formatted_date = format_date(date_obj) if date_obj else meeting_date
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_duty"),
                    InlineKeyboardButton("❌ Cannot", callback_data="decline_duty")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send notification
            message = MessageTemplates.duty_notification(participant.full_name, formatted_date)
            
            await self.bot.send_message(
                chat_id=participant.telegram_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            logger.info(f"Duty notification sent to {participant.full_name} for {meeting_date}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send notification to {participant.full_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}", exc_info=True)
            return False
    
    async def send_confirmation_acknowledgment(self, participant: Participant, meeting_date: str) -> bool:
        """Send confirmation acknowledgment to participant"""
        try:
            # Parse and format date
            date_obj = parse_date(meeting_date)
            formatted_date = format_date(date_obj) if date_obj else meeting_date
            
            message = MessageTemplates.duty_confirmed(participant.full_name, formatted_date)
            
            await self.bot.send_message(
                chat_id=participant.telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send confirmation to {participant.full_name}: {e}")
            return False
    
    async def send_decline_acknowledgment(self, participant: Participant) -> bool:
        """Send decline acknowledgment to participant"""
        try:
            message = MessageTemplates.duty_declined(participant.full_name)
            
            await self.bot.send_message(
                chat_id=participant.telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send decline acknowledgment to {participant.full_name}: {e}")
            return False
    
    async def send_escalation_alert(self, meeting_date: str) -> None:
        """Send escalation alert to all admins"""
        config = self.application.bot_data.get('config')
        
        if not config:
            logger.error("Config not found in bot_data")
            return
        
        # Parse and format date
        date_obj = parse_date(meeting_date)
        formatted_date = format_date(date_obj) if date_obj else meeting_date
        
        message = MessageTemplates.escalation_alert(formatted_date)
        
        # Send to all admins
        for admin_id in config.admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Escalation alert sent to admin {admin_id}")
            except TelegramError as e:
                logger.error(f"Failed to send escalation to admin {admin_id}: {e}")
    
    async def send_reminder(self, participant: Participant, hours_remaining: int) -> bool:
        """Send reminder to participant about pending response"""
        try:
            message = MessageTemplates.timeout_warning(hours_remaining)
            
            # Include response buttons again
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_duty"),
                    InlineKeyboardButton("❌ Cannot", callback_data="decline_duty")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=participant.telegram_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send reminder to {participant.full_name}: {e}")
            return False
    
    async def notify_admins_of_confirmation(self, participant: Participant, meeting_date: str) -> None:
        """Notify admins that someone has confirmed duty"""
        config = self.application.bot_data.get('config')
        
        if not config:
            return
        
        # Parse and format date
        date_obj = parse_date(meeting_date)
        formatted_date = format_date(date_obj) if date_obj else meeting_date
        
        message = (
            f"✅ **Duty Confirmed**\n\n"
            f"{participant.full_name} has confirmed happy hour duty for {formatted_date}"
        )
        
        # Send to all admins
        for admin_id in config.admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except TelegramError as e:
                logger.error(f"Failed to notify admin {admin_id} of confirmation: {e}")