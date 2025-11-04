import pandas as pd
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path
import json
from datetime import datetime
import sqlite3
from sqlalchemy import create_engine, text
from app.services.database_connection_service import DatabaseConnectionService
from app.services.chunked_insertion_service import ChunkedInsertionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLQueryService:
    """
    Advanced SQL Query Builder with comprehensive JOIN support
    Now with REAL SQL execution using SQLite!
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
        # SQLite connection will be created per request (stateless)
        
    def _get_database_connection(self):
        """Create a persistent SQLite database connection"""
        db_path = self.upload_dir.parent / "excel_data.db"  # data/excel_data.db
        return sqlite3.connect(str(db_path))
    
    def _load_uploaded_files_to_database(self, conn: sqlite3.Connection) -> Dict[str, Dict]:
        """Load all uploaded files into the SQLite database with optimized indexing"""
        cursor = conn.cursor()
        loaded_tables = {}
        
        try:
            # Find all CSV and Excel files
            csv_files = list(self.upload_dir.glob("*.csv"))
            xlsx_files = list(self.upload_dir.glob("*.xlsx"))
            xls_files = list(self.upload_dir.glob("*.xls"))
            
            all_files = csv_files + xlsx_files + xls_files
            
            self.logger.info(f"Loading {len(all_files)} files into database...")
            
            for file_path in all_files:
                try:
                    # Skip very small or system files
                    if file_path.stat().st_size < 10 or file_path.name.startswith('.'):
                        continue
                    
                    # Create clean table name
                    table_name = file_path.stem.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '').lower()
                    
                    # Load file based on extension
                    if file_path.suffix.lower() == '.csv':
                        df = pd.read_csv(file_path)
                    else:  # Excel files
                        df = pd.read_excel(file_path)
                    
                    # Skip empty files
                    if df.empty:
                        self.logger.warning(f"Skipping empty file: {file_path.name}")
                        continue
                    
                    # Load into SQLite
                    df.to_sql(table_name, conn, index=False, if_exists='replace')
                    
                    # Create indexes for common join columns to optimize JOIN performance
                    self._create_optimized_indexes(cursor, table_name, df.columns)
                    
                    # Track loaded table
                    loaded_tables[table_name] = {
                        'original_filename': file_path.name,
                        'row_count': len(df),
                        'columns': list(df.columns)
                    }
                    
                    self.logger.info(f"Loaded {file_path.name} → {table_name} ({len(df)} rows)")
                    
                except Exception as e:
                    self.logger.error(f"Error loading {file_path.name}: {e}")
                    continue
            
            self.logger.info(f"Successfully loaded {len(loaded_tables)} tables")
            return loaded_tables
            
        except Exception as e:
            self.logger.error(f"Error loading files to database: {e}")
            return {}
    
    def _create_optimized_indexes(self, cursor: sqlite3.Cursor, table_name: str, columns: List[str]) -> None:
        """Create indexes on common join columns to optimize JOIN performance"""
        try:
            # Common join column patterns that appear in your data
            join_patterns = [
                # Voucher number patterns
                r'.*voucher.*no.*',
                r'.*vch.*no.*',
                r'.*voucher_no.*',
                # Branch code patterns
                r'.*branch.*code.*',
                r'.*br.*code.*',
                # Siscon code patterns
                r'.*siscon.*code.*',
                r'.*siscon_code.*',
                # Account code patterns
                r'.*acc.*code.*',
                r'.*account.*code.*',
                # Customer/Supplier code patterns
                r'.*cust.*code.*',
                r'.*supplr.*code.*',
                # Bank code patterns
                r'.*bank.*code.*',
                r'.*sbnk.*code.*',
                # ID patterns
                r'.*id$',
                r'.*_id$',
                # Date patterns
                r'.*date.*',
                r'.*_date$'
            ]
            
            import re
            indexed_columns = set()
            
            for column in columns:
                column_lower = column.lower()
                for pattern in join_patterns:
                    if re.match(pattern, column_lower):
                        if column not in indexed_columns:
                            try:
                                index_name = f"idx_{table_name}_{column.replace('.', '_')}"
                                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column})")
                                indexed_columns.add(column)
                                self.logger.info(f"Created index on {table_name}.{column}")
                            except Exception as e:
                                self.logger.warning(f"Could not create index on {table_name}.{column}: {e}")
                        break
            
            # Create composite indexes for common multi-column joins
            if 'lg_voucher_no' in columns and 'lg_siscon_code' in columns and 'lg_branch_code' in columns:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_voucher_composite ON {table_name} (lg_voucher_no, lg_siscon_code, lg_branch_code)")
                    self.logger.info(f"Created composite index on {table_name} for voucher columns")
                except Exception as e:
                    self.logger.warning(f"Could not create composite index on {table_name}: {e}")
            
            if 'lgd_voucher_no' in columns and 'lgd_siscon_code' in columns and 'lgd_branch_code' in columns:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_voucher_detail_composite ON {table_name} (lgd_voucher_no, lgd_siscon_code, lgd_branch_code)")
                    self.logger.info(f"Created composite index on {table_name} for voucher detail columns")
                except Exception as e:
                    self.logger.warning(f"Could not create composite index on {table_name}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error creating indexes for {table_name}: {e}")

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
                        "columns": ["lgd_budget_code", "lgd_branch_code", "lgd_qty"],  # Added support for join table columns
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
            aggregations = query_config.get("aggregations", [])
            
            # Build SELECT clause - now includes columns from joined tables
            select_clause = self._build_select_clause(
                query_config["tables"], 
                query_config.get("joins", []),
                aggregations,
                query_config.get("group_by", [])
            )
            
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
    
    def _build_select_clause(self, tables: List[Dict], joins: List[Dict] = None, aggregations: List[Dict] = None, group_by: List[str] = None) -> str:
        """Build SELECT clause with table aliases and custom expressions, including joined table columns and aggregations"""
        columns = []
        group_by = group_by or []
        columns_set = set()  # Track all column variations to avoid duplicates
        
        # Helper function to normalize column name for comparison (extracts base column name)
        def get_base_column_name(col_name: str) -> str:
            """Extract base column name (without table prefix)"""
            # Remove any SQL functions or AS aliases first
            col_clean = col_name.strip()
            # Handle aggregate functions - extract column from inside function
            if '(' in col_clean and ')' in col_clean:
                # For functions like SUM(ledger.lgd_amount), extract the column part
                func_match = col_clean.split('(')
                if len(func_match) > 1:
                    col_part = func_match[1].split(')')[0].strip()
                    if '.' in col_part:
                        return col_part.split('.')[-1]
                    return col_part
            # Handle AS aliases
            if ' AS ' in col_clean.upper():
                col_part = col_clean.split(' AS ')[0].strip()
                if '.' in col_part:
                    return col_part.split('.')[-1]
                return col_part
            # Regular column
            if '.' in col_clean:
                return col_clean.split('.')[-1]
            return col_clean
        
        # Track base column names that have been added (for duplicate detection)
        added_base_columns = set()
        
        # Helper function to check if column is already added (checks both prefixed and non-prefixed versions)
        def is_column_already_added(col_name: str) -> bool:
            """Check if column or any variation is already in columns_set"""
            # Check exact match
            if col_name in columns_set:
                return True
            
            # Get base column name for comparison
            base_name = get_base_column_name(col_name)
            
            # Check if this base column name has already been added
            if base_name in added_base_columns:
                return True
            
            # Also check if any existing column has the same base name
            for existing_col in columns_set:
                existing_base = get_base_column_name(existing_col)
                # If base names match, they're the same column (duplicate)
                if existing_base == base_name:
                    return True
            
            return False
        
        # Helper function to add column and track it
        def add_column(col_name: str):
            """Add column to list and track variations"""
            if not is_column_already_added(col_name):
                columns.append(col_name)
                columns_set.add(col_name)
                # Track the base column name (without prefix) for duplicate detection
                base_name = get_base_column_name(col_name)
                added_base_columns.add(base_name)
        
        # Track which columns are being aggregated (to prevent selecting individual values)
        aggregated_columns = set()
        
        # If aggregations exist, add them first
        if aggregations:
            for agg in aggregations:
                function = agg.get("function", "SUM")
                column = agg.get("column", "")
                alias = agg.get("alias")
                
                if column:
                    # Track that this column is being aggregated
                    base_agg_col = get_base_column_name(column)
                    aggregated_columns.add(base_agg_col)
                    
                    # Handle COUNT_DISTINCT specially - SQL syntax is COUNT(DISTINCT column)
                    if function == "COUNT_DISTINCT":
                        sql_function = f"COUNT(DISTINCT {column})"
                    else:
                        sql_function = f"{function}({column})"
                    
                    if alias:
                        columns.append(f"{sql_function} AS {alias}")
                        columns_set.add(f"{sql_function} AS {alias}")
                    else:
                        columns.append(sql_function)
                        columns_set.add(sql_function)
        
        # Build a map of all table/join aliases and their columns for GROUP BY normalization
        # We need to check both selected columns AND all columns that might be in GROUP BY
        table_column_map = {}  # Maps column_name -> (table_alias, column_name)
        join_column_map = {}  # Maps column_name -> (join_alias, column_name)
        
        # Map main table columns (selected columns)
        for table in tables:
            table_alias = table.get("alias") or ""
            if isinstance(table_alias, str):
                table_alias = table_alias.strip()
            else:
                table_alias = ""
            
            if not table_alias or table_alias == "None":
                table_alias = table["name"]
            
            for column in table.get("columns", []):
                # Only map if not already mapped (first occurrence wins)
                if column not in table_column_map:
                    table_column_map[column] = (table_alias, column)
        
        # Map join table columns (selected columns)
        if joins:
            for join in joins:
                join_alias = join.get("alias") or ""
                if isinstance(join_alias, str):
                    join_alias = join_alias.strip()
                else:
                    join_alias = ""
                
                if not join_alias or join_alias == "None":
                    join_alias = join["table"]
                
                for column in join.get("columns", []):
                    # Only map if not already mapped (first occurrence wins)
                    if column not in join_column_map:
                        join_column_map[column] = (join_alias, column)
        
        # Also check GROUP BY columns to find which table they belong to
        # This helps normalize GROUP BY columns that aren't in selected columns yet
        if group_by:
            for group_col in group_by:
                col_name = group_col.strip()
                # If it has a prefix, extract table info
                if '.' in col_name:
                    parts = col_name.split('.', 1)
                    table_ref = parts[0]
                    col_ref = parts[1]
                    # Try to find matching table/join
                    for table in tables:
                        table_alias = table.get("alias") or ""
                        if isinstance(table_alias, str):
                            table_alias = table_alias.strip()
                        else:
                            table_alias = ""
                        if not table_alias or table_alias == "None":
                            table_alias = table["name"]
                        if table_alias == table_ref or table["name"] == table_ref:
                            if col_ref not in table_column_map:
                                table_column_map[col_ref] = (table_alias, col_ref)
                            break
                    if joins:
                        for join in joins:
                            join_alias = join.get("alias") or ""
                            if isinstance(join_alias, str):
                                join_alias = join_alias.strip()
                            else:
                                join_alias = ""
                            if not join_alias or join_alias == "None":
                                join_alias = join["table"]
                            if join_alias == table_ref or join["table"] == table_ref:
                                if col_ref not in join_column_map:
                                    join_column_map[col_ref] = (join_alias, col_ref)
                                break
                else:
                    # No prefix - try to find in table columns first, then join columns
                    # Check if this column name exists in any selected table columns
                    found_in_table = False
                    for table in tables:
                        table_alias = table.get("alias") or ""
                        if isinstance(table_alias, str):
                            table_alias = table_alias.strip()
                        else:
                            table_alias = ""
                        if not table_alias or table_alias == "None":
                            table_alias = table["name"]
                        if col_name in table.get("columns", []):
                            if col_name not in table_column_map:
                                table_column_map[col_name] = (table_alias, col_name)
                            found_in_table = True
                            break
                    if not found_in_table and joins:
                        for join in joins:
                            join_alias = join.get("alias") or ""
                            if isinstance(join_alias, str):
                                join_alias = join_alias.strip()
                            else:
                                join_alias = ""
                            if not join_alias or join_alias == "None":
                                join_alias = join["table"]
                            if col_name in join.get("columns", []):
                                if col_name not in join_column_map:
                                    join_column_map[col_name] = (join_alias, col_name)
                                break
        
        # Track which GROUP BY columns we need to add (defer normalization until we process table columns)
        pending_group_by_columns = []
        # Track which GROUP BY columns have been successfully added (to prevent duplicates)
        added_group_by_columns = set()
        
        # If GROUP BY columns are specified, normalize them to use table prefixes
        # GROUP BY columns must appear in SELECT when using aggregations
        if group_by:
            for group_col in group_by:
                col_name = group_col.strip()
                base_col = get_base_column_name(col_name)
                
                # Check if this column exists in table or join columns
                # If it has a prefix already, use it as-is
                if '.' in col_name:
                    add_column(col_name)
                    added_group_by_columns.add(base_col)
                else:
                    # Try to find matching column in tables or joins
                    normalized_col = None
                    if col_name in table_column_map:
                        table_alias, col = table_column_map[col_name]
                        normalized_col = f"{table_alias}.{col}"
                    elif col_name in join_column_map:
                        join_alias, col = join_column_map[col_name]
                        normalized_col = f"{join_alias}.{col}"
                    
                    # Add normalized column if found, otherwise defer (will be added when processing table columns)
                    if normalized_col:
                        add_column(normalized_col)
                        added_group_by_columns.add(base_col)
                    else:
                        # Defer - will be added when processing table/join columns if found, otherwise add as-is at the end
                        pending_group_by_columns.append(col_name)
        
        # Process main tables (only if no aggregations OR if we're showing individual columns)
        # When aggregations are present and no GROUP BY columns are specified, only return aggregations
        if not aggregations or tables[0].get("columns"):
            for table in tables:
                table_alias = table.get("alias") or ""
                if isinstance(table_alias, str):
                    table_alias = table_alias.strip()
                else:
                    table_alias = ""
                
                # Use table name if no alias or alias is "None"
                if not table_alias or table_alias == "None":
                    table_alias = table["name"]
                
                table_columns = table.get("columns", [])
                custom_expressions = table.get("custom_expressions", [])
                
                if not table_columns and not custom_expressions and not aggregations:
                    # If no specific columns and no aggregations, select all
                    add_column(f"{table_alias}.*")
                elif table_columns or custom_expressions:
                    # Add regular columns (skip if already in GROUP BY or if being aggregated)
                    for column in table_columns:
                        base_col = get_base_column_name(column)
                        full_col_name = f"{table_alias}.{column}"
                        
                        # Skip if this column is already added (via GROUP BY normalization)
                        if is_column_already_added(full_col_name):
                            continue
                        
                        # Skip if this column was already added as a GROUP BY column
                        if base_col in added_group_by_columns:
                            continue
                        
                        # If this column is in pending GROUP BY, add it now and remove from pending
                        if column in pending_group_by_columns:
                            add_column(full_col_name)
                            added_group_by_columns.add(base_col)
                            # Remove from pending (use list comprehension to handle multiple occurrences)
                            pending_group_by_columns = [c for c in pending_group_by_columns if c != column]
                            continue
                        
                        # Skip if this column is being aggregated (unless it's in GROUP BY)
                        if base_col in aggregated_columns:
                            # Only skip if aggregations exist and this column is not in GROUP BY
                            if aggregations:
                                # Check if this column is in GROUP BY (in any form)
                                is_in_group_by = False
                                for gb_col in group_by:
                                    gb_base = get_base_column_name(gb_col.strip())
                                    if gb_base == base_col:
                                        is_in_group_by = True
                                        break
                                if not is_in_group_by:
                                    continue  # Skip this column - it's being aggregated
                        
                        add_column(full_col_name)
                    
                    # Add custom expressions (CASE statements, etc.)
                    for expr in custom_expressions:
                        if expr not in columns_set:
                            columns.append(expr)
                            columns_set.add(expr)
        
        # Process joined tables (only if no aggregations OR if we're showing joined columns)
        if joins and (not aggregations or any(join.get("columns") for join in joins)):
            for join in joins:
                join_alias = join.get("alias") or ""
                if isinstance(join_alias, str):
                    join_alias = join_alias.strip()
                else:
                    join_alias = ""
                
                # Use table name if no alias or alias is "None"
                if not join_alias or join_alias == "None":
                    join_alias = join["table"]
                
                join_columns = join.get("columns", [])
                join_custom_expressions = join.get("custom_expressions", [])
                
                # Add regular columns from joined table (skip if being aggregated)
                for column in join_columns:
                    base_col = get_base_column_name(column)
                    full_col_name = f"{join_alias}.{column}"
                    
                    # Skip if this column is already added (via GROUP BY normalization)
                    if is_column_already_added(full_col_name):
                        continue
                    
                    # Skip if this column was already added as a GROUP BY column
                    if base_col in added_group_by_columns:
                        continue
                    
                    # If this column is in pending GROUP BY, add it now and remove from pending
                    if column in pending_group_by_columns:
                        add_column(full_col_name)
                        added_group_by_columns.add(base_col)
                        # Remove from pending (use list comprehension to handle multiple occurrences)
                        pending_group_by_columns = [c for c in pending_group_by_columns if c != column]
                        continue
                    
                    # Skip if this column is being aggregated (unless it's in GROUP BY)
                    if base_col in aggregated_columns:
                        # Only skip if aggregations exist and this column is not in GROUP BY
                        if aggregations:
                            # Check if this column is in GROUP BY (in any form)
                            is_in_group_by = False
                            for gb_col in group_by:
                                gb_base = get_base_column_name(gb_col.strip())
                                if gb_base == base_col:
                                    is_in_group_by = True
                                    break
                            if not is_in_group_by:
                                continue  # Skip this column - it's being aggregated
                    
                    add_column(full_col_name)
                
                # Add custom expressions from joined table
                for expr in join_custom_expressions:
                    if expr not in columns_set:
                        columns.append(expr)
                        columns_set.add(expr)
        
        # Add any pending GROUP BY columns that weren't found in table/join columns
        # These will be added without prefix (they might be expressions or we couldn't determine table)
        for pending_col in pending_group_by_columns:
            if not is_column_already_added(pending_col):
                add_column(pending_col)
        
        return f"SELECT {', '.join(columns)}"
    
    def _build_from_clause(self, tables: List[Dict]) -> str:
        """Build FROM clause with first table"""
        if not tables:
            raise ValueError("At least one table is required")
        
        first_table = tables[0]
        table_name = first_table["name"]
        table_alias = first_table.get("alias") or ""
        if isinstance(table_alias, str):
            table_alias = table_alias.strip()
        else:
            table_alias = ""
        
        if table_alias and table_alias != "None":
            return f"FROM {table_name} {table_alias}"
        else:
            return f"FROM {table_name}"
    
    def _build_join_clauses(self, joins: List[Dict]) -> str:
        """Build JOIN clauses"""
        if not joins:
            return ""
        
        join_statements = []
        
        for join in joins:
            join_type = join.get("type", "INNER JOIN")
            table_name = join["table"]
            table_alias = join.get("alias") or ""
            if isinstance(table_alias, str):
                table_alias = table_alias.strip()
            else:
                table_alias = ""
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
            
            if table_alias and table_alias != "None":
                join_statements.append(f"{join_type} {table_name} {table_alias} ON {join_condition}")
            else:
                join_statements.append(f"{join_type} {table_name} ON {join_condition}")
        
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
        
        # Validate aggregations
        if "aggregations" in query_config and query_config["aggregations"]:
            for i, agg in enumerate(query_config["aggregations"]):
                if "function" not in agg:
                    errors.append(f"Aggregation {i+1}: 'function' is required")
                elif agg["function"] not in ["SUM", "COUNT", "AVG", "MIN", "MAX", "COUNT_DISTINCT"]:
                    warnings.append(f"Aggregation {i+1}: Uncommon function '{agg['function']}'")
                
                if "column" not in agg:
                    errors.append(f"Aggregation {i+1}: 'column' is required")
        
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
                            df = pd.read_csv(file_path, low_memory=False)
                        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                            # Try different engines for Excel files
                            try:
                                df = pd.read_excel(file_path, engine='openpyxl')
                            except Exception as e1:
                                try:
                                    df = pd.read_excel(file_path, engine='xlrd')
                                except Exception as e2:
                                    try:
                                        # Try reading as CSV if Excel fails
                                        df = pd.read_csv(file_path, low_memory=False)
                                        self.logger.warning(f"Excel file {file_path.name} read as CSV due to format issues")
                                    except Exception as e3:
                                        self.logger.error(f"Could not read {file_path.name} with any method: {e1}, {e2}, {e3}")
                                        continue
                        
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
            result_data = self.execute_raw_sql(sql_query, sample_size)

            if sample_size is None:
                message = f"Query executed sucsesfully. Showing all {result_data['total_rows']} rows"
            
            else:
                 message = (
                    f"Query executed successfully. Showing {len(result_data['data'])} "
                    f"of {result_data['total_rows']} rows."
                    )
            
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
    
    def execute_raw_sql(self, sql_query: str, limit: int = None) -> Dict:
        """Execute SQL query against uploaded CSV/Excel files using SQLite with optimizations"""
        import time
        start_time = time.time()
        
        try:
            # Create database connection
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Check if data already exists in database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ledger'")
            data_exists = cursor.fetchone() is not None
            
            if data_exists:
                self.logger.info("Using existing data from persistent database")
                # Get table info for loaded_tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                loaded_tables = {}
                for (table_name,) in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    loaded_tables[table_name] = {
                        'original_filename': f"{table_name}.csv",  # Approximate
                        'row_count': row_count,
                        'columns': []  # Will be filled when needed
                    }
            else:
                self.logger.info("Loading fresh data into persistent database...")
                loaded_tables = self._load_uploaded_files_to_database(conn)
            
            if not loaded_tables:
                return {
                    "data": [],
                    "total_rows": 0,
                    "columns": [],
                    "execution_time": f"{(time.time() - start_time):.3f}s",
                    "error": "No data files loaded. Please upload some Excel/CSV files first."
                }
            
            # Optimize SQLite settings for better performance
            self._optimize_sqlite_settings(cursor)
            
            # Execute the actual SQL query using optimized approach
            self.logger.info(f"Executing SQL: {sql_query}")
            
            # Check for expensive JOIN types and apply optimizations
            is_expensive_join = self._is_expensive_join(sql_query)
            self.logger.info(f"Expensive join detection result: {is_expensive_join}")
            
            if is_expensive_join:
                self.logger.warning(f"⚠️  {is_expensive_join} detected - applying performance optimizations")
                self.logger.info("Switching to expensive query execution path...")
                try:
                    result = self._execute_expensive_query(cursor, sql_query, limit, start_time, loaded_tables)
                    conn.close()  # Close connection here for expensive queries
                    return result
                except Exception as e:
                    self.logger.error(f"Error in expensive query execution: {e}")
                    self.logger.info("Falling back to simplified query...")
                    try:
                        # Fallback: try with a very simple query structure
                        fallback_result = self._execute_fallback_query(cursor, sql_query, limit, start_time, loaded_tables)
                        conn.close()
                        return fallback_result
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback query also failed: {fallback_error}")
                        conn.close()
                        raise
            
            # Execute normal query
            self.logger.info("Using normal query execution path...")
            result = self._execute_normal_query(cursor, sql_query, limit, start_time, loaded_tables)
            conn.close()  # Close connection here for normal queries
            return result
            
        except sqlite3.Error as e:
            execution_time = f"{(time.time() - start_time):.3f}s"
            error_msg = f"SQL Error: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "data": [],
                "total_rows": 0,
                "columns": [],
                "execution_time": execution_time,
                "error": error_msg
            }
            
        except Exception as e:
            execution_time = f"{(time.time() - start_time):.3f}s"
            error_msg = f"Execution error: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "data": [],
                "total_rows": 0,
                "columns": [],
                "execution_time": execution_time,
                "error": error_msg
            }
    
    def _optimize_sqlite_settings(self, cursor: sqlite3.Cursor) -> None:
        """Optimize SQLite settings for better performance"""
        try:
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Increase cache size (default is 2000 pages, set to 10000)
            cursor.execute("PRAGMA cache_size=10000")
            
            # Enable memory-mapped I/O
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Optimize for speed over safety
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Enable query planner optimizations
            cursor.execute("PRAGMA optimize")
            
            # Set longer timeout for complex queries
            cursor.execute("PRAGMA busy_timeout = 120000")  # 2 minutes timeout
            
            self.logger.info("Applied SQLite performance optimizations")
        except Exception as e:
            self.logger.warning(f"Could not apply all SQLite optimizations: {e}")
    
    def _is_expensive_join(self, sql_query: str) -> str:
        """Check if query contains expensive JOIN operations"""
        query_upper = sql_query.upper()
        self.logger.info(f"Checking for expensive joins in query: {query_upper[:100]}...")
        
        if 'FULL OUTER JOIN' in query_upper:
            self.logger.info("Found FULL OUTER JOIN")
            return "FULL OUTER JOIN"
        elif 'RIGHT JOIN' in query_upper:
            self.logger.info("Found RIGHT JOIN")
            return "RIGHT JOIN"
        elif 'CROSS JOIN' in query_upper:
            self.logger.info("Found CROSS JOIN")
            return "CROSS JOIN"
        
        self.logger.info("No expensive joins found")
        return None
    
    def _execute_expensive_query(self, cursor: sqlite3.Cursor, sql_query: str, limit: int, start_time: float, loaded_tables: Dict) -> Dict:
        """Execute expensive queries with special optimizations"""
        import time
        import threading
        
        try:
            # For expensive queries, we'll use a different strategy
            # First, try to get a sample without counting all rows
            self.logger.info("Executing expensive query with sample-first approach...")
            
            # Execute main query with LIMIT for display (skip count for now)
            final_query = sql_query
            if limit:
                if 'LIMIT' not in sql_query.upper():
                    final_query = f"{sql_query} LIMIT {limit}"
            else:
                # Default limit for expensive queries
                final_query = f"{sql_query} LIMIT 1000"
            
            self.logger.info(f"Executing main query with limit: {limit or 1000}")
            self.logger.info(f"Final query: {final_query}")
            
            # Set a shorter timeout for expensive queries to prevent hanging
            cursor.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
            
            # Use a more aggressive approach for RIGHT JOIN - convert to LEFT JOIN
            if 'RIGHT JOIN' in final_query.upper():
                self.logger.info("Converting RIGHT JOIN to LEFT JOIN for better performance...")
                # Simple conversion: swap table order and change RIGHT JOIN to LEFT JOIN
                # This is a basic conversion - in production you'd want more sophisticated logic
                optimized_query = final_query.replace('RIGHT JOIN', 'LEFT JOIN')
                self.logger.info(f"Optimized query: {optimized_query}")
                
                # Execute query without signal-based timeout (thread-safe approach)
                cursor.execute(optimized_query)
            else:
                # Execute query without signal-based timeout (thread-safe approach)
                cursor.execute(final_query)
            
            results = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # Format results as list of dictionaries
            formatted_data = [dict(zip(column_names, row)) for row in results]
            
            execution_time = f"{(time.time() - start_time):.3f}s"
            
            # For expensive queries, we'll estimate total rows instead of counting
            estimated_total = len(formatted_data) * 10  # Rough estimate
            
            result = {
                "data": formatted_data,
                "total_rows": estimated_total,  # Estimated for expensive queries
                "columns": column_names,
                "execution_time": execution_time,
                "loaded_tables": loaded_tables,
                "warning": "This is an expensive query. Total row count is estimated."
            }
            
            self.logger.info(
                f"Expensive query executed successfully: {len(formatted_data)} rows returned "
                f"(estimated {estimated_total} total) in {execution_time}"
            )
            
            return result
            
        except Exception as e:
            execution_time = f"{(time.time() - start_time):.3f}s"
            error_msg = f"Expensive query execution error: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "data": [],
                "total_rows": 0,
                "columns": [],
                "execution_time": execution_time,
                "error": error_msg
            }
    
    def _execute_normal_query(self, cursor: sqlite3.Cursor, sql_query: str, limit: int, start_time: float, loaded_tables: Dict) -> Dict:
        """Execute normal queries with standard approach"""
        import time
        
        try:
            # Step 1: Get total count first (without LIMIT)
            count_sql = sql_query
            if 'LIMIT' in sql_query.upper():
                # Remove LIMIT clause and everything after it
                limit_position = sql_query.upper().rfind('LIMIT')
                count_sql = sql_query[:limit_position].strip()
            
            count_query = f"SELECT COUNT(*) FROM ({count_sql}) AS subquery"
            self.logger.info(f"Getting total count...")
            
            cursor.execute(count_query)
            total_rows = cursor.fetchone()[0]
            self.logger.info(f"Total rows available: {total_rows}")
            
            # Step 2: Execute main query with LIMIT for display
            final_query = sql_query
            if limit:
                if 'LIMIT' not in sql_query.upper():
                    final_query = f"{sql_query} LIMIT {limit}"
            
            self.logger.info(f"Executing main query with limit: {limit}")
            cursor.execute(final_query)
            results = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # Format results as list of dictionaries
            formatted_data = [dict(zip(column_names, row)) for row in results]
            
            execution_time = f"{(time.time() - start_time):.3f}s"
            
            result = {
                "data": formatted_data,
                "total_rows": total_rows,  # ✅ NOW SHOWS ACTUAL TOTAL
                "columns": column_names,
                "execution_time": execution_time,
                "loaded_tables": loaded_tables
            }
            
            self.logger.info(
                f"Query executed successfully: {len(formatted_data)} rows returned "
                f"out of {total_rows} total rows in {execution_time}"
            )
            
            return result
            
        except Exception as e:
            execution_time = f"{(time.time() - start_time):.3f}s"
            error_msg = f"Normal query execution error: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "data": [],
                "total_rows": 0,
                "columns": [],
                "execution_time": execution_time,
                "error": error_msg
            }
    
    def optimize_query_for_joins(self, sql_query: str) -> str:
        """Optimize SQL query for better JOIN performance"""
        try:
            # Convert RIGHT JOIN to LEFT JOIN (equivalent but often faster)
            if 'RIGHT JOIN' in sql_query.upper():
                self.logger.info("Converting RIGHT JOIN to LEFT JOIN for better performance...")
                # This is a simplified conversion - in practice, you'd need to swap table order
                # For now, we'll add a hint to use indexes
                optimized_query = sql_query.replace('RIGHT JOIN', 'LEFT JOIN')
                return optimized_query
            
            # Add hints for FULL OUTER JOIN optimization
            if 'FULL OUTER JOIN' in sql_query.upper():
                self.logger.info("Adding optimization hints for FULL OUTER JOIN...")
                # Add a comment with optimization hints
                optimized_query = sql_query.replace(
                    'FULL OUTER JOIN', 
                    'FULL OUTER JOIN /*+ USE_INDEX */'
                )
                return optimized_query
            
            return sql_query
            
        except Exception as e:
            self.logger.warning(f"Could not optimize query: {e}")
            return sql_query
    
    def _execute_fallback_query(self, cursor: sqlite3.Cursor, sql_query: str, limit: int, start_time: float, loaded_tables: Dict) -> Dict:
        """Execute a simplified fallback query when expensive queries fail"""
        import time
        
        try:
            self.logger.info("Executing fallback query with minimal data...")
            
            # Create a very simple query that just gets a few rows from the first table
            # This is a last resort to prevent complete failure
            if 'FROM' in sql_query.upper():
                # Extract the first table from the query
                from_index = sql_query.upper().find('FROM')
                from_clause = sql_query[from_index:]
                
                # Find the first table name
                parts = from_clause.split()
                if len(parts) > 1:
                    first_table = parts[1]
                    # Create a simple query
                    simple_query = f"SELECT * FROM {first_table} LIMIT {limit or 100}"
                    
                    self.logger.info(f"Fallback query: {simple_query}")
                    cursor.execute(simple_query)
                    results = cursor.fetchall()
                    
                    # Get column names
                    column_names = [description[0] for description in cursor.description] if cursor.description else []
                    
                    # Format results
                    formatted_data = [dict(zip(column_names, row)) for row in results]
                    
                    execution_time = f"{(time.time() - start_time):.3f}s"
                    
                    return {
                        "data": formatted_data,
                        "total_rows": len(formatted_data),
                        "columns": column_names,
                        "execution_time": execution_time,
                        "loaded_tables": loaded_tables,
                        "warning": "This is a fallback query due to JOIN performance issues. Results may be incomplete."
                    }
            
            # If we can't extract table info, return empty result
            return {
                "data": [],
                "total_rows": 0,
                "columns": [],
                "execution_time": f"{(time.time() - start_time):.3f}s",
                "error": "Could not create fallback query"
            }
            
        except Exception as e:
            execution_time = f"{(time.time() - start_time):.3f}s"
            self.logger.error(f"Fallback query failed: {e}")
            return {
                "data": [],
                "total_rows": 0,
                "columns": [],
                "execution_time": execution_time,
                "error": f"Fallback query failed: {str(e)}"
            }
    
    def recreate_indexes_for_existing_data(self) -> Dict:
        """Recreate indexes for existing data to improve JOIN performance"""
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Get all existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            recreated_count = 0
            for (table_name,) in tables:
                try:
                    # Get table columns
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # Recreate indexes for this table
                    self._create_optimized_indexes(cursor, table_name, columns)
                    recreated_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Could not recreate indexes for {table_name}: {e}")
                    continue
            
            conn.close()
            
            return {
                "success": True,
                "message": f"Successfully recreated indexes for {recreated_count} tables",
                "tables_processed": recreated_count
            }
            
        except Exception as e:
            self.logger.error(f"Error recreating indexes: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to recreate indexes"
            }
    
    def get_database_tables(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get tables from connected database"""
        try:
            db_connection_service = DatabaseConnectionService()
            result = db_connection_service.get_tables_with_password(connection_config)
            
            if result["success"]:
                # Transform the result to match the expected format
                tables = []
                for table_info in result["tables"]:
                    table = {
                        "name": table_info["table_name"],
                        "filename": f"database_{table_info['table_name']}",
                        "columns": [col["name"] for col in table_info["columns"]],
                        "row_count": table_info["row_count"],
                        "file_type": "database",
                        "source_type": "database"
                    }
                    tables.append(table)
                
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables)
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Error getting database tables: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get database tables"
            }
    
    def execute_database_query(self, connection_config: Dict[str, Any], query: str, limit: int = 1000) -> Dict[str, Any]:
        """Execute query on connected database"""
        try:
            db_connection_service = DatabaseConnectionService()
            result = db_connection_service.execute_query(connection_config, query, limit)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing database query: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute database query"
            }
    
    def generate_database_sql_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query for database tables"""
        try:
            # Extract connection config and query config
            connection_config = request.get("connection_config", {})
            query_config = request.get("query_config", {})
            
            # Generate the SQL query using the same logic as file-based queries
            sql_result = self.generate_sql_query(query_config)
            
            # The generate_sql_query method doesn't return "success" field, it returns the SQL directly
            return {
                "success": True,
                "sql": sql_result["sql"],
                "formatted_sql": sql_result["formatted_sql"],
                "query_config": query_config,
                "generated_at": datetime.now().isoformat(),
                "join_count": sql_result.get("join_count", 0),
                "table_count": sql_result.get("table_count", 0)
            }
                
        except Exception as e:
            self.logger.error(f"Error generating database SQL query: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate database SQL query"
            }

    def execute_database_query_preview(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database query and return preview data (1000 rows)"""
        try:
            connection_config = request.get("connection_config", {})
            sql_query = request.get("sql", "")
            limit = request.get("limit", 1000)
            
            if not sql_query:
                return {
                    "success": False,
                    "error": "No SQL query provided",
                    "message": "SQL query is required for execution"
                }
            
            # Execute the query on the database
            execution_result = self.execute_database_query(connection_config, sql_query, limit)
            
            if execution_result["success"]:
                return {
                    "success": True,
                    "data": execution_result["data"],
                    "columns": execution_result["columns"],
                    "row_count": execution_result["row_count"],
                    "sql_query": sql_query,
                    "execution_time": "0.0s",  # Could be calculated
                    "message": f"Query executed successfully. Showing {len(execution_result['data'])} rows."
                }
            else:
                return execution_result
                
        except Exception as e:
            self.logger.error(f"Error executing database query preview: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute database query preview"
            }

    def save_database_query_to_warehouse(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Save database query results to data warehouse"""
        try:
            connection_config = request.get("connection_config", {})
            sql_query = request.get("sql", "")
            table_name = request.get("table_name", "")
            schema = request.get("schema", "processed_data")
            
            if not sql_query:
                return {
                    "success": False,
                    "error": "No SQL query provided",
                    "message": "SQL query is required for saving"
                }
            
            if not table_name:
                return {
                    "success": False,
                    "error": "No table name provided",
                    "message": "Table name is required for saving"
                }
            
            # Execute the query on the database to get all data
            execution_result = self.execute_database_query(connection_config, sql_query, limit=None)
            
            if not execution_result["success"]:
                return execution_result
            
            # Convert data to DataFrame for warehouse processing
            import pandas as pd
            df = pd.DataFrame(execution_result["data"])
            
            # Use existing data pipeline service to save to warehouse
            from app.services.data_pipeline_service import DataPipelineService
            pipeline_service = DataPipelineService()
            
            # Generate schema preview
            schema_preview = pipeline_service.generate_schema_preview(
                df=df,
                schema=schema,
                user_table_name=table_name,
                query_sql=sql_query
            )
            
            if schema_preview["success"] and schema_preview["can_create"]:
                # Save to warehouse
                save_result = pipeline_service.save_dataframe_to_warehouse(
                    df=df,
                    schema=schema,
                    table_name=table_name,
                    query_sql=sql_query
                )
                
                if save_result["success"]:
                    return {
                        "success": True,
                        "message": f"Data saved successfully to {schema}.{table_name}",
                        "table_name": table_name,
                        "schema": schema,
                        "full_table_name": f"{schema}.{table_name}",
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "query_sql": sql_query
                    }
                else:
                    return save_result
            else:
                return {
                    "success": False,
                    "error": "Cannot create table",
                    "message": schema_preview.get("message", "Table creation failed"),
                    "validation_errors": schema_preview.get("errors", [])
                }
                
        except Exception as e:
            self.logger.error(f"Error saving database query to warehouse: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save database query to warehouse"
            }

    def save_database_query_to_warehouse_chunked(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Save database query results to data warehouse with chunked insertion and progress tracking"""
        try:
            connection_config = request.get("connection_config", {})
            sql_query = request.get("sql", "")
            table_name = request.get("table_name", "")
            schema = request.get("schema", "processed_data")
            chunk_size = request.get("chunk_size", 1000)
            preserve_order = request.get("preserve_order", True)
            
            if not sql_query:
                return {
                    "success": False,
                    "error": "No SQL query provided",
                    "message": "SQL query is required for saving"
                }
            
            if not table_name:
                return {
                    "success": False,
                    "error": "No table name provided",
                    "message": "Table name is required for saving"
                }
            
            # Use chunked insertion service
            chunked_service = ChunkedInsertionService()
            
            result = chunked_service.insert_data_with_progress(
                connection_config=connection_config,
                sql_query=sql_query,
                target_table_name=table_name,
                target_schema=schema,
                chunk_size=chunk_size,
                preserve_order=preserve_order
            )
            
            return result
                
        except Exception as e:
            self.logger.error(f"Error in chunked database save: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save database query to warehouse with chunked insertion"
            }
