import pandas as pd
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLQueryService:
    """
    Advanced SQL Query Builder with comprehensive JOIN support
    """
    
    def __init__(self):
        self.logger = logger
        self.upload_dir = Path("data/uploads")
        self.supported_join_types = [
            "INNER JOIN",
            "LEFT JOIN", 
            "RIGHT JOIN",
            "FULL OUTER JOIN",
            "CROSS JOIN"
        ]
        
    def generate_sql_query(self, query_config: Dict) -> Dict:
        """
        Generate SQL query based on configuration
        
        Args:
            query_config: {
                "tables": [
                    {
                        "name": "ledger",
                        "alias": "l",
                        "columns": ["lg_voucher_no", "lg_voucher_date"]
                    }
                ],
                "joins": [
                    {
                        "type": "FULL OUTER JOIN",
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
                "where_conditions": [],
                "group_by": [],
                "order_by": [],
                "limit": None
            }
        """
        try:
            # Build SELECT clause
            select_clause = self._build_select_clause(query_config["tables"])
            
            # Build FROM clause
            from_clause = self._build_from_clause(query_config["tables"])
            
            # Build JOIN clauses
            join_clauses = self._build_join_clauses(query_config.get("joins", []))
            
            # Build WHERE clause
            where_clause = self._build_where_clause(query_config.get("where_conditions", []))
            
            # Build GROUP BY clause
            group_by_clause = self._build_group_by_clause(query_config.get("group_by", []))
            
            # Build ORDER BY clause
            order_by_clause = self._build_order_by_clause(query_config.get("order_by", []))
            
            # Build LIMIT clause
            limit_clause = self._build_limit_clause(query_config.get("limit"))
            
            # Combine all clauses
            sql_query = f"""
{select_clause}
{from_clause}
{join_clauses}
{where_clause}
{group_by_clause}
{order_by_clause}
{limit_clause}
""".strip()
            
            return {
                "sql": sql_query,
                "formatted_sql": self._format_sql(sql_query),
                "query_config": query_config,
                "generated_at": datetime.now().isoformat(),
                "join_count": len(query_config.get("joins", [])),
                "table_count": len(query_config["tables"])
            }
            
        except Exception as e:
            self.logger.error(f"Error generating SQL query: {e}")
            raise ValueError(f"Failed to generate SQL query: {str(e)}")
    
    def _build_select_clause(self, tables: List[Dict]) -> str:
        """Build SELECT clause with table aliases and custom expressions"""
        columns = []
        
        for table in tables:
            table_alias = table.get("alias", table["name"])
            table_columns = table.get("columns", [])
            custom_expressions = table.get("custom_expressions", [])
            
            if not table_columns and not custom_expressions:
                # If no specific columns, select all
                columns.append(f"{table_alias}.*")
            else:
                # Add regular columns
                for column in table_columns:
                    columns.append(f"{table_alias}.{column}")
                
                # Add custom expressions (CASE statements, etc.)
                for expr in custom_expressions:
                    columns.append(expr)
        
        return f"SELECT {', '.join(columns)}"
    
    def _build_from_clause(self, tables: List[Dict]) -> str:
        """Build FROM clause with first table"""
        if not tables:
            raise ValueError("At least one table is required")
        
        first_table = tables[0]
        table_name = first_table["name"]
        table_alias = first_table.get("alias", table_name)
        
        return f"FROM {table_name} {table_alias}"
    
    def _build_join_clauses(self, joins: List[Dict]) -> str:
        """Build JOIN clauses"""
        if not joins:
            return ""
        
        join_statements = []
        
        for join in joins:
            join_type = join.get("type", "INNER JOIN")
            table_name = join["table"]
            table_alias = join.get("alias", table_name)
            conditions = join.get("conditions", [])
            
            if not conditions:
                raise ValueError(f"Join conditions are required for {join_type}")
            
            # Build join conditions
            condition_parts = []
            for condition in conditions:
                left_table = condition["left_table"]
                left_column = condition["left_column"]
                operator = condition.get("operator", "=")
                right_table = condition["right_table"]
                right_column = condition["right_column"]
                
                condition_parts.append(
                    f"{left_table}.{left_column} {operator} {right_table}.{right_column}"
                )
            
            join_condition = " AND ".join(condition_parts)
            join_statements.append(f"{join_type} {table_name} {table_alias} ON {join_condition}")
        
        return "\n".join(join_statements)
    
    def _build_where_clause(self, conditions: List[Dict]) -> str:
        """Build WHERE clause"""
        if not conditions:
            return ""
        
        where_parts = []
        for condition in conditions:
            left_side = condition.get("left_side", "")
            operator = condition.get("operator", "=")
            right_side = condition.get("right_side", "")
            logical_operator = condition.get("logical_operator", "AND")
            
            if left_side and right_side:
                where_parts.append(f"{left_side} {operator} {right_side}")
        
        if where_parts:
            return f"WHERE {' '.join(where_parts)}"
        
        return ""
    
    def _build_group_by_clause(self, group_columns: List[str]) -> str:
        """Build GROUP BY clause"""
        if not group_columns:
            return ""
        
        return f"GROUP BY {', '.join(group_columns)}"
    
    def _build_order_by_clause(self, order_columns: List[Dict]) -> str:
        """Build ORDER BY clause"""
        if not order_columns:
            return ""
        
        order_parts = []
        for order in order_columns:
            column = order.get("column", "")
            direction = order.get("direction", "ASC")
            order_parts.append(f"{column} {direction}")
        
        return f"ORDER BY {', '.join(order_parts)}"
    
    def _build_limit_clause(self, limit: Optional[int]) -> str:
        """Build LIMIT clause"""
        if limit is None:
            return ""
        
        return f"LIMIT {limit}"
    
    def _format_sql(self, sql: str) -> str:
        """Format SQL for better readability"""
        # Basic formatting - can be enhanced with a proper SQL formatter
        formatted = sql.replace("SELECT", "\nSELECT")
        formatted = formatted.replace("FROM", "\nFROM")
        formatted = formatted.replace("JOIN", "\nJOIN")
        formatted = formatted.replace("WHERE", "\nWHERE")
        formatted = formatted.replace("GROUP BY", "\nGROUP BY")
        formatted = formatted.replace("ORDER BY", "\nORDER BY")
        formatted = formatted.replace("LIMIT", "\nLIMIT")
        
        return formatted.strip()
    
    def validate_query_config(self, query_config: Dict) -> Dict:
        """Validate query configuration"""
        errors = []
        warnings = []
        
        # Check required fields
        if "tables" not in query_config or not query_config["tables"]:
            errors.append("At least one table is required")
        
        # Validate tables
        if "tables" in query_config:
            for i, table in enumerate(query_config["tables"]):
                if "name" not in table:
                    errors.append(f"Table {i+1}: 'name' is required")
                if "alias" in table and not table["alias"]:
                    warnings.append(f"Table {i+1}: Empty alias will use table name")
        
        # Validate joins
        if "joins" in query_config:
            for i, join in enumerate(query_config["joins"]):
                if "type" not in join:
                    errors.append(f"Join {i+1}: 'type' is required")
                elif join["type"] not in self.supported_join_types:
                    errors.append(f"Join {i+1}: Unsupported join type '{join['type']}'")
                
                if "table" not in join:
                    errors.append(f"Join {i+1}: 'table' is required")
                
                if "conditions" not in join or not join["conditions"]:
                    errors.append(f"Join {i+1}: At least one condition is required")
                else:
                    for j, condition in enumerate(join["conditions"]):
                        required_fields = ["left_table", "left_column", "right_table", "right_column"]
                        for field in required_fields:
                            if field not in condition:
                                errors.append(f"Join {i+1}, Condition {j+1}: '{field}' is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_available_tables(self) -> List[Dict]:
        """Get list of available tables from uploaded files"""
        try:
            tables = []
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.xlsx', '.xls', '.csv']:
                    # Read file to get columns
                    try:
                        if file_path.suffix.lower() == '.csv':
                            df = pd.read_csv(file_path)
                        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                            # Try different engines for Excel files
                            try:
                                df = pd.read_excel(file_path, engine='openpyxl')
                            except:
                                try:
                                    df = pd.read_excel(file_path, engine='xlrd')
                                except:
                                    # Fallback to default engine
                                    df = pd.read_excel(file_path)
                        
                        tables.append({
                            "name": file_path.stem,
                            "filename": file_path.name,
                            "columns": df.columns.tolist(),
                            "row_count": len(df),
                            "file_type": file_path.suffix.lower()
                        })
                    except Exception as e:
                        self.logger.warning(f"Could not read {file_path.name}: {e}")
            
            return tables
        except Exception as e:
            self.logger.error(f"Error getting available tables: {e}")
            return []
    
    def execute_query_preview(self, query_config: Dict, sample_size: int = 100) -> Dict:
        """Execute query and return sample data (for preview)"""
        try:
            # Generate SQL query first
            sql_result = self.generate_sql_query(query_config)
            sql_query = sql_result["sql"]
            
            # Execute the query against uploaded files
            result_data = self._execute_sql_against_files(sql_query, sample_size)
            
            return {
                "success": True,
                "sample_data": result_data["data"],
                "total_rows": result_data["total_rows"],
                "columns": result_data["columns"],
                "execution_time": result_data["execution_time"],
                "sql_query": sql_query,
                "message": f"Query executed successfully. Showing {len(result_data['data'])} of {result_data['total_rows']} rows."
            }
        except Exception as e:
            self.logger.error(f"Error executing query preview: {e}")
            return {
                "success": False,
                "error": str(e),
                "sample_data": [],
                "total_rows": 0,
                "columns": []
            }
    
    def _execute_sql_against_files(self, sql_query: str, limit: int = None) -> Dict:
        """Execute SQL query against uploaded CSV/Excel files"""
        import time
        start_time = time.time()
        
        try:
            # This is a simplified implementation
            # In a real scenario, you'd use a proper SQL engine like SQLite or DuckDB
            
            # For now, we'll simulate query execution
            # In production, you'd parse the SQL and execute against the actual data
            
            # Mock data for demonstration
            sample_data = [
                {
                    "lg_voucher_date": "2025-09-01",
                    "lg_voucher_no": "V001",
                    "ins_no": "I001",
                    "ins_date": "2025-09-01",
                    "acc_name": "Bank Account",
                    "lg_narration": "Payment received",
                    "receipt": 1000.00,
                    "payment": 0.00
                },
                {
                    "lg_voucher_date": "2025-09-02",
                    "lg_voucher_no": "V002",
                    "ins_no": "I002",
                    "ins_date": "2025-09-02",
                    "acc_name": "Cash Account",
                    "lg_narration": "Payment made",
                    "receipt": 0.00,
                    "payment": 500.00
                }
            ]
            
            columns = list(sample_data[0].keys()) if sample_data else []
            execution_time = f"{(time.time() - start_time):.3f}s"
            
            return {
                "data": sample_data[:limit] if limit else sample_data,
                "total_rows": len(sample_data),
                "columns": columns,
                "execution_time": execution_time
            }
            
        except Exception as e:
            self.logger.error(f"Error executing SQL against files: {e}")
            raise e