from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    INACTIVE = "inactive"

@dataclass
class Participant:
    """Participant data model"""
    telegram_id: int
    full_name: str
    status: str = UserStatus.PENDING.value
    joined_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Participant':
        return cls(**data)

@dataclass
class Schedule:
    """Schedule data model"""
    rotation_list: List[int] = field(default_factory=list)
    next_pointer_index: int = 0
    last_assignment_date: Optional[str] = None
    next_meeting_date: Optional[str] = None
    skipped_this_round: List[int] = field(default_factory=list)
    current_assigned_id: Optional[int] = None
    assignment_status: str = "pending"  # pending, confirmed, searching
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        return cls(**data)