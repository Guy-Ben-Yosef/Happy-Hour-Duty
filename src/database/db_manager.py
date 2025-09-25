import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from threading import Lock
from src.models.database_schema import Participant, Schedule, UserStatus

class DatabaseManager:
    """Manages file-based JSON database operations"""
    
    def __init__(self, db_path: str = "data/db.json"):
        self.db_path = db_path
        self.lock = Lock()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if not os.path.exists(self.db_path):
            self._initialize_database()
    
    def _initialize_database(self):
        """Initialize empty database structure"""
        initial_db = {
            "participants": {},
            "schedule": {
                "rotation_list": [],
                "next_pointer_index": 0,
                "last_assignment_date": None,
                "next_meeting_date": None,
                "skipped_this_round": [],
                "current_assigned_id": None,
                "assignment_status": "pending"
            },
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
        }
        self._write_db(initial_db)
    
    def _read_db(self) -> Dict[str, Any]:
        """Read database from file"""
        with self.lock:
            with open(self.db_path, 'r') as f:
                return json.load(f)
    
    def _write_db(self, data: Dict[str, Any]):
        """Write database to file"""
        with self.lock:
            data["metadata"]["last_modified"] = datetime.now().isoformat()
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    # Participant operations
    def add_participant(self, participant: Participant) -> bool:
        """Add a new participant to the database"""
        db = self._read_db()
        
        if str(participant.telegram_id) in db["participants"]:
            return False
        
        db["participants"][str(participant.telegram_id)] = participant.to_dict()
        self._write_db(db)
        return True
    
    def get_participant(self, telegram_id: int) -> Optional[Participant]:
        """Get participant by telegram ID"""
        db = self._read_db()
        participant_data = db["participants"].get(str(telegram_id))
        
        if participant_data:
            return Participant.from_dict(participant_data)
        return None
    
    def update_participant(self, participant: Participant) -> bool:
        """Update existing participant"""
        db = self._read_db()
        
        if str(participant.telegram_id) not in db["participants"]:
            return False
        
        db["participants"][str(participant.telegram_id)] = participant.to_dict()
        
        # If status changed to approved, add to rotation
        if participant.status == UserStatus.APPROVED.value:
            if participant.telegram_id not in db["schedule"]["rotation_list"]:
                db["schedule"]["rotation_list"].append(participant.telegram_id)
        
        self._write_db(db)
        return True
    
    def remove_participant(self, telegram_id: int) -> bool:
        """Remove participant from database"""
        db = self._read_db()
        
        if str(telegram_id) not in db["participants"]:
            return False
        
        del db["participants"][str(telegram_id)]
        
        # Remove from rotation list
        if telegram_id in db["schedule"]["rotation_list"]:
            db["schedule"]["rotation_list"].remove(telegram_id)
            # Adjust pointer if necessary
            if db["schedule"]["next_pointer_index"] >= len(db["schedule"]["rotation_list"]):
                db["schedule"]["next_pointer_index"] = 0
        
        self._write_db(db)
        return True
    
    def get_all_participants(self, status: Optional[str] = None) -> List[Participant]:
        """Get all participants, optionally filtered by status"""
        db = self._read_db()
        participants = []
        
        for participant_data in db["participants"].values():
            participant = Participant.from_dict(participant_data)
            if status is None or participant.status == status:
                participants.append(participant)
        
        return participants
    
    def get_pending_participants(self) -> List[Participant]:
        """Get all pending participants awaiting approval"""
        return self.get_all_participants(status=UserStatus.PENDING.value)
    
    def get_approved_participants(self) -> List[Participant]:
        """Get all approved participants"""
        return self.get_all_participants(status=UserStatus.APPROVED.value)
    
    # Schedule operations
    def get_schedule(self) -> Schedule:
        """Get current schedule"""
        db = self._read_db()
        return Schedule.from_dict(db["schedule"])
    
    def update_schedule(self, schedule: Schedule) -> bool:
        """Update schedule"""
        db = self._read_db()
        db["schedule"] = schedule.to_dict()
        self._write_db(db)
        return True
    
    def get_next_assigned_participant(self) -> Optional[Participant]:
        """Get the next participant to be assigned"""
        schedule = self.get_schedule()
        
        if not schedule.rotation_list:
            return None
        
        if schedule.next_pointer_index >= len(schedule.rotation_list):
            schedule.next_pointer_index = 0
            self.update_schedule(schedule)
        
        next_id = schedule.rotation_list[schedule.next_pointer_index]
        return self.get_participant(next_id)
    
    def move_to_next_participant(self) -> bool:
        """Move pointer to next participant in rotation"""
        schedule = self.get_schedule()
        
        if not schedule.rotation_list:
            return False
        
        schedule.next_pointer_index = (schedule.next_pointer_index + 1) % len(schedule.rotation_list)
        return self.update_schedule(schedule)
    
    def add_skipped_participant(self, telegram_id: int) -> bool:
        """Add participant to skipped list for current round"""
        schedule = self.get_schedule()
        
        if telegram_id not in schedule.skipped_this_round:
            schedule.skipped_this_round.append(telegram_id)
            return self.update_schedule(schedule)
        
        return False
    
    def clear_skipped_participants(self) -> bool:
        """Clear the skipped participants list (after successful confirmation)"""
        schedule = self.get_schedule()
        schedule.skipped_this_round = []
        return self.update_schedule(schedule)
    
    def set_current_assignment(self, telegram_id: int, meeting_date: str) -> bool:
        """Set the current assignment"""
        schedule = self.get_schedule()
        schedule.current_assigned_id = telegram_id
        schedule.next_meeting_date = meeting_date
        schedule.last_assignment_date = datetime.now().isoformat()
        schedule.assignment_status = "pending"
        return self.update_schedule(schedule)
    
    def confirm_assignment(self) -> bool:
        """Confirm the current assignment"""
        schedule = self.get_schedule()
        schedule.assignment_status = "confirmed"
        schedule.skipped_this_round = []  # Clear skipped list
        self.move_to_next_participant()  # Move pointer for next week
        return self.update_schedule(schedule)