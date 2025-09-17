import psycopg2
import logging
from contextlib import contextmanager
from typing import Optional
from .config_service import config

class PostgreSQLService:
    """Service for managing PostgreSQL connections and operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Database configuration from environment variables
        self.db_config = config.postgres_config
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for PostgreSQL connections
        
        Logic:
        1. Create a connection to PostgreSQL
        2. Yield the connection for use
        3. Automatically close connection when done
        4. Handle any errors that occur
        
        Usage:
        with postgres_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            # Step 1: Create connection
            conn = psycopg2.connect(**self.db_config)
            self.logger.info("PostgreSQL connection established")
            
            # Step 2: Yield connection for use
            yield conn
            
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL connection error: {e}")
            if conn:
                conn.rollback()  # Rollback any failed transactions
            raise
            
        finally:
            # Step 3: Always close connection
            if conn:
                conn.close()
                self.logger.info("PostgreSQL connection closed")
    
    def test_connection(self) -> bool:
        """
        Test if PostgreSQL connection is working
        
        Logic:
        1. Try to connect to PostgreSQL
        2. Execute a simple query (SELECT 1)
        3. Return True if successful, False if failed
        
        Returns:
        bool: True if connection works, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Step 1: Execute simple test query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                # Step 2: Verify we got expected result
                if result and result[0] == 1:
                    self.logger.info("PostgreSQL connection test: SUCCESS")
                    return True
                else:
                    self.logger.error("PostgreSQL connection test: Unexpected result")
                    return False
                    
        except Exception as e:
            self.logger.error(f"PostgreSQL connection test: FAILED - {e}")
            return False 