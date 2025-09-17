#!/usr/bin/env python3
"""
Test Database Connection Script
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append('app')

def test_database_connection():
    """Test the database connection"""
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    try:
        # Import after adding to path
        from database import db_manager
        
        print("1. Testing database connection...")
        with db_manager.get_connection() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        print("\n2. Testing metadata table creation...")
        db_manager.create_metadata_table()
        print("✅ Metadata table created/verified")
        
        print("\n3. Testing table operations...")
        # Test if we can create a simple table
        test_table_name = "connection_test"
        with db_manager.get_connection() as conn:
            # Drop table if exists
            conn.execute(f"DROP TABLE IF EXISTS {test_table_name}")
            
            # Create test table
            conn.execute(f"""
                CREATE TABLE {test_table_name} (
                    id SERIAL PRIMARY KEY,
                    test_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            conn.execute(f"""
                INSERT INTO {test_table_name} (test_message) 
                VALUES ('Database connection successful!')
            """)
            
            # Query test data
            result = conn.execute(f"SELECT * FROM {test_table_name}")
            data = result.fetchall()
            print(f"✅ Test table created and data inserted: {data}")
            
            # Clean up
            conn.execute(f"DROP TABLE {test_table_name}")
            print("✅ Test table cleaned up")
        
        print("\n🎉 Database connection test successful!")
        print("✅ Your PostgreSQL database is properly configured!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Please check:")
        print("1. PostgreSQL is running")
        print("2. Database 'datawarehouse' exists")
        print("3. User 'postgres' has proper permissions")
        print("4. .env file has correct credentials")
        print("5. Password is correct")
        return False

def show_configuration_help():
    """Show configuration help"""
    print("\n📋 Configuration Help")
    print("=" * 40)
    print("1. Make sure PostgreSQL is installed and running")
    print("2. Create database 'datawarehouse':")
    print("   sudo -u postgres createdb datawarehouse")
    print("3. Update .env file with your credentials")
    print("4. Run this test script again")

if __name__ == "__main__":
    print("🚀 Database Connection Test")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Please create .env file with your database credentials")
        show_configuration_help()
        sys.exit(1)
    
    # Test connection
    if test_database_connection():
        print("\n✅ All tests passed! Your database is ready to use.")
    else:
        print("\n❌ Tests failed. Please fix the issues above.")
        show_configuration_help()