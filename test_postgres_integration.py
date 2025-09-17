#!/usr/bin/env python3
"""
Test PostgreSQL Integration for Save as Table Feature
"""

import sys
import os
sys.path.append('app')

from services.sql_query_service import SQLQueryService
from database import db_manager
import json

def test_postgres_integration():
    """Test the PostgreSQL integration"""
    print("🧪 Testing PostgreSQL Integration")
    print("=" * 50)
    
    try:
        # Test database connection
        print("1. Testing database connection...")
        with db_manager.get_connection() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Test metadata table
        print("\n2. Testing metadata table...")
        db_manager.create_metadata_table()
        print("✅ Metadata table ready")
        
        # Test table existence check
        print("\n3. Testing table existence check...")
        exists = db_manager.table_exists("test_table")
        print(f"✅ Table existence check works: {exists}")
        
        # Test SQL Query Service
        print("\n4. Testing SQL Query Service...")
        service = SQLQueryService()
        
        # Sample data to save
        sample_data = [
            {"name": "John Doe", "age": 30, "city": "New York", "salary": 75000.50},
            {"name": "Jane Smith", "age": 25, "city": "Los Angeles", "salary": 65000.00},
            {"name": "Bob Johnson", "age": 35, "city": "Chicago", "salary": 80000.75}
        ]
        
        sample_columns = ["name", "age", "city", "salary"]
        sample_sql = "SELECT name, age, city, salary FROM employees WHERE age > 20"
        
        print(f"📊 Sample data: {len(sample_data)} rows")
        print(f"📋 Columns: {sample_columns}")
        print(f"🔍 SQL: {sample_sql}")
        
        # Test saving table
        print("\n5. Testing save as table...")
        result = service.save_query_results_as_table(
            table_name="test_employees",
            data=sample_data,
            columns=sample_columns,
            sql_query=sample_sql
        )
        
        if result["success"]:
            print(f"✅ Table saved successfully: {result['message']}")
            
            # Test if table exists now
            exists = db_manager.table_exists("test_employees")
            print(f"✅ Table exists in database: {exists}")
            
            # Get table info
            table_info = db_manager.get_table_info("test_employees")
            print(f"📊 Table info: {json.dumps(table_info, indent=2)}")
            
        else:
            print(f"❌ Failed to save table: {result['message']}")
            return False
        
        print("\n🎉 PostgreSQL integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_postgres_integration()
    if success:
        print("\n✅ All tests passed! Your PostgreSQL integration is working.")
    else:
        print("\n❌ Tests failed. Please check your PostgreSQL setup.")