"""
Comprehensive Aggregation Test Suite - Testing with Different Tables, Columns, and Scenarios
This file tests aggregation functionality with 10+ different realistic queries.
"""

import requests
import json
from typing import List, Dict
import time

BASE_URL = "http://localhost:8000/api/sql-query"

def test_query(test_name: str, query_config: Dict) -> Dict:
    """Test a query configuration and return results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(f"{BASE_URL}/generate", json=query_config, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"\nGenerated SQL:")
            print(f"{result['sql']}")
            
            # Check if aggregations are present in SQL
            sql_lower = result['sql'].lower()
            has_sum = 'sum(' in sql_lower
            has_count = 'count(' in sql_lower
            has_avg = 'avg(' in sql_lower
            has_min = 'min(' in sql_lower
            has_max = 'max(' in sql_lower
            has_count_distinct = 'count(distinct' in sql_lower
            
            aggregation_found = has_sum or has_count or has_avg or has_min or has_max or has_count_distinct
            
            if aggregation_found:
                print(f"\n✅ Aggregation functions detected in SQL")
                if has_sum:
                    print(f"   - SUM found")
                if has_avg:
                    print(f"   - AVG found")
                if has_count:
                    print(f"   - COUNT found")
                if has_min:
                    print(f"   - MIN found")
                if has_max:
                    print(f"   - MAX found")
                if has_count_distinct:
                    print(f"   - COUNT(DISTINCT) found")
            else:
                print(f"\n⚠️  WARNING: No aggregation functions found in SQL!")
            
            return {"success": True, "result": result, "has_aggregations": aggregation_found}
        else:
            error = response.json()
            print(f"❌ FAILED: {error}")
            return {"success": False, "error": error}
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE AGGREGATION TEST SUITE - 10+ Different Queries")
    print("="*80)
    
    test_results = []
    
    # Test 1: Simple SUM on amount column
    test_results.append(test_query(
        "Test 1: SUM of amount column (no GROUP BY)",
        {
            "tables": [
                {
                    "name": "ledger_detail",
                    "columns": []
                }
            ],
            "aggregations": [
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "SUM",
                    "alias": "total_amount"
                }
            ]
        }
    ))
    
    # Test 2: COUNT of all records grouped by account code
    test_results.append(test_query(
        "Test 2: COUNT records grouped by account_code",
        {
            "tables": [
                {
                    "name": "ledger_detail",
                    "columns": ["lgd_account_code"]
                }
            ],
            "aggregations": [
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "record_count"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 3: AVG of amount with multiple aggregations
    test_results.append(test_query(
        "Test 3: AVG and SUM of amount, grouped by voucher type",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_voucher_type"]
                }
            ],
            "joins": [
                {
                    "type": "INNER JOIN",
                    "table": "ledger_detail",
                    "alias": "lgd",
                    "conditions": [
                        {
                            "left_table": "ledger",
                            "left_column": "lg_voucher_no",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_voucher_no"
                        }
                    ]
                }
            ],
            "aggregations": [
                {
                    "column": "lgd.lgd_amount",
                    "function": "AVG",
                    "alias": "average_amount"
                },
                {
                    "column": "lgd.lgd_amount",
                    "function": "SUM",
                    "alias": "total_amount"
                }
            ],
            "group_by": ["ledger.lg_voucher_type"]
        }
    ))
    
    # Test 4: MIN and MAX on different columns
    test_results.append(test_query(
        "Test 4: MIN and MAX of amount, grouped by branch",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_branch_code"]
                }
            ],
            "joins": [
                {
                    "type": "LEFT JOIN",
                    "table": "ledger_detail",
                    "alias": "lgd",
                    "conditions": [
                        {
                            "left_table": "ledger",
                            "left_column": "lg_voucher_no",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_voucher_no"
                        }
                    ]
                }
            ],
            "aggregations": [
                {
                    "column": "lgd.lgd_amount",
                    "function": "MIN",
                    "alias": "min_amount"
                },
                {
                    "column": "lgd.lgd_amount",
                    "function": "MAX",
                    "alias": "max_amount"
                }
            ],
            "group_by": ["ledger.lg_branch_code"]
        }
    ))
    
    # Test 5: COUNT DISTINCT on voucher numbers
    test_results.append(test_query(
        "Test 5: COUNT DISTINCT vouchers grouped by voucher type",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_voucher_type"]
                }
            ],
            "aggregations": [
                {
                    "column": "ledger.lg_voucher_no",
                    "function": "COUNT_DISTINCT",
                    "alias": "unique_vouchers"
                }
            ],
            "group_by": ["ledger.lg_voucher_type"]
        }
    ))
    
    # Test 6: Multiple aggregations with WHERE filter
    test_results.append(test_query(
        "Test 6: SUM, COUNT, AVG with WHERE condition (amount > 0)",
        {
            "tables": [
                {
                    "name": "ledger_detail",
                    "columns": ["lgd_account_code"]
                }
            ],
            "where_conditions": [
                {
                    "left_side": "ledger_detail.lgd_amount",
                    "operator": ">",
                    "right_side": "0",
                    "logical_operator": "AND"
                }
            ],
            "aggregations": [
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "SUM",
                    "alias": "total_positive"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "transaction_count"
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "AVG",
                    "alias": "average_positive"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 7: Complex JOIN with multiple aggregations
    test_results.append(test_query(
        "Test 7: Complex JOIN with SUM and COUNT on different joined columns",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_voucher_type", "lg_branch_code"]
                }
            ],
            "joins": [
                {
                    "type": "INNER JOIN",
                    "table": "ledger_detail",
                    "alias": "lgd",
                    "conditions": [
                        {
                            "left_table": "ledger",
                            "left_column": "lg_voucher_no",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_voucher_no"
                        },
                        {
                            "left_table": "ledger",
                            "left_column": "lg_siscon_code",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_siscon_code"
                        }
                    ]
                }
            ],
            "aggregations": [
                {
                    "column": "lgd.lgd_amount",
                    "function": "SUM",
                    "alias": "sum_amount"
                },
                {
                    "column": "lgd.lgd_amount",
                    "function": "COUNT",
                    "alias": "count_amount"
                }
            ],
            "group_by": ["ledger.lg_voucher_type", "ledger.lg_branch_code"]
        }
    ))
    
    # Test 8: All aggregation functions together
    test_results.append(test_query(
        "Test 8: All aggregation functions (SUM, COUNT, AVG, MIN, MAX) together",
        {
            "tables": [
                {
                    "name": "ledger_detail",
                    "columns": ["lgd_account_code"]
                }
            ],
            "aggregations": [
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "SUM",
                    "alias": "total"
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "AVG",
                    "alias": "average"
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "MIN",
                    "alias": "minimum"
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "MAX",
                    "alias": "maximum"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "count"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 9: Aggregation with ORDER BY and LIMIT
    test_results.append(test_query(
        "Test 9: SUM with ORDER BY and LIMIT (top 10)",
        {
            "tables": [
                {
                    "name": "ledger_detail",
                    "columns": ["lgd_account_code"]
                }
            ],
            "aggregations": [
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "SUM",
                    "alias": "total_amount"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"],
            "order_by": [
                {
                    "column": "total_amount",
                    "direction": "DESC"
                }
            ],
            "limit": 10
        }
    ))
    
    # Test 10: COUNT DISTINCT with multiple conditions
    test_results.append(test_query(
        "Test 10: COUNT DISTINCT with complex WHERE conditions",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_voucher_type"]
                }
            ],
            "where_conditions": [
                {
                    "left_side": "ledger.lg_branch_code",
                    "operator": "IS NOT NULL",
                    "right_side": "",
                    "logical_operator": "AND"
                }
            ],
            "aggregations": [
                {
                    "column": "ledger.lg_voucher_no",
                    "function": "COUNT_DISTINCT",
                    "alias": "distinct_vouchers"
                }
            ],
            "group_by": ["ledger.lg_voucher_type"]
        }
    ))
    
    # Test 11: Aggregation on joined table column with alias
    test_results.append(test_query(
        "Test 11: SUM on joined table with table alias",
        {
            "tables": [
                {
                    "name": "ledger",
                    "alias": "l",
                    "columns": ["lg_voucher_type"]
                }
            ],
            "joins": [
                {
                    "type": "RIGHT JOIN",
                    "table": "ledger_detail",
                    "alias": "ld",
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
            "aggregations": [
                {
                    "column": "ld.lgd_amount",
                    "function": "SUM",
                    "alias": "total"
                }
            ],
            "group_by": ["l.lg_voucher_type"]
        }
    ))
    
    # Test 12: Multiple tables with multiple aggregations
    test_results.append(test_query(
        "Test 12: Complex query with FULL OUTER JOIN and multiple aggregations",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_branch_code"]
                }
            ],
            "joins": [
                {
                    "type": "FULL OUTER JOIN",
                    "table": "ledger_detail",
                    "alias": "lgd",
                    "conditions": [
                        {
                            "left_table": "ledger",
                            "left_column": "lg_voucher_no",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_voucher_no"
                        }
                    ]
                }
            ],
            "aggregations": [
                {
                    "column": "lgd.lgd_amount",
                    "function": "SUM",
                    "alias": "sum_amount"
                },
                {
                    "column": "lgd.lgd_amount",
                    "function": "AVG",
                    "alias": "avg_amount"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "total_records"
                }
            ],
            "group_by": ["ledger.lg_branch_code"],
            "order_by": [
                {
                    "column": "sum_amount",
                    "direction": "DESC"
                }
            ]
        }
    ))
    
    # Test 13: Aggregation without alias
    test_results.append(test_query(
        "Test 13: Aggregation without alias (should still work)",
        {
            "tables": [
                {
                    "name": "ledger_detail",
                    "columns": []
                }
            ],
            "aggregations": [
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "SUM"
                    # No alias specified
                }
            ]
        }
    ))
    
    # Test 14: COUNT with WHERE and GROUP BY
    test_results.append(test_query(
        "Test 14: COUNT with WHERE condition and GROUP BY",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_branch_code"]
                }
            ],
            "where_conditions": [
                {
                    "left_side": "ledger.lg_voucher_type",
                    "operator": "=",
                    "right_side": "'PAYMENT'",
                    "logical_operator": "AND"
                }
            ],
            "aggregations": [
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "payment_count"
                }
            ],
            "group_by": ["ledger.lg_branch_code"]
        }
    ))
    
    # Test 15: Mixed aggregations with different column references
    test_results.append(test_query(
        "Test 15: Mixed aggregations (COUNT DISTINCT + SUM + AVG)",
        {
            "tables": [
                {
                    "name": "ledger",
                    "columns": ["lg_voucher_type"]
                }
            ],
            "joins": [
                {
                    "type": "INNER JOIN",
                    "table": "ledger_detail",
                    "alias": "lgd",
                    "conditions": [
                        {
                            "left_table": "ledger",
                            "left_column": "lg_voucher_no",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_voucher_no"
                        }
                    ]
                }
            ],
            "aggregations": [
                {
                    "column": "ledger.lg_voucher_no",
                    "function": "COUNT_DISTINCT",
                    "alias": "unique_vouchers"
                },
                {
                    "column": "lgd.lgd_amount",
                    "function": "SUM",
                    "alias": "total_amount"
                },
                {
                    "column": "lgd.lgd_amount",
                    "function": "AVG",
                    "alias": "avg_amount"
                }
            ],
            "group_by": ["ledger.lg_voucher_type"]
        }
    ))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in test_results if result.get("success"))
    failed = sum(1 for result in test_results if not result.get("success"))
    aggregations_working = sum(1 for result in test_results if result.get("has_aggregations", False))
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"✅ Aggregations Working: {aggregations_working}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Aggregation Detection Rate: {(aggregations_working/total)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for i, result in enumerate(test_results, 1):
            if not result.get("success"):
                print(f"  Test {i}: {result.get('error', 'Unknown error')}")
    
    if aggregations_working < total:
        print("\n⚠️  TESTS WITH MISSING AGGREGATIONS:")
        for i, result in enumerate(test_results, 1):
            if result.get("success") and not result.get("has_aggregations"):
                print(f"  Test {i}: Aggregation functions not found in generated SQL")

if __name__ == "__main__":
    # Wait a bit for server to be ready
    import time
    print("Waiting for server to be ready...")
    time.sleep(2)
    main()

