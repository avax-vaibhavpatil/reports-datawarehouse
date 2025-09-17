"""
PostgreSQL Database Configuration and Connection Management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """PostgreSQL Database Manager for Data Warehouse"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize PostgreSQL connection"""
        try:
            # Database connection parameters
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'datawarehouse'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password')
            }
            
            # Create connection string
            connection_string = (
                f"postgresql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            )
            
            # Create engine
            self.engine = create_engine(
                connection_string,
                poolclass=NullPool,  # Use NullPool for stateless operations
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Test connection
            self._test_connection()
            
            logger.info(f"✅ Connected to PostgreSQL database: {db_config['database']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("✅ Database connection test successful")
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise
    
    def get_connection(self):
        """Get a new database connection"""
        return self.engine.connect()
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def create_metadata_table(self):
        """Create table_metadata table if it doesn't exist"""
        try:
            with self.get_connection() as conn:
                # Create table_metadata table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS table_metadata (
                        id SERIAL PRIMARY KEY,
                        table_name VARCHAR(255) UNIQUE NOT NULL,
                        source_query TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        row_count INTEGER,
                        column_count INTEGER,
                        columns TEXT
                    )
                """))
                conn.commit()
                logger.info("✅ table_metadata table created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating table_metadata: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """), {"table_name": table_name})
                return result.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Error checking if table exists: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> dict:
        """Get information about a table"""
        try:
            with self.get_connection() as conn:
                # Get column information
                columns_result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                    ORDER BY ordinal_position
                """), {"table_name": table_name})
                
                columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in columns_result]
                
                # Get row count
                count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                row_count = count_result.fetchone()[0]
                
                return {
                    "table_name": table_name,
                    "columns": columns,
                    "row_count": row_count
                }
        except Exception as e:
            logger.error(f"❌ Error getting table info: {e}")
            return {}
    
    def list_all_tables(self) -> list:
        """List all tables in the database"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"❌ Error listing tables: {e}")
            return []

# Global database manager instance
db_manager = DatabaseManager()