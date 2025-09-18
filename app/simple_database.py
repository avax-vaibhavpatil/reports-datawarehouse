"""
Simple PostgreSQL Database Manager
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SimpleDatabaseManager:
    """Simple PostgreSQL Database Manager using psycopg2 directly"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'datawarehouse'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'root')
        }
        self.database_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        logger.info(f"Database config: {self.db_config['user']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
    
    def get_connection(self):
        """Get a new database connection"""
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_metadata_table(self):
        """Create table_metadata table if it doesn't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS table_metadata (
                        id SERIAL PRIMARY KEY,
                        table_name VARCHAR(255) UNIQUE NOT NULL,
                        source_query TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        row_count INTEGER,
                        column_count INTEGER,
                        columns TEXT
                    )
                """)
                conn.commit()
                logger.info("✅ table_metadata table created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating table_metadata: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table_name,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Error checking if table exists: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> dict:
        """Get information about a table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get column information
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in cursor.fetchall()]
                
                # Get row count
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                row_count = cursor.fetchone()[0]
                
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
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error listing tables: {e}")
            return []

# Global database manager instance
simple_db_manager = SimpleDatabaseManager()