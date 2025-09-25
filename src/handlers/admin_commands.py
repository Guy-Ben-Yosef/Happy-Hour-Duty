import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from src.auth.auth_manager import admin_required
from src.utils.message_templates import MessageTemplates
from src.utils.datetime_utils import parse_date, format_date, get_next_wednesday

logger = logging.getLogger(__name__)

class AdminCommandHandler:
    """Handles all admin-specific commands"""
    
    @admin_required
    async def admin_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display current rotation status and next assigned person"""
        db_manager = context.bot_data.get('db_manager')
        
        # Get schedule
        schedule = db_manager.get_schedule()
        
        # Get current assigned participant
        current_assigned = None
        if schedule.current_assigned_id:
            participant = db_manager.get_participant(schedule.current_assigned_id)
            if participant:
                current_assigned = f"{participant.full_name} ({participant.telegram_id})"
        
        # Get next participant
        next_person = None
        if schedule.rotation_list:
            next_participant = db_manager.get_next_assigned_participant()
            if next_participant:
                next_person = f"{next_participant.full_name} ({next_participant.telegram_id})"
        
        # Format and send status
        status_text = MessageTemplates.format_rotation_status(
            current_assigned, 
            next_person, 
            schedule.next_meeting_date
        )
        
        # Add rotation list
        status_text += "\n\n**📋 Full Rotation Order:**\n"
        if schedule.rotation_list:
            for i, user_id in enumerate(schedule.rotation_list):
                participant = db_manager.get_participant(user_id)
                if participant:
                    pointer = "👉 " if i == schedule.next_pointer_index else "   "
                    status_text += f"{pointer}{i+1}. {participant.full_name}\n"
        else:
            status_text += "No participants in rotation.\n"
        
        # Add skipped this round
        if schedule.skipped_this_round:
            status_text += "\n**⏭️ Skipped This Round:**\n"
            for user_id in schedule.skipped_this_round:
                participant = db_manager.get_participant(user_id)
                if participant:
                    status_text += f"• {participant.full_name}\n"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    @admin_required
    async def adjust_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually adjust the next meeting date"""
        db_manager = context.bot_data.get('db_manager')
        
        # Parse command arguments
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Usage: /adjust_date YYYY-MM-DD\n"
                "Example: /adjust_date 2025-10-15"
            )
            return
        
        date_str = context.args[0]
        
        # Validate date format
        try:
            meeting_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if date is in the future
            if meeting_date.date() <= datetime.now().date():
                await update.message.reply_text(
                    "❌ Meeting date must be in the future."
                )
                return
            
            # Update schedule
            schedule = db_manager.get_schedule()
            schedule.next_meeting_date = date_str
            
            if db_manager.update_schedule(schedule):
                await update.message.reply_text(
                    f"✅ Meeting date adjusted to: **{date_str}**\n\n"
                    f"Day: {meeting_date.strftime('%A')}",
                    parse_mode='Markdown'
                )
                logger.info(f"Admin {update.effective_user.id} adjusted meeting date to {date_str}")
            else:
                await update.message.reply_text("❌ Failed to update meeting date.")
                
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid date format. Please use YYYY-MM-DD\n"
                "Example: /adjust_date 2025-10-15"
            )
    
    @admin_required
    async def assign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually assign duty to a specific participant"""
        db_manager = context.bot_data.get('db_manager')
        
        # Parse command arguments
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Usage: /assign PARTICIPANT_ID\n"
                "Example: /assign 123456789\n\n"
                "Use /list_users to see participant IDs"
            )
            return
        
        try:
            participant_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid participant ID. Must be a number.")
            return
        
        # Check if participant exists and is approved
        participant = db_manager.get_participant(participant_id)
        
        if not participant:
            await update.message.reply_text(f"❌ No participant found with ID: {participant_id}")
            return
        
        if participant.status != "approved":
            await update.message.reply_text(
                f"❌ Participant {participant.full_name} is not approved.\n"
                f"Current status: {participant.status}"
            )
            return
        
        # Set meeting date if not set
        schedule = db_manager.get_schedule()
        if not schedule.next_meeting_date:
            next_wednesday = get_next_wednesday()
            schedule.next_meeting_date = next_wednesday.strftime("%Y-%m-%d")
        
        # Manually assign
        if db_manager.set_current_assignment(participant_id, schedule.next_meeting_date):
            # Update schedule to mark as manually assigned
            schedule = db_manager.get_schedule()
            schedule.assignment_status = "pending"
            db_manager.update_schedule(schedule)
            
            await update.message.reply_text(
                f"✅ Manually assigned refreshment duty to:\n"
                f"**{participant.full_name}** (ID: {participant_id})\n\n"
                f"Meeting date: {schedule.next_meeting_date}\n\n"
                f"They will be notified shortly.",
                parse_mode='Markdown'
            )
            
            # TODO: Trigger notification to assigned person
            logger.info(f"Admin {update.effective_user.id} manually assigned duty to {participant_id}")
        else:
            await update.message.reply_text("❌ Failed to assign duty.")
    
    @admin_required
    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a participant from the rotation"""
        db_manager = context.bot_data.get('db_manager')
        
        # Parse command arguments
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Usage: /remove_user PARTICIPANT_ID\n"
                "Example: /remove_user 123456789\n\n"
                "⚠️ This will permanently remove the user from the rotation."
            )
            return
        
        try:
            participant_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid participant ID. Must be a number.")
            return
        
        # Get participant info before removal
        participant = db_manager.get_participant(participant_id)
        
        if not participant:
            await update.message.reply_text(f"❌ No participant found with ID: {participant_id}")
            return
        
        # Remove participant
        if db_manager.remove_participant(participant_id):
            await update.message.reply_text(
                f"✅ Successfully removed participant:\n"
                f"**{participant.full_name}** (ID: {participant_id})\n\n"
                f"They have been removed from the rotation list.",
                parse_mode='Markdown'
            )
            logger.info(f"Admin {update.effective_user.id} removed participant {participant_id}")
        else:
            await update.message.reply_text("❌ Failed to remove participant.")
    
    @admin_required
    async def list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all participants with their status"""
        db_manager = context.bot_data.get('db_manager')
        
        # Get all participants
        all_participants = db_manager.get_all_participants()
        
        if not all_participants:
            await update.message.reply_text("No participants registered yet.")
            return
        
        # Group by status
        approved = [p for p in all_participants if p.status == "approved"]
        pending = [p for p in all_participants if p.status == "pending"]
        inactive = [p for p in all_participants if p.status == "inactive"]
        
        text = "**👥 All Participants**\n\n"
        
        if approved:
            text += "**✅ Approved:**\n"
            for p in approved:
                text += f"• {p.full_name} (ID: {p.telegram_id})\n"
            text += "\n"
        
        if pending:
            text += "**⏳ Pending Approval:**\n"
            for p in pending:
                text += f"• {p.full_name} (ID: {p.telegram_id})\n"
            text += "\n"
        
        if inactive:
            text += "**❌ Inactive:**\n"
            for p in inactive:
                text += f"• {p.full_name} (ID: {p.telegram_id})\n"
            text += "\n"
        
        text += f"**Total:** {len(all_participants)} participants"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @admin_required
    async def trigger_weekly(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually trigger the weekly notification (for testing)"""
        scheduler = context.bot_data.get('scheduler')
        
        if not scheduler:
            await update.message.reply_text("❌ Scheduler not initialized")
            return
        
        await update.message.reply_text("🔄 Triggering weekly notification job...")
        
        try:
            # Run the weekly notification job manually
            await scheduler.weekly_notification_job()
            await update.message.reply_text("✅ Weekly notification job completed")
        except Exception as e:
            logger.error(f"Error triggering weekly job: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    @admin_required
    async def reset_round(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset the current round (clear skipped list)"""
        db_manager = context.bot_data.get('db_manager')
        
        # Clear skipped participants
        db_manager.clear_skipped_participants()
        
        # Reset assignment status
        schedule = db_manager.get_schedule()
        schedule.assignment_status = "pending"
        schedule.current_assigned_id = None
        db_manager.update_schedule(schedule)
        
        await update.message.reply_text(
            "✅ Round reset successfully!\n\n"
            "• Skipped list cleared\n"
            "• Assignment status reset\n"
            "• Ready for new assignments",
            parse_mode='Markdown'
        )