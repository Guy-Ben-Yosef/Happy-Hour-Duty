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
        """Load configuration from CONFIG_JSON env var, JSON file, or use defaults"""
        # Try to load from CONFIG_JSON environment variable first
        config_json = os.getenv('CONFIG_JSON')
        if config_json:
            try:
                return json.loads(config_json)
            except json.JSONDecodeError:
                print("Warning: Failed to parse CONFIG_JSON environment variable")

        # Try to load config file if environment variable not available
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        # Try example config
        example_path = "config.json.example"
        if os.path.exists(example_path):
            print(f"Warning: Using {example_path}. Please create {self.config_path}")
            with open(example_path, 'r') as f:
                return json.load(f)
        
        # Use environment variables and defaults for Railway
        print("No config file found, using environment variables and defaults")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Railway deployment"""
        # Parse admin IDs from environment variable
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = []
        if admin_ids_str:
            try:
                # Support comma-separated list: "123456789,987654321"
                admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
            except ValueError:
                print("Warning: Invalid ADMIN_IDS format. Using empty list.")
        
        return {
            "admin_ids": admin_ids,
            "notification_time": os.getenv("NOTIFICATION_TIME", "10:00"),
            "response_window_hours": int(os.getenv("RESPONSE_WINDOW_HOURS", "24")),
            "database_file_path": os.getenv("DATABASE_PATH", "data/db.json"),
            "timezone": os.getenv("TIMEZONE", "UTC"),
            "default_meeting_day": os.getenv("MEETING_DAY", "Wednesday"),
            "notification_day": os.getenv("NOTIFICATION_DAY", "Thursday")
        }
    
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