from datetime import datetime, timedelta, time
from typing import Optional
import pytz

def get_next_wednesday() -> datetime:
    """Get the next Wednesday from today"""
    today = datetime.now()
    days_ahead = 2 - today.weekday()  # Wednesday is 2
    
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    return today + timedelta(days=days_ahead)

def get_next_thursday() -> datetime:
    """Get the next Thursday from today"""
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is 3
    
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    return today + timedelta(days=days_ahead)

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def format_date(date_obj: datetime) -> str:
    """Format date as readable string"""
    return date_obj.strftime("%A, %B %d, %Y")

def parse_time(time_str: str) -> Optional[time]:
    """Parse time string in HH:MM format"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except (ValueError, AttributeError):
        return None

def get_timezone(timezone_str: str) -> pytz.timezone:
    """Get timezone object from string"""
    try:
        return pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        return pytz.UTC

def localize_datetime(dt: datetime, timezone_str: str) -> datetime:
    """Localize datetime to specified timezone"""
    tz = get_timezone(timezone_str)
    if dt.tzinfo is None:
        return tz.localize(dt)
    else:
        return dt.astimezone(tz)

def is_within_hours(start_time: datetime, hours: int) -> bool:
    """Check if current time is within specified hours from start_time"""
    now = datetime.now()
    deadline = start_time + timedelta(hours=hours)
    return now <= deadline

def hours_until_deadline(start_time: datetime, total_hours: int) -> float:
    """Calculate hours remaining until deadline"""
    now = datetime.now()
    deadline = start_time + timedelta(hours=total_hours)
    remaining = deadline - now
    
    if remaining.total_seconds() < 0:
        return 0
    
    return remaining.total_seconds() / 3600

def next_occurrence_of_time(target_time: time, target_weekday: Optional[int] = None) -> datetime:
    """
    Get the next occurrence of a specific time
    target_weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
    """
    now = datetime.now()
    target = datetime.combine(now.date(), target_time)
    
    if target_weekday is not None:
        # Find next occurrence of the target weekday
        days_ahead = target_weekday - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and now.time() > target_time):
            days_ahead += 7
        target += timedelta(days=days_ahead)
    else:
        # If time has passed today, move to tomorrow
        if target <= now:
            target += timedelta(days=1)
    
    return target