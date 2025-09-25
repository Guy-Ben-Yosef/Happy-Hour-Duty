import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from src.config import BotConfig
from src.database.db_manager import DatabaseManager
from src.schedule.rotation_manager import RotationManager
from src.notifications.notifier import NotificationManager
from src.utils.datetime_utils import parse_time, get_next_wednesday

logger = logging.getLogger(__name__)

class WeeklyScheduler:
    """Manages weekly notification scheduling"""
    
    def __init__(self, application: Application, config: BotConfig, db_manager: DatabaseManager):
        self.application = application
        self.config = config
        self.db_manager = db_manager
        self.rotation_manager = RotationManager(db_manager)
        self.notification_manager = NotificationManager(application, db_manager)
        self.scheduler = AsyncIOScheduler(timezone=config.timezone)
        self.timeout_tasks: Dict[int, asyncio.Task] = {}
    
    async def initialize(self):
        """Initialize the scheduler and set up weekly notifications"""
        # Parse notification time
        notification_time = parse_time(self.config.notification_time)
        if not notification_time:
            logger.error(f"Invalid notification time: {self.config.notification_time}")
            return
        
        # Schedule weekly notification (every Thursday by default)
        trigger = CronTrigger(
            day_of_week='thu',  # Thursday
            hour=notification_time.hour,
            minute=notification_time.minute,
            timezone=self.config.timezone
        )
        
        self.scheduler.add_job(
            self.weekly_notification_job,
            trigger=trigger,
            id='weekly_notification',
            replace_existing=True
        )
        
        # Check for any pending assignments on startup
        self.scheduler.add_job(
            self.check_pending_assignments,
            'interval',
            minutes=30,  # Check every 30 minutes
            id='pending_check',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler initialized. Weekly notifications on Thursday at {self.config.notification_time}")
        
        # Run initial check
        await self.check_pending_assignments()
    
    async def weekly_notification_job(self):
        """Job that runs weekly to send notifications"""
        logger.info("Running weekly notification job")
        
        try:
            # Get next available participant
            participant = self.rotation_manager.get_next_available_participant()
            
            if not participant:
                # All participants exhausted - escalate
                await self.escalate_to_admins()
                return
            
            # Set meeting date (next Wednesday)
            meeting_date = get_next_wednesday()
            
            # Assign duty
            self.rotation_manager.assign_duty(participant.telegram_id, meeting_date.strftime("%Y-%m-%d"))
            
            # Send notification
            success = await self.notification_manager.send_duty_notification(
                participant,
                meeting_date.strftime("%Y-%m-%d")
            )
            
            if success:
                # Start timeout timer
                await self.start_response_timeout(participant.telegram_id)
                logger.info(f"Weekly notification sent to {participant.full_name}")
            else:
                logger.error(f"Failed to send notification to {participant.full_name}")
                # Try next participant
                await self.handle_notification_failure(participant.telegram_id)
        
        except Exception as e:
            logger.error(f"Error in weekly notification job: {e}", exc_info=True)
    
    async def start_response_timeout(self, user_id: int):
        """Start timeout timer for user response"""
        # Cancel existing timeout if any
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
        
        # Create new timeout task
        timeout_task = asyncio.create_task(
            self.handle_response_timeout(user_id)
        )
        self.timeout_tasks[user_id] = timeout_task
    
    async def handle_response_timeout(self, user_id: int):
        """Handle timeout when user doesn't respond within window"""
        try:
            # Wait for response window
            await asyncio.sleep(self.config.response_window_hours * 3600)
            
            # Check if assignment is still pending
            schedule = self.db_manager.get_schedule()
            if schedule.current_assigned_id == user_id and schedule.assignment_status == "pending":
                logger.info(f"Response timeout for user {user_id}")
                
                # Mark as skipped and try next person
                await self.handle_decline(user_id)
        
        except asyncio.CancelledError:
            # Timeout was cancelled (user responded)
            pass
        except Exception as e:
            logger.error(f"Error handling timeout for user {user_id}: {e}")
    
    async def handle_decline(self, user_id: int):
        """Handle when a user declines or times out"""
        logger.info(f"Handling decline/timeout for user {user_id}")
        
        # Get next participant
        next_participant = self.rotation_manager.skip_current_and_get_next()
        
        if not next_participant:
            # All exhausted - escalate
            await self.escalate_to_admins()
            return
        
        # Get current meeting date
        schedule = self.db_manager.get_schedule()
        meeting_date = schedule.next_meeting_date or get_next_wednesday().strftime("%Y-%m-%d")
        
        # Assign to next person
        self.rotation_manager.assign_duty(next_participant.telegram_id, meeting_date)
        
        # Send notification
        success = await self.notification_manager.send_duty_notification(
            next_participant,
            meeting_date
        )
        
        if success:
            await self.start_response_timeout(next_participant.telegram_id)
        else:
            # Continue to next
            await self.handle_notification_failure(next_participant.telegram_id)
    
    async def handle_notification_failure(self, user_id: int):
        """Handle when notification fails to send"""
        logger.warning(f"Notification failed for user {user_id}, trying next")
        await self.handle_decline(user_id)
    
    async def escalate_to_admins(self):
        """Send escalation alert to all admins"""
        schedule = self.db_manager.get_schedule()
        meeting_date = schedule.next_meeting_date or get_next_wednesday().strftime("%Y-%m-%d")
        
        await self.notification_manager.send_escalation_alert(meeting_date)
        logger.warning(f"Escalated to admins - no one available for {meeting_date}")
    
    async def check_pending_assignments(self):
        """Check for any pending assignments that need attention"""
        try:
            schedule = self.db_manager.get_schedule()
            
            if schedule.current_assigned_id and schedule.assignment_status == "pending":
                # Check if assignment is overdue
                if schedule.last_assignment_date:
                    assignment_time = datetime.fromisoformat(schedule.last_assignment_date)
                    deadline = assignment_time + timedelta(hours=self.config.response_window_hours)
                    
                    if datetime.now() > deadline:
                        logger.info("Found overdue assignment, handling timeout")
                        await self.handle_decline(schedule.current_assigned_id)
        
        except Exception as e:
            logger.error(f"Error checking pending assignments: {e}")
    
    def cancel_timeout(self, user_id: int):
        """Cancel timeout for a user who has responded"""
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
            del self.timeout_tasks[user_id]
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        
        # Cancel all timeout tasks
        for task in self.timeout_tasks.values():
            task.cancel()
        self.timeout_tasks.clear()