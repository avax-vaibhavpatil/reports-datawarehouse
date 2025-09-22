#!/usr/bin/env python3
"""
Test Script for Data Warehouse Flow

This script tests the complete data warehouse flow:
1. Upload files
2. Execute queries
3. Generate schema preview
4. Create tables in PostgreSQL
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:4200"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/files/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def test_database_connection():
    """Test PostgreSQL database connection"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/schema-editor/health", timeout=5)
        if response.status_code == 200:
            print("✅ Database connection is working")
            return True
        else:
            print(f"❌ Database connection failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot test database connection: {e}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    try:
        # Create a sample CSV file for testing
        sample_data = """id,name,age,city
1,John,25,New York
2,Jane,30,Los Angeles
3,Bob,35,Chicago
4,Alice,28,Boston
5,Charlie,32,Seattle"""
        
        sample_file = Path("test_sample.csv")
        sample_file.write_text(sample_data)
        
        # Upload the file
        with open(sample_file, 'rb') as f:
            files = {'files': ('test_sample.csv', f, 'text/csv')}
            response = requests.post(f"{BACKEND_URL}/api/files/upload", files=files)
        
        # Clean up
        sample_file.unlink()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('total_uploaded', 0) > 0:
                print("✅ File upload is working")
                return True
            else:
                print("❌ File upload failed: No files uploaded")
                return False
        else:
            print(f"❌ File upload failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False

def test_sql_query():
    """Test SQL query execution"""
    try:
        # Get available tables
        response = requests.get(f"{BACKEND_URL}/api/sql-query/tables")
        if response.status_code != 200:
            print("❌ Cannot get available tables")
            return False
        
        tables = response.json().get('tables', [])
        if not tables:
            print("❌ No tables available for query testing")
            return False
        
        # Create a simple query
        query_config = {
            "tables": [{"name": tables[0]['name'], "columns": tables[0]['columns'][:2]}],
            "joins": [],
            "where_conditions": [],
            "group_by": [],
            "order_by": [],
            "limit": 10
        }
        
        # Execute query
        response = requests.post(f"{BACKEND_URL}/api/sql-query/preview", 
                               json={"query_config": query_config, "sample_size": 10})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                print("✅ SQL query execution is working")
                return True
            else:
                print(f"❌ SQL query execution failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ SQL query execution failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SQL query test failed: {e}")
        return False

def test_schema_preview():
    """Test schema preview generation"""
    try:
        # First, get a simple query result
        response = requests.get(f"{BACKEND_URL}/api/sql-query/tables")
        tables = response.json().get('tables', [])
        
        if not tables:
            print("❌ No tables available for schema preview testing")
            return False
        
        # Create a simple query
        query_config = {
            "tables": [{"name": tables[0]['name'], "columns": tables[0]['columns'][:2]}],
            "joins": [],
            "where_conditions": [],
            "group_by": [],
            "order_by": [],
            "limit": 10
        }
        
        # Generate SQL
        response = requests.post(f"{BACKEND_URL}/api/sql-query/generate", json=query_config)
        if response.status_code != 200:
            print("❌ Cannot generate SQL query")
            return False
        
        sql_query = response.json().get('sql', '')
        if not sql_query:
            print("❌ Generated SQL query is empty")
            return False
        
        # Test schema preview
        preview_request = {
            "query_sql": sql_query,
            "db_schema": "processed_data",
            "user_table_name": "test_table",
            "limit": 10
        }
        
        response = requests.post(f"{BACKEND_URL}/api/schema-editor/preview", json=preview_request)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                print("✅ Schema preview generation is working")
                return True
            else:
                print(f"❌ Schema preview failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Schema preview failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Schema preview test failed: {e}")
        return False

def test_table_creation():
    """Test table creation in PostgreSQL"""
    try:
        # First, get a simple query result
        response = requests.get(f"{BACKEND_URL}/api/sql-query/tables")
        tables = response.json().get('tables', [])
        
        if not tables:
            print("❌ No tables available for table creation testing")
            return False
        
        # Create a simple query
        query_config = {
            "tables": [{"name": tables[0]['name'], "columns": tables[0]['columns'][:2]}],
            "joins": [],
            "where_conditions": [],
            "group_by": [],
            "order_by": [],
            "limit": 5
        }
        
        # Generate SQL
        response = requests.post(f"{BACKEND_URL}/api/sql-query/generate", json=query_config)
        sql_query = response.json().get('sql', '')
        
        # Test table creation
        create_request = {
            "query_sql": sql_query,
            "db_schema": "processed_data",
            "user_table_name": f"test_table_{int(time.time())}",
            "column_corrections": {},
            "limit": 5
        }
        
        response = requests.post(f"{BACKEND_URL}/api/schema-editor/create-table", json=create_request)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                print("✅ Table creation is working")
                return True
            else:
                print(f"❌ Table creation failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Table creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Table creation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Data Warehouse Flow")
    print("=" * 50)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Database Connection", test_database_connection),
        ("File Upload", test_file_upload),
        ("SQL Query Execution", test_sql_query),
        ("Schema Preview", test_schema_preview),
        ("Table Creation", test_table_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Data warehouse flow is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running: sudo systemctl start postgresql")
        print("2. Run database setup: python3 setup_database.py")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Start backend: python -m app.main")
        print("5. Check logs for detailed error messages")

if __name__ == "__main__":
    main()