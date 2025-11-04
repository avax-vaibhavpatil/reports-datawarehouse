"""
Test Aggregation Feature - All Possible Query Combinations and Scenarios
This file tests the aggregation functionality with various query combinations.
"""

import requests
import json
from typing import List, Dict

BASE_URL = "http://localhost:8000/api/sql-query"

def test_query(test_name: str, query_config: Dict) -> Dict:
    """Test a query configuration and return results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(f"{BASE_URL}/generate", json=query_config)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"\nGenerated SQL:")
            print(f"{result['sql']}")
            print(f"\nFormatted SQL:")
            print(f"{result['formatted_sql']}")
            return {"success": True, "result": result}
        else:
            error = response.json()
            print(f"❌ FAILED: {error}")
            return {"success": False, "error": error}
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE AGGREGATION TEST SUITE")
    print("="*80)
    
    test_results = []
    
    # Test 1: Simple SUM aggregation without GROUP BY (aggregate entire dataset)
    test_results.append(test_query(
        "Test 1: Simple SUM without GROUP BY",
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
    
    # Test 2: Multiple aggregations without GROUP BY
    test_results.append(test_query(
        "Test 2: Multiple aggregations (SUM, COUNT, AVG) without GROUP BY",
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
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "AVG",
                    "alias": "avg_amount"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "total_records"
                }
            ]
        }
    ))
    
    # Test 3: Aggregation with GROUP BY (one grouping column)
    test_results.append(test_query(
        "Test 3: SUM with single GROUP BY column",
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
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 4: Multiple aggregations with GROUP BY
    test_results.append(test_query(
        "Test 4: Multiple aggregations with GROUP BY",
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
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "AVG",
                    "alias": "avg_amount"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "transaction_count"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 5: Aggregation with JOIN and GROUP BY
    test_results.append(test_query(
        "Test 5: Aggregation with JOIN and GROUP BY",
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
                    "function": "SUM",
                    "alias": "total_amount"
                }
            ],
            "group_by": ["ledger.lg_voucher_type"]
        }
    ))
    
    # Test 6: All aggregation functions tested
    test_results.append(test_query(
        "Test 6: All aggregation functions (SUM, COUNT, AVG, MIN, MAX)",
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
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "AVG",
                    "alias": "avg_amount"
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "MIN",
                    "alias": "min_amount"
                },
                {
                    "column": "ledger_detail.lgd_amount",
                    "function": "MAX",
                    "alias": "max_amount"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "total_records"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 7: COUNT DISTINCT
    test_results.append(test_query(
        "Test 7: COUNT DISTINCT aggregation",
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
    
    # Test 8: Aggregation with WHERE conditions
    test_results.append(test_query(
        "Test 8: Aggregation with WHERE filter",
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
                    "alias": "total_positive_amount"
                }
            ],
            "group_by": ["ledger_detail.lgd_account_code"]
        }
    ))
    
    # Test 9: Aggregation with ORDER BY
    test_results.append(test_query(
        "Test 9: Aggregation with ORDER BY",
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
            "limit": 100
        }
    ))
    
    # Test 10: Complex scenario - JOIN + Aggregation + GROUP BY + ORDER BY + LIMIT
    test_results.append(test_query(
        "Test 10: Complex - JOIN + Multiple Aggregations + GROUP BY + ORDER BY + LIMIT",
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
                        },
                        {
                            "left_table": "ledger",
                            "left_column": "lg_branch_code",
                            "operator": "=",
                            "right_table": "lgd",
                            "right_column": "lgd_branch_code"
                        }
                    ]
                }
            ],
            "aggregations": [
                {
                    "column": "lgd.lgd_amount",
                    "function": "SUM",
                    "alias": "total_amount"
                },
                {
                    "column": "*",
                    "function": "COUNT",
                    "alias": "record_count"
                }
            ],
            "group_by": ["ledger.lg_voucher_type", "ledger.lg_branch_code"],
            "order_by": [
                {
                    "column": "total_amount",
                    "direction": "DESC"
                }
            ],
            "limit": 50
        }
    ))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in test_results if result.get("success"))
    failed = sum(1 for result in test_results if not result.get("success"))
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for i, result in enumerate(test_results, 1):
            if not result.get("success"):
                print(f"  Test {i}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()





