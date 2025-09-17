#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Data Warehouse
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with PostgreSQL configuration"""
    env_content = """# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=datawarehouse
DB_USER=postgres
DB_PASSWORD=your_password_here

# Optional: Database URL (alternative to individual settings)
# DATABASE_URL=postgresql://postgres:password@localhost:5432/datawarehouse
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists. Please update it manually with your PostgreSQL credentials.")
        return False
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with PostgreSQL configuration")
    print("📝 Please update the DB_PASSWORD with your actual PostgreSQL password")
    return True

def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        sys.path.append('app')
        from database import db_manager
        
        print("🔍 Testing PostgreSQL connection...")
        
        # Test connection
        with db_manager.get_connection() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
            
        # Test metadata table creation
        db_manager.create_metadata_table()
        print("✅ Metadata table created/verified")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n🔧 Please check:")
        print("1. PostgreSQL is running")
        print("2. Database 'datawarehouse' exists")
        print("3. User has proper permissions")
        print("4. .env file has correct credentials")
        return False

def main():
    """Main setup function"""
    print("🚀 PostgreSQL Setup for Data Warehouse")
    print("=" * 50)
    
    # Create .env file
    if create_env_file():
        print("\n📝 Next steps:")
        print("1. Update .env file with your PostgreSQL password")
        print("2. Ensure PostgreSQL is running")
        print("3. Create database 'datawarehouse' if it doesn't exist")
        print("4. Run this script again to test connection")
    else:
        print("\n🔍 Testing existing PostgreSQL connection...")
        if test_postgres_connection():
            print("\n🎉 PostgreSQL setup is complete!")
            print("✅ Your application is ready to use PostgreSQL")
        else:
            print("\n❌ Setup incomplete. Please fix the issues above.")

if __name__ == "__main__":
    main()