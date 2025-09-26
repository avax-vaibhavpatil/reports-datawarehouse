#!/usr/bin/env python3
"""
Test script to verify JOIN optimization improvements
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_recreate_indexes():
    """Test the recreate indexes endpoint"""
    print("🔄 Testing index recreation...")
    
    try:
        response = requests.post(f"{API_BASE}/sql-query/recreate-indexes")
        result = response.json()
        
        if result.get("success"):
            print(f"✅ {result['message']}")
            print(f"   Tables processed: {result['tables_processed']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing index recreation: {e}")

def test_right_join_query():
    """Test a RIGHT JOIN query"""
    print("\n🔄 Testing RIGHT JOIN query...")
    
    query_config = {
        "tables": [
            {
                "name": "ledger_detail",
                "alias": "ld",
                "columns": ["lgd_voucher_no", "lgd_acc_code", "lgd_amount"]
            }
        ],
        "joins": [
            {
                "type": "RIGHT JOIN",
                "table": "ledger",
                "alias": "l",
                "columns": ["lg_voucher_no", "lg_branch_code", "lg_voucher_date"],
                "conditions": [
                    {
                        "left_table": "ld",
                        "left_column": "lgd_voucher_no",
                        "operator": "=",
                        "right_table": "l",
                        "right_column": "lg_voucher_no"
                    },
                    {
                        "left_table": "ld",
                        "left_column": "lgd_siscon_code",
                        "operator": "=",
                        "right_table": "l",
                        "right_column": "lg_siscon_code"
                    },
                    {
                        "left_table": "ld",
                        "left_column": "lgd_branch_code",
                        "operator": "=",
                        "right_table": "l",
                        "right_column": "lg_branch_code"
                    }
                ]
            }
        ],
        "limit": 100
    }
    
    try:
        start_time = time.time()
        
        # Generate SQL
        response = requests.post(f"{API_BASE}/sql-query/generate", json=query_config)
        if response.status_code != 200:
            print(f"❌ SQL generation failed: {response.text}")
            return
            
        sql_result = response.json()
        print(f"📝 Generated SQL: {sql_result['sql'][:100]}...")
        
        # Execute query
        response = requests.post(f"{API_BASE}/sql-query/execute", json=query_config)
        if response.status_code != 200:
            print(f"❌ Query execution failed: {response.text}")
            return
            
        result = response.json()
        execution_time = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ RIGHT JOIN executed successfully!")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Rows returned: {len(result.get('sample_data', []))}")
            print(f"   Total rows: {result.get('total_rows', 'N/A')}")
            if result.get('warning'):
                print(f"   ⚠️  Warning: {result['warning']}")
        else:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing RIGHT JOIN: {e}")

def test_full_outer_join_query():
    """Test a FULL OUTER JOIN query"""
    print("\n🔄 Testing FULL OUTER JOIN query...")
    
    query_config = {
        "tables": [
            {
                "name": "ledger",
                "alias": "l",
                "columns": ["lg_voucher_no", "lg_branch_code", "lg_voucher_date"]
            }
        ],
        "joins": [
            {
                "type": "FULL OUTER JOIN",
                "table": "ledger_detail",
                "alias": "ld",
                "columns": ["lgd_voucher_no", "lgd_acc_code", "lgd_amount"],
                "conditions": [
                    {
                        "left_table": "l",
                        "left_column": "lg_voucher_no",
                        "operator": "=",
                        "right_table": "ld",
                        "right_column": "lgd_voucher_no"
                    }
                ]
            }
        ],
        "limit": 50
    }
    
    try:
        start_time = time.time()
        
        # Generate SQL
        response = requests.post(f"{API_BASE}/sql-query/generate", json=query_config)
        if response.status_code != 200:
            print(f"❌ SQL generation failed: {response.text}")
            return
            
        sql_result = response.json()
        print(f"📝 Generated SQL: {sql_result['sql'][:100]}...")
        
        # Execute query
        response = requests.post(f"{API_BASE}/sql-query/execute", json=query_config)
        if response.status_code != 200:
            print(f"❌ Query execution failed: {response.text}")
            return
            
        result = response.json()
        execution_time = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ FULL OUTER JOIN executed successfully!")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Rows returned: {len(result.get('sample_data', []))}")
            print(f"   Total rows: {result.get('total_rows', 'N/A')}")
            if result.get('warning'):
                print(f"   ⚠️  Warning: {result['warning']}")
        else:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing FULL OUTER JOIN: {e}")

def test_normal_join_for_comparison():
    """Test a normal LEFT JOIN for comparison"""
    print("\n🔄 Testing LEFT JOIN for comparison...")
    
    query_config = {
        "tables": [
            {
                "name": "ledger",
                "alias": "l",
                "columns": ["lg_voucher_no", "lg_branch_code", "lg_voucher_date"]
            }
        ],
        "joins": [
            {
                "type": "LEFT JOIN",
                "table": "ledger_detail",
                "alias": "ld",
                "columns": ["lgd_voucher_no", "lgd_acc_code", "lgd_amount"],
                "conditions": [
                    {
                        "left_table": "l",
                        "left_column": "lg_voucher_no",
                        "operator": "=",
                        "right_table": "ld",
                        "right_column": "lgd_voucher_no"
                    }
                ]
            }
        ],
        "limit": 100
    }
    
    try:
        start_time = time.time()
        
        # Execute query
        response = requests.post(f"{API_BASE}/sql-query/execute", json=query_config)
        if response.status_code != 200:
            print(f"❌ Query execution failed: {response.text}")
            return
            
        result = response.json()
        execution_time = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ LEFT JOIN executed successfully!")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Rows returned: {len(result.get('sample_data', []))}")
            print(f"   Total rows: {result.get('total_rows', 'N/A')}")
        else:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing LEFT JOIN: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing JOIN Optimization Solution")
    print("=" * 50)
    
    # Test index recreation
    test_recreate_indexes()
    
    # Test different JOIN types
    test_normal_join_for_comparison()
    test_right_join_query()
    test_full_outer_join_query()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")
    print("\nIf RIGHT JOIN and FULL OUTER JOIN queries now execute successfully,")
    print("the optimization solution is working correctly.")

if __name__ == "__main__":
    main()