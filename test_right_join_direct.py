#!/usr/bin/env python3
"""
Direct test of RIGHT JOIN optimization without the web service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_query_service import SQLQueryService
import time

def test_right_join_optimization():
    """Test RIGHT JOIN optimization directly"""
    print("🧪 Testing RIGHT JOIN optimization directly...")
    
    service = SQLQueryService()
    
    # Test the expensive join detection
    test_query = """
    SELECT ledger.lg_branch_code, ledger.lg_voucher_date, ledger.lg_voucher_type, 
           ledger_detail.lgd_refvoucher_no, ledger_detail.lgd_acc_code, ledger_detail.lgd_amount
    FROM ledger
    RIGHT JOIN ledger_detail ON ledger.lg_voucher_no = ledger_detail.lgd_voucher_no 
        AND ledger.lg_siscon_code = ledger_detail.lgd_siscon_code 
        AND ledger.lg_branch_code = ledger_detail.lgd_branch_code
    LIMIT 1000
    """
    
    print("📝 Test query:")
    print(test_query.strip())
    
    # Test detection
    is_expensive = service._is_expensive_join(test_query)
    print(f"🔍 Expensive join detection result: {is_expensive}")
    
    if is_expensive:
        print("✅ RIGHT JOIN detected correctly!")
        
        # Test the optimization
        optimized_query = service.optimize_query_for_joins(test_query)
        print(f"🔧 Optimized query:")
        print(optimized_query.strip())
        
        # Test execution with timeout
        print("\n🚀 Testing query execution...")
        start_time = time.time()
        
        try:
            result = service.execute_raw_sql(test_query, limit=100)
            execution_time = time.time() - start_time
            
            print(f"✅ Query executed successfully!")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Rows returned: {len(result.get('data', []))}")
            print(f"   Total rows: {result.get('total_rows', 'N/A')}")
            
            if result.get('warning'):
                print(f"   ⚠️  Warning: {result['warning']}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Query failed after {execution_time:.2f}s: {e}")
            
    else:
        print("❌ RIGHT JOIN not detected!")

if __name__ == "__main__":
    test_right_join_optimization()