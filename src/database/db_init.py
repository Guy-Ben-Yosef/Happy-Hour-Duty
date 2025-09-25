from src.database.db_manager import DatabaseManager
from src.config import ConfigManager

def initialize_database():
    """Initialize the database with configuration"""
    config_manager = ConfigManager()
    config = config_manager.get_bot_config()
    
    db_manager = DatabaseManager(config.database_file_path)
    print(f"Database initialized at: {config.database_file_path}")
    return db_manager

if __name__ == "__main__":
    initialize_database()