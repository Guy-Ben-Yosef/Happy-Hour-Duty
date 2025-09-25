import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from src.database.db_manager import DatabaseManager
from src.models.database_schema import Participant, Schedule
from src.utils.datetime_utils import get_next_wednesday

logger = logging.getLogger(__name__)

class RotationManager:
    """Manages the rotation logic for duty assignments"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_next_available_participant(self) -> Optional[Participant]:
        """
        Get the next available participant who hasn't been skipped this round
        Returns None if all participants have been exhausted
        """
        schedule = self.db_manager.get_schedule()
        
        if not schedule.rotation_list:
            logger.warning("No participants in rotation list")
            return None
        
        # Get list of skipped participants this round
        skipped = set(schedule.skipped_this_round)
        
        # Check if all participants have been skipped
        if len(skipped) >= len(schedule.rotation_list):
            logger.warning("All participants have been exhausted for this round")
            return None
        
        # Start from current pointer and find next non-skipped participant
        start_index = schedule.next_pointer_index
        checked_count = 0
        
        while checked_count < len(schedule.rotation_list):
            current_index = (start_index + checked_count) % len(schedule.rotation_list)
            participant_id = schedule.rotation_list[current_index]
            
            if participant_id not in skipped:
                participant = self.db_manager.get_participant(participant_id)
                if participant and participant.status == "approved":
                    # Update the pointer to this position
                    schedule.next_pointer_index = current_index
                    self.db_manager.update_schedule(schedule)
                    return participant
            
            checked_count += 1
        
        return None
    
    def assign_duty(self, participant_id: int, meeting_date: Optional[str] = None) -> bool:
        """Assign duty to a specific participant"""
        if not meeting_date:
            meeting_date = get_next_wednesday().strftime("%Y-%m-%d")
        
        return self.db_manager.set_current_assignment(participant_id, meeting_date)
    
    def skip_current_and_get_next(self) -> Optional[Participant]:
        """Skip current assigned participant and get the next one"""
        schedule = self.db_manager.get_schedule()
        
        # Add current to skipped list
        if schedule.current_assigned_id:
            self.db_manager.add_skipped_participant(schedule.current_assigned_id)
        
        # Move pointer and get next
        self.db_manager.move_to_next_participant()
        return self.get_next_available_participant()
    
    def is_rotation_exhausted(self) -> bool:
        """Check if all participants have been skipped/declined"""
        schedule = self.db_manager.get_schedule()
        
        if not schedule.rotation_list:
            return True
        
        return len(schedule.skipped_this_round) >= len(schedule.rotation_list)
    
    def reset_round(self):
        """Reset the skipped list for a new round (after confirmation)"""
        self.db_manager.clear_skipped_participants()
    
    def get_rotation_status(self) -> dict:
        """Get detailed rotation status"""
        schedule = self.db_manager.get_schedule()
        approved_participants = self.db_manager.get_approved_participants()
        
        status = {
            "total_participants": len(approved_participants),
            "rotation_size": len(schedule.rotation_list),
            "current_pointer": schedule.next_pointer_index,
            "skipped_count": len(schedule.skipped_this_round),
            "is_exhausted": self.is_rotation_exhausted(),
            "current_assigned": None,
            "next_in_line": None
        }
        
        if schedule.current_assigned_id:
            current = self.db_manager.get_participant(schedule.current_assigned_id)
            if current:
                status["current_assigned"] = current.full_name
        
        next_participant = self.get_next_available_participant()
        if next_participant:
            status["next_in_line"] = next_participant.full_name
        
        return status