#!/usr/bin/env python3
"""
Database Setup Script for Excel Generator Data Warehouse

This script sets up the PostgreSQL database and required schemas
for the data warehouse functionality.
"""

import psycopg2
import os
import sys
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'datawarehouse',
    'user': 'postgres',  # Use postgres user for setup
    'password': 'root'   # Change this to your postgres password
}

def create_database():
    """Create the main database if it doesn't exist"""
    try:
        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database: {DB_CONFIG['database']}")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print("✅ Database created successfully")
        else:
            print(f"✅ Database {DB_CONFIG['database']} already exists")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def create_schemas():
    """Create required schemas in the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        schemas = [
            'processed_data',  # For query results
            'raw_data',        # For original uploaded data
            'reports',         # For business reports
            'temp'            # For temporary tables
        ]
        
        for schema in schemas:
            print(f"Creating schema: {schema}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            print(f"✅ Schema {schema} created")
        
        cursor.close()
        conn.close()
        print("✅ All schemas created successfully")
        
    except psycopg2.Error as e:
        print(f"❌ Error creating schemas: {e}")
        return False
    
    return True

def create_user():
    """Create the reporting user for the application"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create user if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ('reporting_user',))
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating reporting user...")
            cursor.execute("CREATE USER reporting_user WITH PASSWORD 'root'")
            print("✅ User created successfully")
        else:
            print("✅ User reporting_user already exists")
        
        # Grant permissions
        print("Granting permissions...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE datawarehouse TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA processed_data TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA raw_data TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA reports TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA temp TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA processed_data TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw_data TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA reports TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA temp TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA processed_data TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw_data TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA reports TO reporting_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA temp TO reporting_user")
        print("✅ Permissions granted successfully")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating user: {e}")
        return False
    
    return True

def test_connection():
    """Test the database connection with the reporting user"""
    try:
        test_config = DB_CONFIG.copy()
        test_config['user'] = 'reporting_user'
        test_config['password'] = 'root'
        
        conn = psycopg2.connect(**test_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT current_database(), current_user, version()")
        result = cursor.fetchone()
        
        print(f"✅ Connection test successful!")
        print(f"   Database: {result[0]}")
        print(f"   User: {result[1]}")
        print(f"   PostgreSQL Version: {result[2].split(',')[0]}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up PostgreSQL Database for Excel Generator Data Warehouse")
    print("=" * 70)
    
    # Check if PostgreSQL is running
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.close()
        print("✅ PostgreSQL is running")
    except psycopg2.Error as e:
        print(f"❌ Cannot connect to PostgreSQL: {e}")
        print("Please ensure PostgreSQL is installed and running")
        print("Default connection: postgres@localhost:5432")
        sys.exit(1)
    
    # Run setup steps
    steps = [
        ("Creating database", create_database),
        ("Creating schemas", create_schemas),
        ("Creating user", create_user),
        ("Testing connection", test_connection)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Setup failed at step: {step_name}")
            sys.exit(1)
    
    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Install Python dependencies: pip install -r requirements.txt")
    print("2. Start the backend: python -m app.main")
    print("3. Start the frontend: cd frontend && npm start")
    print("4. Test the data warehouse flow!")

if __name__ == "__main__":
    main()