#!/usr/bin/env python3
"""
Composite Key JOIN Test - Using multiple columns for accurate relationships
siscon_code + branch_code + voucher_no = Composite Primary Key
"""

import sys
import os
sys.path.append('app')

from services.sql_query_service import SQLQueryService

def test_composite_key_join():
    """Test JOIN using composite key (siscon_code + branch_code + voucher_no)"""
    print("🔧 Composite Key JOIN Test - Financial Data")
    print("📊 Using siscon_code + branch_code + voucher_no")
    print("=" * 70)
    
    service = SQLQueryService()
    
    # First, let's examine the key fields in both tables
    print("\n1. Examining composite key fields...")
    try:
        # Check ledger table key fields
        ledger_keys = service._execute_sql_against_files("""
            SELECT 
                lg_siscon_code, 
                lg_branch_code, 
                lg_voucher_no,
                lg_voucher_date,
                lg_narration
            FROM ledger 
            LIMIT 3
        """)
        
        print("✅ Ledger table composite keys:")
        for i, row in enumerate(ledger_keys['data'], 1):
            print(f"   {i}. Siscon: {row['lg_siscon_code']}, Branch: {row['lg_branch_code']}, Voucher: {row['lg_voucher_no']}")
        
        # Check ledger_detail table key fields
        detail_keys = service._execute_sql_against_files("""
            SELECT 
                lgd_siscon_code, 
                lgd_branch_code, 
                lgd_voucher_no,
                lgd_acc_code,
                lgd_amount
            FROM ledger_detail 
            LIMIT 3
        """)
        
        print("\n✅ Ledger Detail table composite keys:")
        for i, row in enumerate(detail_keys['data'], 1):
            print(f"   {i}. Siscon: {row['lgd_siscon_code']}, Branch: {row['lgd_branch_code']}, Voucher: {row['lgd_voucher_no']}")
            
    except Exception as e:
        print(f"❌ Key examination error: {e}")
    
    # Test 2: Composite Key INNER JOIN
    print("\n2. INNER JOIN using Composite Key (siscon + branch + voucher)")
    print("-" * 60)
    try:
        composite_join_sql = """
        SELECT 
            l.lg_siscon_code,
            l.lg_branch_code, 
            l.lg_voucher_no,
            l.lg_voucher_date,
            l.lg_narration,
            ld.lgd_acc_code,
            ld.lgd_amount,
            ld.lgd_remarks
        FROM ledger l
        INNER JOIN ledger_detail ld ON (
            l.lg_siscon_code = ld.lgd_siscon_code 
            AND l.lg_branch_code = ld.lgd_branch_code 
            AND l.lg_voucher_no = ld.lgd_voucher_no
        )
        LIMIT 5
        """
        
        result = service._execute_sql_against_files(composite_join_sql.strip())
        print(f"✅ Composite Key JOIN successful!")
        print(f"📊 Found {result['total_rows']} matching records")
        print(f"🔍 Columns: {result['columns']}")
        
        print("\n📋 Sample Records with Composite Key Match:")
        for i, row in enumerate(result['data'], 1):
            print(f"   {i}. Key: ({row['lg_siscon_code']}, {row['lg_branch_code']}, {row['lg_voucher_no']})")
            print(f"      Date: {row['lg_voucher_date']}")
            print(f"      Account: {row['lgd_acc_code']}")
            print(f"      Amount: {row['lgd_amount']}")
            print(f"      Narration: {row['lg_narration'][:60]}...")
            print()
            
    except Exception as e:
        print(f"❌ Composite JOIN Error: {e}")
    
    # Test 3: Count comparison - Single key vs Composite key
    print("\n3. Comparison: Single Key vs Composite Key JOIN results")
    print("-" * 60)
    try:
        # Single key JOIN count
        single_key_count = service._execute_sql_against_files("""
            SELECT COUNT(*) as count
            FROM ledger l
            INNER JOIN ledger_detail ld ON l.lg_voucher_no = ld.lgd_voucher_no
        """)
        
        # Composite key JOIN count
        composite_key_count = service._execute_sql_against_files("""
            SELECT COUNT(*) as count
            FROM ledger l
            INNER JOIN ledger_detail ld ON (
                l.lg_siscon_code = ld.lgd_siscon_code 
                AND l.lg_branch_code = ld.lgd_branch_code 
                AND l.lg_voucher_no = ld.lgd_voucher_no
            )
        """)
        
        single_count = single_key_count['data'][0]['count']
        composite_count = composite_key_count['data'][0]['count']
        
        print(f"📊 JOIN Results Comparison:")
        print(f"   Single Key (voucher_no only):     {single_count:,} records")
        print(f"   Composite Key (siscon+branch+voucher): {composite_count:,} records")
        print(f"   Difference: {single_count - composite_count:,} records")
        
        if composite_count < single_count:
            print("   ✅ Composite key is more accurate (eliminates duplicates)")
        elif composite_count == single_count:
            print("   ℹ️ Both keys produce same results")
        else:
            print("   ⚠️ Composite key found more matches")
            
    except Exception as e:
        print(f"❌ Comparison Error: {e}")
    
    # Test 4: Business Intelligence with Composite Key
    print("\n4. Business Intelligence: Daily summary with Composite Key")
    print("-" * 60)
    try:
        business_sql = """
        SELECT 
            l.lg_voucher_date,
            l.lg_siscon_code,
            l.lg_branch_code,
            COUNT(DISTINCT l.lg_voucher_no) as unique_vouchers,
            COUNT(*) as total_entries,
            SUM(ld.lgd_amount) as total_amount,
            AVG(ld.lgd_amount) as avg_amount
        FROM ledger l
        INNER JOIN ledger_detail ld ON (
            l.lg_siscon_code = ld.lgd_siscon_code 
            AND l.lg_branch_code = ld.lgd_branch_code 
            AND l.lg_voucher_no = ld.lgd_voucher_no
        )
        WHERE l.lg_voucher_date >= '2025-08-01'
        GROUP BY l.lg_voucher_date, l.lg_siscon_code, l.lg_branch_code
        ORDER BY l.lg_voucher_date DESC, total_amount DESC
        LIMIT 10
        """
        
        result = service._execute_sql_against_files(business_sql.strip())
        print(f"✅ Business Intelligence query successful!")
        print(f"📊 Branch-wise daily summary:")
        print(f"{'Date':<12} {'Siscon':<8} {'Branch':<8} {'Vouchers':<10} {'Entries':<8} {'Total Amount':<15} {'Avg Amount':<12}")
        print("-" * 85)
        
        for row in result['data']:
            print(f"{row['lg_voucher_date']:<12} {row['lg_siscon_code']:<8} {row['lg_branch_code']:<8} {row['unique_vouchers']:<10} {row['total_entries']:<8} {row['total_amount']:<15.2f} {row['avg_amount']:<12.2f}")
            
    except Exception as e:
        print(f"❌ Business Intelligence Error: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 COMPOSITE KEY JOIN ANALYSIS COMPLETE!")
    print("🔑 More accurate relationships using multiple key fields!")
    print("📊 Ready for complex multi-branch, multi-location analysis!")

if __name__ == "__main__":
    test_composite_key_join() 