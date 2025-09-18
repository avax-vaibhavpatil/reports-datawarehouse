#!/usr/bin/env python3
"""
Test Simple Database Connection
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append('app')

def test_simple_database():
    """Test the simple database connection"""
    print("🔍 Testing Simple Database Connection")
    print("=" * 50)
    
    try:
        # Import after adding to path
        from simple_database import simple_db_manager
        
        print("1. Testing database connection...")
        with simple_db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        print("\n2. Testing metadata table creation...")
        simple_db_manager.create_metadata_table()
        print("✅ Metadata table created/verified")
        
        print("\n3. Testing table operations...")
        # Test if we can create a simple table
        test_table_name = "connection_test"
        with simple_db_manager.get_connection() as conn:
            cursor = conn.cursor()
            # Drop table if exists
            cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
            
            # Create test table
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id SERIAL PRIMARY KEY,
                    test_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            cursor.execute(f"""
                INSERT INTO {test_table_name} (test_message) 
                VALUES ('Database connection successful!')
            """)
            
            # Query test data
            cursor.execute(f"SELECT * FROM {test_table_name}")
            data = cursor.fetchall()
            print(f"✅ Test table created and data inserted: {data}")
            
            # Clean up
            cursor.execute(f"DROP TABLE {test_table_name}")
            print("✅ Test table cleaned up")
        
        print("\n🎉 Simple database connection test successful!")
        print("✅ Your PostgreSQL database is properly configured!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple Database Connection Test")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        sys.exit(1)
    
    # Test connection
    if test_simple_database():
        print("\n✅ All tests passed! Your database is ready to use.")
    else:
        print("\n❌ Tests failed. Please check the error above.")