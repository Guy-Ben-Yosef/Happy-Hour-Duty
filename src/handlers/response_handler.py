import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.message_templates import MessageTemplates
from src.notifications.notifier import NotificationManager
from src.schedule.rotation_manager import RotationManager
from src.utils.datetime_utils import get_next_wednesday

logger = logging.getLogger(__name__)

class ResponseHandler:
    """Handles participant responses to duty assignments"""
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle duty confirmation from participant"""
        query = update.callback_query
        user_id = update.effective_user.id
        db_manager = context.bot_data.get('db_manager')
        
        # Get current schedule
        schedule = db_manager.get_schedule()
        
        # Verify this user is the currently assigned one
        if schedule.current_assigned_id != user_id:
            await query.answer("This assignment is not for you.")
            return
        
        # Confirm assignment
        if db_manager.confirm_assignment():
            participant = db_manager.get_participant(user_id)
            
            # Cancel timeout if scheduler exists
            if 'scheduler' in context.bot_data:
                scheduler = context.bot_data['scheduler']
                scheduler.cancel_timeout(user_id)
            
            # Update message
            await query.edit_message_text(
                MessageTemplates.duty_confirmed(
                    participant.full_name,
                    schedule.next_meeting_date
                ),
                parse_mode='Markdown'
            )
            
            # Notify admins of confirmation
            notifier = NotificationManager(context.application, db_manager)
            await notifier.notify_admins_of_confirmation(participant, schedule.next_meeting_date)
            
            logger.info(f"User {user_id} confirmed duty for {schedule.next_meeting_date}")
            await query.answer("Thank you for confirming!")
        else:
            await query.answer("Failed to confirm assignment. Please contact an admin.")
    
    async def handle_decline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle duty decline from participant"""
        query = update.callback_query
        user_id = update.effective_user.id
        db_manager = context.bot_data.get('db_manager')
        
        # Get current schedule
        schedule = db_manager.get_schedule()
        
        # Verify this user is the currently assigned one
        if schedule.current_assigned_id != user_id:
            await query.answer("This assignment is not for you.")
            return
        
        # Cancel timeout if scheduler exists
        if 'scheduler' in context.bot_data:
            scheduler = context.bot_data['scheduler']
            scheduler.cancel_timeout(user_id)
        
        participant = db_manager.get_participant(user_id)
        
        # Update message
        await query.edit_message_text(
            MessageTemplates.duty_declined(participant.full_name),
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user_id} declined duty for {schedule.next_meeting_date}")
        await query.answer("Understood. Finding replacement...")
        
        # Trigger fallback logic through scheduler
        if 'scheduler' in context.bot_data:
            scheduler = context.bot_data['scheduler']
            # Add to skipped list and find next person
            db_manager.add_skipped_participant(user_id)
            
            # Update status
            schedule.assignment_status = "searching"
            db_manager.update_schedule(schedule)
            
            # Trigger async fallback
            await scheduler.handle_decline(user_id)
        else:
            # Fallback without scheduler (manual mode)
            rotation_manager = RotationManager(db_manager)
            next_participant = rotation_manager.skip_current_and_get_next()
            
            if next_participant:
                # Assign to next person
                meeting_date = schedule.next_meeting_date or get_next_wednesday().strftime("%Y-%m-%d")
                rotation_manager.assign_duty(next_participant.telegram_id, meeting_date)
                
                # Send notification
                notifier = NotificationManager(context.application, db_manager)
                await notifier.send_duty_notification(next_participant, meeting_date)
            else:
                # Escalate
                notifier = NotificationManager(context.application, db_manager)
                await notifier.send_escalation_alert(schedule.next_meeting_date)