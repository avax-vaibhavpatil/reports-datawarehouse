#!/usr/bin/env python3
"""
Test PostgreSQL connection and verify schema setup
"""

import psycopg2
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'datawarehouse',
    'user': 'reporting_user',
    'password': 'root',
    'port': 5432
}

def test_connection():
    """Test basic PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL Connection: SUCCESS")
        print(f"📊 Version: {version}")
        
        return conn, cursor
        
    except Exception as e:
        print(f"❌ PostgreSQL Connection: FAILED")
        print(f"Error: {e}")
        return None, None

def test_schemas(cursor):
    """Test if all schemas exist"""
    try:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('raw_data', 'processed_data', 'reports', 'metadata')
            ORDER BY schema_name;
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        expected_schemas = ['metadata', 'processed_data', 'raw_data', 'reports']
        
        print(f"\n📁 Schema Verification:")
        for schema in expected_schemas:
            if schema in schemas:
                print(f"  ✅ {schema}")
            else:
                print(f"  ❌ {schema} - MISSING")
        
        return len(schemas) == len(expected_schemas)
        
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

def test_metadata_tables(cursor):
    """Test if metadata tables exist and are accessible"""
    try:
        # Test query_history table
        cursor.execute("""
            SELECT COUNT(*) FROM metadata.query_history;
        """)
        query_count = cursor.fetchone()[0]
        print(f"  ✅ metadata.query_history - {query_count} records")
        
        # Test table_info table
        cursor.execute("""
            SELECT COUNT(*) FROM metadata.table_info;
        """)
        table_count = cursor.fetchone()[0]
        print(f"  ✅ metadata.table_info - {table_count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata tables test failed: {e}")
        return False

def test_insert_sample_data(cursor, conn):
    """Test inserting sample data"""
    try:
        # Insert sample query history
        cursor.execute("""
            INSERT INTO metadata.query_history 
            (original_query, execution_time_ms, source_tables, result_table_name, result_row_count, status)
            VALUES 
            (%s, %s, %s, %s, %s, %s)
        """, (
            "SELECT * FROM test_table",
            1500,
            ['ledger', 'ledger_detail'],
            'processed_data.test_result_20241217',
            4530822,
            'success'
        ))
        
        # Insert sample table info
        cursor.execute("""
            INSERT INTO metadata.table_info 
            (schema_name, table_name, row_count, column_count, description)
            VALUES 
            (%s, %s, %s, %s, %s)
        """, (
            'processed_data',
            'test_result_20241217',
            4530822,
            10,
            'Test query result from ledger JOIN'
        ))
        
        conn.commit()
        print(f"✅ Sample data insertion: SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ Sample data insertion failed: {e}")
        conn.rollback()
        return False

def main():
    """Main test function"""
    print("🐘 PostgreSQL Connection Test")
    print("=" * 50)
    
    # Test connection
    conn, cursor = test_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Test schemas
        print(f"\n📁 Testing Schemas...")
        schema_ok = test_schemas(cursor)
        
        # Test metadata tables
        print(f"\n📊 Testing Metadata Tables...")
        tables_ok = test_metadata_tables(cursor)
        
        # Test data insertion
        print(f"\n💾 Testing Data Insertion...")
        insert_ok = test_insert_sample_data(cursor, conn)
        
        # Summary
        print(f"\n📋 Test Summary:")
        print(f"  Connection: {'✅ PASS' if conn else '❌ FAIL'}")
        print(f"  Schemas: {'✅ PASS' if schema_ok else '❌ FAIL'}")
        print(f"  Tables: {'✅ PASS' if tables_ok else '❌ FAIL'}")
        print(f"  Data Insert: {'✅ PASS' if insert_ok else '❌ FAIL'}")
        
        if all([conn, schema_ok, tables_ok, insert_ok]):
            print(f"\n🎉 All tests PASSED! PostgreSQL is ready for the data pipeline!")
        else:
            print(f"\n⚠️ Some tests FAILED. Please check the configuration.")
            
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print(f"\n🔌 Connection closed.")

if __name__ == "__main__":
    main() 