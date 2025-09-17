import os
from dotenv import load_dotenv
from typing import Optional

class ConfigService:
    """Service for managing application configuration from environment variables"""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
    
    # PostgreSQL Configuration
    @property
    def postgres_host(self) -> str:
        return os.getenv('POSTGRES_HOST', 'localhost')
    
    @property
    def postgres_port(self) -> int:
        return int(os.getenv('POSTGRES_PORT', '5432'))
    
    @property
    def postgres_database(self) -> str:
        return os.getenv('POSTGRES_DATABASE', 'datawarehouse')
    
    @property
    def postgres_user(self) -> str:
        return os.getenv('POSTGRES_USER', 'reporting_user')
    
    @property
    def postgres_password(self) -> str:
        return os.getenv('POSTGRES_PASSWORD', 'root')
    
    @property
    def postgres_config(self) -> dict:
        """Get complete PostgreSQL configuration dictionary"""
        return {
            'host': self.postgres_host,
            'port': self.postgres_port,
            'database': self.postgres_database,
            'user': self.postgres_user,
            'password': self.postgres_password
        }
    
    # SQLite Configuration
    @property
    def sqlite_db_path(self) -> str:
        return os.getenv('SQLITE_DB_PATH', 'data/excel_data.db')
    
    # Application Configuration
    @property
    def app_env(self) -> str:
        return os.getenv('APP_ENV', 'development')
    
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    # Pipeline Configuration
    @property
    def pipeline_chunk_size(self) -> int:
        return int(os.getenv('PIPELINE_CHUNK_SIZE', '10000'))
    
    @property
    def pipeline_max_retries(self) -> int:
        return int(os.getenv('PIPELINE_MAX_RETRIES', '3'))
    
    @property
    def pipeline_timeout_seconds(self) -> int:
        return int(os.getenv('PIPELINE_TIMEOUT_SECONDS', '300'))

# Create global config instance
config = ConfigService() 