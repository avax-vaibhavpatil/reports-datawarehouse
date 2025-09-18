#!/usr/bin/env python3
"""
Simple PostgreSQL Connection Test
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def test_simple_connection():
    """Test simple PostgreSQL connection"""
    print("🔍 Simple PostgreSQL Connection Test")
    print("=" * 50)
    
    try:
        # Get database credentials from .env
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'datawarehouse'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'root')
        }
        
        print(f"Connecting to: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Test direct psycopg2 connection
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        print("✅ Direct psycopg2 connection successful!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL version: {version}")
        
        # Test our database
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        print(f"✅ Connected to database: {db_name}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 All tests passed! The issue is in our SQLAlchemy setup.")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_simple_connection()