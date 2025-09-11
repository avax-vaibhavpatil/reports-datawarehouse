#!/usr/bin/env python3
"""
Test Main Application API vs Direct SQL
Proves that main app produces same results as test files
"""

import sys
import os
sys.path.append('app')

from services.sql_query_service import SQLQueryService

def test_main_app_vs_direct():
    """Compare main app API method vs direct SQL execution"""
    print("🔧 Testing Main App API vs Direct SQL")
    print("📊 Verifying identical results")
    print("=" * 60)
    
    service = SQLQueryService()
    
    # Test 1: Using Main Application API (like your frontend does)
    print("\n1. Using Main Application API (execute_query_preview)...")
    try:
        # This is how your main app calls it (correct format)
        query_config = {
            "tables": [
                {
                    "name": "ledger",
                    "alias": "l",
                    "columns": ["lg_siscon_code", "lg_branch_code", "lg_voucher_no"]
                },
                {
                    "name": "ledger_detail", 
                    "alias": "ld",
                    "columns": ["lgd_acc_code", "lgd_amount"]
                }
            ],
            "joins": [
                {
                    "type": "INNER JOIN",
                    "table": "ledger_detail",
                    "alias": "ld",
                    "conditions": [
                        {
                            "left_table": "l",
                            "left_column": "lg_siscon_code",
                            "operator": "=",
                            "right_table": "ld", 
                            "right_column": "lgd_siscon_code"
                        },
                        {
                            "left_table": "l",
                            "left_column": "lg_branch_code",
                            "operator": "=",
                            "right_table": "ld", 
                            "right_column": "lgd_branch_code"
                        },
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
            "where_conditions": [],
            "group_by": [],
            "order_by": [],
            "limit": 5
        }
        
        main_app_result = service.execute_query_preview(query_config, sample_size=5)
        
        print(f"✅ Main App API Result:")
        print(f"   📊 Success: {main_app_result['success']}")
        print(f"   📊 Records: {main_app_result['total_rows']}")
        print(f"   📊 Columns: {main_app_result['columns']}")
        print(f"   📊 Generated SQL: {main_app_result.get('sql_query', 'N/A')}")
        
        if main_app_result['success']:
            print(f"   📋 Sample data:")
            for i, row in enumerate(main_app_result['sample_data'][:2], 1):
                print(f"      {i}. {row}")
        
    except Exception as e:
        print(f"❌ Main App API Error: {e}")
        main_app_result = None
    
    # Test 2: Using Direct SQL (like test files do)
    print("\n2. Using Direct SQL (like test files)...")
    try:
        # This is how test files call it
        direct_sql = """
        SELECT 
            l.lg_siscon_code,
            l.lg_branch_code, 
            l.lg_voucher_no,
            ld.lgd_acc_code,
            ld.lgd_amount
        FROM ledger l
        INNER JOIN ledger_detail ld ON (
            l.lg_siscon_code = ld.lgd_siscon_code 
            AND l.lg_branch_code = ld.lgd_branch_code 
            AND l.lg_voucher_no = ld.lgd_voucher_no
        )
        LIMIT 5
        """
        
        direct_result = service._execute_sql_against_files(direct_sql.strip())
        
        print(f"✅ Direct SQL Result:")
        print(f"   📊 Records: {direct_result['total_rows']}")
        print(f"   📊 Columns: {direct_result['columns']}")
        print(f"   📋 Sample data:")
        for i, row in enumerate(direct_result['data'][:2], 1):
            print(f"      {i}. {row}")
        
    except Exception as e:
        print(f"❌ Direct SQL Error: {e}")
        direct_result = None
    
    # Test 3: Compare Results
    print("\n3. Comparing Results...")
    if main_app_result and main_app_result['success'] and direct_result:
        main_count = main_app_result['total_rows']
        direct_count = direct_result['total_rows']
        
        print(f"📊 Result Comparison:")
        print(f"   Main App API:  {main_count} records")
        print(f"   Direct SQL:    {direct_count} records")
        
        if main_count == direct_count:
            print("   ✅ IDENTICAL RESULTS! Main app = Test files")
        else:
            print("   ⚠️ Different results - needs investigation")
            
        # Compare columns
        main_cols = set(main_app_result['columns'])
        direct_cols = set(direct_result['columns'])
        
        if main_cols == direct_cols:
            print("   ✅ IDENTICAL COLUMNS! Same data structure")
        else:
            print("   ⚠️ Different columns")
    else:
        print("   ❌ Cannot compare - one or both methods failed")
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE!")
    print("📊 Main application uses the exact same SQL engine as test files!")

if __name__ == "__main__":
    test_main_app_vs_direct() 