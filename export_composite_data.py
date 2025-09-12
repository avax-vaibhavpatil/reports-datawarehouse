#!/usr/bin/env python3
"""
Export Composite Key JOIN Results to Excel
For verification against actual database
"""

import sys
import os
sys.path.append('app')

from services.sql_query_service import SQLQueryService
import pandas as pd
from datetime import datetime

def export_composite_data():
    """Export composite key JOIN results to Excel files"""
    print("🔧 Exporting Composite Key JOIN Results")
    print("📊 Creating Excel files for database verification")
    print("=" * 60)
    
    service = SQLQueryService()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export 1: Sample composite key matches
    print("\n1. Exporting sample composite key matches...")
    try:
        # ⭐ HERE IS THE QUERY YOU ASKED ABOUT ⭐
        sample_sql = """
        SELECT 
            l.lg_siscon_code,
            l.lg_branch_code,
            l.lg_voucher_no,
            l.lg_voucher_date,
            l.lg_voucher_type,
            l.lg_narration,
            ld.lgd_serial_no,
            ld.lgd_acc_code,
            ld.lgd_amount,
            ld.lgd_remarks,
            ld.lgd_voucher_date as detail_voucher_date,
            ld.lgd_voucher_type as detail_voucher_type
        FROM ledger l
        INNER JOIN ledger_detail ld ON (
            l.lg_siscon_code = ld.lgd_siscon_code 
            AND l.lg_branch_code = ld.lgd_branch_code 
            AND l.lg_voucher_no = ld.lgd_voucher_no
        )
        ORDER BY l.lg_voucher_date DESC, l.lg_siscon_code, l.lg_branch_code
        LIMIT 1000
        """
        
        result = service._execute_sql_against_files(sample_sql.strip())
        
        # Convert to DataFrame and export
        df_sample = pd.DataFrame(result['data'])
        filename_sample = f"composite_key_sample_{timestamp}.xlsx"
        df_sample.to_excel(filename_sample, index=False)
        
        print(f"✅ Sample data exported: {filename_sample}")
        print(f"   📊 Records: {len(df_sample)}")
        print(f"   🔍 Columns: {len(df_sample.columns)}")
        
    except Exception as e:
        print(f"❌ Sample export error: {e}")

if __name__ == "__main__":
    export_composite_data() 