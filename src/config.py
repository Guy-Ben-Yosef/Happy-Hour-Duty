import json
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class BotConfig:
    """Bot configuration settings"""
    bot_token: str
    admin_ids: List[int]
    notification_time: str
    response_window_hours: int
    database_file_path: str
    timezone: str
    default_meeting_day: str
    notification_day: str
    environment: str

class ConfigManager:
    """Manages bot configuration from environment and config files"""
    
    def __init__(self, config_path: str = "config.json"):
        load_dotenv()
        self.config_path = config_path
        self.config_data = self._load_config_file()
        
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            # Try to use example if main config doesn't exist
            example_path = "config.json.example"
            if os.path.exists(example_path):
                print(f"Warning: Using {example_path}. Please create {self.config_path}")
                with open(example_path, 'r') as f:
                    return json.load(f)
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_bot_config(self) -> BotConfig:
        """Get complete bot configuration"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        return BotConfig(
            bot_token=bot_token,
            admin_ids=self.config_data.get("admin_ids", []),
            notification_time=self.config_data.get("notification_time", "10:00"),
            response_window_hours=self.config_data.get("response_window_hours", 24),
            database_file_path=self.config_data.get("database_file_path", "data/db.json"),
            timezone=self.config_data.get("timezone", "UTC"),
            default_meeting_day=self.config_data.get("default_meeting_day", "Wednesday"),
            notification_day=self.config_data.get("notification_day", "Thursday"),
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user ID is an admin"""
        return user_id in self.config_data.get("admin_ids", [])