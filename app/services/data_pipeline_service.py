import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from .postgresql_service import PostgreSQLService

class DataPipelineService:
    """Service for transferring query results from SQLite to PostgreSQL"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.postgres_service = PostgreSQLService()
    
    def generate_table_name(self, prefix: str = "query_result") -> str:
        """Generate unique table name for storing query results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"{prefix}_{timestamp}"
        self.logger.info(f"Generated table name: {table_name}")
        return table_name
    
    def suggest_table_names(self, query_sql: str = "", columns: List[str] = None) -> List[str]:
        """
        Generate smart table name suggestions based on query content and columns.
        
        This function analyzes the SQL query and column names to suggest meaningful
        business-friendly table names that users can choose from or modify.
        
        Args:
            query_sql (str): The SQL query that was executed (optional)
            columns (List[str]): List of column names in the result (optional)
            
        Returns:
            List[str]: List of suggested table names (3-5 suggestions)
        """
        try:
            suggestions = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            # Analyze query content for smart suggestions
            query_lower = query_sql.lower() if query_sql else ""
            
            # Pattern 1: Based on table names in query
            if "ledger" in query_lower and "customer" in query_lower:
                suggestions.extend([
                    f"ledger_customer_analysis_{timestamp}",
                    "customer_ledger_report", 
                    "customer_transaction_summary"
                ])
            elif "ledger" in query_lower and "detail" in query_lower:
                suggestions.extend([
                    f"ledger_detail_join_{timestamp}",
                    "ledger_reconciliation",
                    "transaction_details"
                ])
            elif "sales" in query_lower:
                suggestions.extend([
                    f"sales_report_{timestamp}",
                    "sales_analysis",
                    "revenue_summary"
                ])
            elif "customer" in query_lower:
                suggestions.extend([
                    f"customer_data_{timestamp}",
                    "customer_analysis", 
                    "customer_summary"
                ])
                
            # Pattern 2: Based on column patterns
            if columns:
                col_str = " ".join(columns).lower()
                
                if "amount" in col_str and "voucher" in col_str:
                    suggestions.append("financial_transactions")
                if "branch" in col_str and "code" in col_str:
                    suggestions.append("branch_analysis")  
                if "date" in col_str or "time" in col_str:
                    suggestions.append("time_series_data")
                    
            # Pattern 3: Based on JOIN operations
            if "join" in query_lower:
                join_count = query_lower.count("join")
                if join_count == 1:
                    suggestions.append("joined_data_analysis")
                elif join_count > 1:
                    suggestions.append("multi_table_report")
                    
            # Pattern 4: Time-based suggestions
            current_month = datetime.now().strftime("%B").lower()
            current_year = datetime.now().strftime("%Y")
            suggestions.extend([
                f"{current_month}_{current_year}_report",
                f"quarterly_analysis_{current_year}",
                "monthly_summary"
            ])
            
            # Remove duplicates and limit to 5 suggestions
            unique_suggestions = list(dict.fromkeys(suggestions))[:5]
            
            # Add fallback if no smart suggestions found
            if not unique_suggestions:
                unique_suggestions = [
                    f"query_result_{timestamp}",
                    "data_analysis",
                    "report_data"
                ]
                
            self.logger.info(f"Generated {len(unique_suggestions)} table name suggestions")
            return unique_suggestions
            
        except Exception as e:
            self.logger.error(f"❌ Error generating table name suggestions: {str(e)}")
            return [f"query_result_{datetime.now().strftime('%Y%m%d_%H%M')}"]
    
    def check_table_exists(self, schema: str, table_name: str) -> Dict[str, Any]:
        """
        Check if a table already exists in PostgreSQL database.
        
        This function connects to PostgreSQL and checks if the specified table
        already exists in the given schema. This prevents duplicate table creation.
        
        Args:
            schema (str): PostgreSQL schema name (e.g., 'processed_data')
            table_name (str): Table name to check
            
        Returns:
            Dict containing:
            - 'exists': Boolean indicating if table exists
            - 'full_name': Full table name (schema.table_name)
            - 'message': User-friendly message
            - 'error': Error message if connection failed
        """
        try:
            # Use PostgreSQL service to check table existence
            with self.postgres_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # Query to check if table exists in the specified schema
                check_query = """
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                );
                """
                
                cursor.execute(check_query, (schema, table_name))
                table_exists = cursor.fetchone()[0]
                
                full_table_name = f"{schema}.{table_name}"
                
                result = {
                    'exists': table_exists,
                    'full_name': full_table_name,
                    'schema': schema,
                    'table_name': table_name,
                    'message': f"Table '{full_table_name}' already exists" if table_exists else f"Table '{full_table_name}' is available",
                    'success': True
                }
                
                self.logger.info(f"Table existence check: {full_table_name} -> {'EXISTS' if table_exists else 'AVAILABLE'}")
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error checking table existence: {str(e)}")
            return {
                'exists': False,  # Assume doesn't exist if we can't check
                'full_name': f"{schema}.{table_name}",
                'schema': schema,
                'table_name': table_name,
                'message': f"Could not verify table existence: {str(e)}",
                'error': str(e),
                'success': False
            }

    def validate_table_name(self, table_name: str) -> Dict[str, Any]:
        """
        Validate table name according to PostgreSQL rules and best practices.
        
        This function checks if a table name is valid for PostgreSQL and provides
        helpful error messages and suggestions for fixing invalid names.
        
        Args:
            table_name (str): The table name to validate
            
        Returns:
            Dict containing:
            - 'is_valid': Boolean indicating if name is valid
            - 'errors': List of validation error messages
            - 'warnings': List of warnings (valid but not recommended)
            - 'suggestions': List of corrected name suggestions
        """
        try:
            errors = []
            warnings = []
            suggestions = []
            
            # PostgreSQL reserved words (common ones)
            RESERVED_WORDS = {
                'table', 'select', 'from', 'where', 'insert', 'update', 'delete',
                'create', 'drop', 'alter', 'index', 'primary', 'key', 'foreign',
                'references', 'constraint', 'null', 'not', 'default', 'check',
                'user', 'group', 'order', 'by', 'having', 'union', 'all', 'distinct'
            }
            
            # Rule 1: Length check
            if len(table_name) == 0:
                errors.append("Table name cannot be empty")
            elif len(table_name) > 63:
                errors.append("Table name too long (max 63 characters)")
                suggestions.append(table_name[:60] + "...")
                
            # Rule 2: Character validation
            if table_name:
                # Must start with letter or underscore
                if not (table_name[0].isalpha() or table_name[0] == '_'):
                    errors.append("Table name must start with a letter or underscore")
                    suggestions.append(f"tbl_{table_name}")
                
                # Can only contain letters, numbers, underscores
                import re
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                    errors.append("Table name can only contain letters, numbers, and underscores")
                    # Suggest cleaned version
                    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
                    clean_name = re.sub(r'_+', '_', clean_name)  # Remove multiple underscores
                    suggestions.append(clean_name)
            
            # Rule 3: Reserved word check
            if table_name.lower() in RESERVED_WORDS:
                errors.append(f"'{table_name}' is a PostgreSQL reserved word")
                suggestions.extend([
                    f"tbl_{table_name}",
                    f"{table_name}_data", 
                    f"user_{table_name}"
                ])
            
            # Rule 4: Best practice warnings
            if table_name.isupper():
                warnings.append("Consider using lowercase (PostgreSQL convention)")
                suggestions.append(table_name.lower())
                
            if len(table_name.split('_')) > 5:
                warnings.append("Very long compound name - consider shorter alternative")
                
            if table_name.startswith('_'):
                warnings.append("Names starting with underscore are not recommended")
                suggestions.append(table_name[1:])
                
            # Rule 5: Check for existing table (would need DB connection)
            # This would be implemented when we integrate with PostgreSQL
            
            is_valid = len(errors) == 0
            
            validation_result = {
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'suggestions': list(set(suggestions)),  # Remove duplicates
                'original_name': table_name,
                'message': 'Valid table name' if is_valid else f'{len(errors)} validation errors found'
            }
            
            self.logger.debug(f"Table name validation: '{table_name}' -> {'✅ Valid' if is_valid else '❌ Invalid'}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"❌ Error validating table name: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'suggestions': [],
                'original_name': table_name,
                'message': 'Validation failed due to error'
            }
    
    def map_pandas_to_postgres_type(self, pandas_dtype: str, sample_data: list = None) -> str:
        """Convert pandas data types to PostgreSQL data types with intelligent VARCHAR sizing"""
        dtype_str = str(pandas_dtype)
        
        # For object types, analyze sample data to determine appropriate VARCHAR length
        if dtype_str == 'object' and sample_data:
            max_length = 0
            for val in sample_data:
                if val is not None:
                    val_str = str(val)
                    max_length = max(max_length, len(val_str))
            
            # Choose appropriate VARCHAR size based on data length
            if max_length <= 50:
                return 'VARCHAR(50)'
            elif max_length <= 100:
                return 'VARCHAR(100)'
            elif max_length <= 255:
                return 'VARCHAR(255)'
            elif max_length <= 500:
                return 'VARCHAR(500)'
            else:
                return 'TEXT'  # Use TEXT for very long strings
        
        # Standard type mapping
        type_mapping = {
            'int64': 'BIGINT',
            'int32': 'INTEGER', 
            'int16': 'SMALLINT',
            'float64': 'DOUBLE PRECISION',
            'float32': 'REAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP',
            'object': 'TEXT',  # Use TEXT for all string data to avoid length issues
        }
        
        postgres_type = type_mapping.get(dtype_str, 'TEXT')
        self.logger.debug(f"Mapped {dtype_str} -> {postgres_type}")
        return postgres_type

    def _extract_source_database_schema(self, connection_config: dict, query_sql: str) -> dict:
        """
        Extract real schema information from source database tables used in the query
        
        Args:
            connection_config: Database connection configuration
            query_sql: SQL query to analyze
            
        Returns:
            Dict mapping column names to their real schema information
        """
        try:
            from .database_connection_service import DatabaseConnectionService
            
            db_service = DatabaseConnectionService()
            schema_info = {}
            
            # Parse the SQL query to extract table names
            table_names = self._extract_table_names_from_query(query_sql)
            
            self.logger.info(f"🔍 Extracting schema from tables: {table_names}")
            
            for table_name in table_names:
                # Get schema for each table
                table_schema = db_service.get_table_schema(connection_config, table_name, 'public')
                
                if table_schema.get('success'):
                    for column in table_schema.get('columns', []):
                        column_name = column['name'].lower()
                        
                        # Map source database type to PostgreSQL type
                        postgres_type = self._map_source_type_to_postgres(
                            column['data_type'],
                            column.get('max_length'),
                            column.get('precision'),
                            column.get('scale')
                        )
                        
                        schema_info[column_name] = {
                            'source_type': column['data_type'],
                            'postgres_type': postgres_type,
                            'max_length': column.get('max_length'),
                            'precision': column.get('precision'),
                            'scale': column.get('scale'),
                            'nullable': column['nullable'],
                            'table': table_name
                        }
                        
                        self.logger.debug(f"Extracted schema: {column_name} -> {postgres_type}")
            
            return schema_info
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting source database schema: {str(e)}")
            return {}

    def _extract_table_names_from_query(self, query_sql: str) -> list:
        """
        Extract table names from SQL query
        
        Args:
            query_sql: SQL query string
            
        Returns:
            List of table names found in the query
        """
        import re
        
        # Simple regex to find table names after FROM and JOIN keywords
        # This is a basic implementation - could be enhanced with proper SQL parsing
        table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(table_pattern, query_sql.upper())
        
        # Convert back to lowercase to match actual PostgreSQL table names
        matches = [match.lower() for match in matches]
        
        # Remove duplicates and return
        return list(set(matches))

    def _map_source_type_to_postgres(self, source_type: str, max_length: int = None, 
                                   precision: int = None, scale: int = None) -> str:
        """
        Map source database types to PostgreSQL types
        
        Args:
            source_type: Source database data type
            max_length: Maximum length for character types
            precision: Precision for numeric types
            scale: Scale for numeric types
            
        Returns:
            PostgreSQL data type string
        """
        source_type_lower = source_type.lower()
        
        # Character types
        if 'varchar' in source_type_lower or 'char' in source_type_lower:
            if max_length:
                return f"VARCHAR({max_length})"
            else:
                return "VARCHAR(255)"
        elif 'text' in source_type_lower:
            return "TEXT"
        
        # Numeric types
        elif 'int' in source_type_lower:
            if 'bigint' in source_type_lower:
                return "BIGINT"
            elif 'smallint' in source_type_lower:
                return "SMALLINT"
            else:
                return "INTEGER"
        elif 'decimal' in source_type_lower or 'numeric' in source_type_lower:
            if precision and scale:
                return f"DECIMAL({precision},{scale})"
            elif precision:
                return f"DECIMAL({precision},2)"
            else:
                return "DECIMAL(10,2)"
        elif 'float' in source_type_lower or 'double' in source_type_lower:
            return "DOUBLE PRECISION"
        elif 'real' in source_type_lower:
            return "REAL"
        
        # Date/Time types
        elif 'date' in source_type_lower:
            return "DATE"
        elif 'timestamp' in source_type_lower or 'datetime' in source_type_lower:
            return "TIMESTAMP"
        elif 'time' in source_type_lower:
            return "TIME"
        
        # Boolean types
        elif 'bool' in source_type_lower:
            return "BOOLEAN"
        
        # Default fallback
        else:
            return "TEXT"
    
    def generate_schema_preview(self, df: pd.DataFrame, schema: str = "processed_data", 
                               user_table_name: str = None, query_sql: str = "", 
                               is_database_mode: bool = False, connection_config: dict = None) -> Dict[str, Any]:
        """
        Generate a preview of the CREATE TABLE statement for user review and editing.
        
        This function analyzes a pandas DataFrame and creates a schema preview that includes:
        1. Auto-detected column types from pandas
        2. Suggested PostgreSQL types  
        3. User-provided table name validation and duplicate checking
        4. Editable CREATE TABLE SQL
        5. Column-by-column breakdown for user review
        
        Args:
            df (pd.DataFrame): The data to analyze
            schema (str): PostgreSQL schema name (default: 'processed_data')
            user_table_name (str): User-provided table name (REQUIRED - no auto-generation)
            query_sql (str): Original SQL query for reference
            
        Returns:
            Dict containing:
            - 'table_name': User-provided table name
            - 'schema': Schema name
            - 'columns': List of column info for editing
            - 'create_sql': Editable CREATE TABLE statement
            - 'total_rows': Number of rows that will be inserted
            - 'name_validation': Validation result for user table name
            - 'table_exists': Table existence check result
            - 'can_create': Boolean indicating if table can be created
        """
        try:
            self.logger.info(f"🔍 Generating schema preview for {len(df)} rows, {len(df.columns)} columns")
            
            # Check if user provided table name
            if not user_table_name:
                return {
                    'success': False,
                    'error': 'Table name is required',
                    'message': 'Please provide a table name. Table names are not auto-generated.'
                }
            
            # Validate the user-provided table name
            name_validation = self.validate_table_name(user_table_name)
            
            # Check if table already exists in PostgreSQL
            table_exists_check = self.check_table_exists(schema, user_table_name)
            
            # Determine if we can create the table
            can_create_table = (
                name_validation['is_valid'] and 
                not table_exists_check['exists'] and 
                table_exists_check['success']
            )
            
            # Analyze each column and prepare for user review
            column_analysis = []
            
            # Extract real schema from source database if in database mode
            source_schema_info = {}
            if is_database_mode and connection_config and query_sql:
                source_schema_info = self._extract_source_database_schema(connection_config, query_sql)
                self.logger.info(f"🔍 Extracted schema from source database: {len(source_schema_info)} columns")
            
            for column_name, dtype in df.dtypes.items():
                # Get auto-detected type
                detected_type = str(dtype)
                
                # Clean column name for PostgreSQL
                clean_column_name = column_name.replace(' ', '_').replace('-', '_').lower()
                
                # Remove table prefix for schema matching (e.g., "ledger.lg_voucher_no" -> "lg_voucher_no")
                if '.' in clean_column_name:
                    clean_column_name = clean_column_name.split('.')[-1]
                
                # Analyze data for better suggestions (peek at actual values)
                # Convert numpy types to native Python types for JSON serialization
                sample_values = []
                for val in df[column_name].dropna().head(5):
                    if hasattr(val, 'item'):  # numpy scalar
                        sample_values.append(val.item())
                    else:
                        sample_values.append(val)
                
                # Use real schema from source database if available, otherwise use pandas mapping
                if clean_column_name in source_schema_info:
                    suggested_type = source_schema_info[clean_column_name]['postgres_type']
                    self.logger.debug(f"Using real schema for '{column_name}': {suggested_type}")
                else:
                    suggested_type = self.map_pandas_to_postgres_type(dtype, sample_values)
                    self.logger.debug(f"Using pandas mapping for '{column_name}': {suggested_type}")
                
                column_info = {
                    'original_name': column_name,
                    'clean_name': clean_column_name,
                    'detected_type': detected_type,
                    'suggested_pg_type': suggested_type,
                    'sample_values': sample_values,
                    'null_count': int(df[column_name].isnull().sum()),  # Convert numpy int to Python int
                    'is_nullable': bool(df[column_name].isnull().any())  # Convert numpy bool to Python bool
                }
                
                column_analysis.append(column_info)
                self.logger.debug(f"Column '{column_name}': {detected_type} -> {suggested_type}")
            
            # Generate the CREATE TABLE SQL for preview (only if table can be created)
            if can_create_table:
                create_sql = self._generate_create_table_sql(column_analysis, schema, user_table_name)
                status_message = f"Schema preview ready - table can be created with {len(df):,} rows"
            else:
                create_sql = f"-- Cannot create table due to validation or existence issues\n-- {table_exists_check['message']}"
                status_message = "Cannot create table - see validation errors"
            
            preview_data = {
                'success': True,
                'table_name': user_table_name,
                'name_validation': name_validation,
                'table_exists': table_exists_check,
                'can_create': can_create_table,
                'schema': schema,
                'full_table_name': f"{schema}.{user_table_name}",
                'columns': column_analysis,
                'create_sql': create_sql,
                'total_rows': int(len(df)),  # Ensure it's a Python int
                'total_columns': int(len(df.columns)),  # Ensure it's a Python int
                'query_sql': query_sql,
                'message': status_message
            }
            
            self.logger.info(f"✅ Schema preview generated: {schema}.{user_table_name} (Can create: {can_create_table})")
            return preview_data
            
        except Exception as e:
            self.logger.error(f"❌ Error generating schema preview: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate schema preview'
            }
    
    def _generate_create_table_sql(self, column_analysis: List[Dict], schema: str, table_name: str) -> str:
        """
        Generate CREATE TABLE SQL statement from column analysis.
        
        This helper function takes the column analysis and creates a properly formatted
        CREATE TABLE statement that users can review and edit.
        
        Args:
            column_analysis (List[Dict]): Column information from generate_schema_preview
            schema (str): PostgreSQL schema name
            table_name (str): Table name
            
        Returns:
            str: Formatted CREATE TABLE SQL statement
        """
        try:
            # Build column definitions
            column_definitions = []
            
            for col in column_analysis:
                # Format: column_name DATA_TYPE
                nullable = "NULL" if col['is_nullable'] else "NOT NULL"
                col_def = f"    {col['clean_name']} {col['suggested_pg_type']}"
                column_definitions.append(col_def)
            
            # Join all column definitions
            columns_sql = ",\n".join(column_definitions)
            
            # Create the complete SQL statement
            create_sql = f"""CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
    id BIGSERIAL PRIMARY KEY,
{columns_sql},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
            
            return create_sql
            
        except Exception as e:
            self.logger.error(f"❌ Error generating CREATE TABLE SQL: {str(e)}")
            return f"-- Error generating SQL: {str(e)}"

    def create_table_and_insert_data(self, query_sql: str, schema: str, table_name: str, 
                                   column_corrections: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Create PostgreSQL table with user-corrected schema and insert all data.
        
        This function:
        1. Executes the original SQL query to get ALL data (not limited)
        2. Creates PostgreSQL table with user's corrected column types
        3. Inserts all data in batches with progress tracking
        4. Returns detailed results and statistics
        
        Args:
            query_sql (str): Original SQL query to execute
            schema (str): PostgreSQL schema name
            table_name (str): User-provided table name
            column_corrections (Dict[str, str]): User's column type corrections
            
        Returns:
            Dict containing creation results, insertion statistics, and timing info
        """
        try:
            from .sql_query_service import SQLQueryService
            import time
            
            self.logger.info(f"🏗️ Starting table creation: {schema}.{table_name}")
            start_time = time.time()
            
            # Step 1: Execute SQL query to get ALL data (no limit)
            self.logger.info("📊 Executing SQL query to get all data...")
            sql_service = SQLQueryService()
            query_result = sql_service.execute_raw_sql(query_sql, limit=None)  # Get ALL data
            
            if not query_result or 'data' not in query_result:
                return {
                    'success': False,
                    'error': 'Failed to execute SQL query',
                    'message': 'Could not retrieve data for insertion'
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(query_result['data'], columns=query_result['columns'])
            total_rows = len(df)
            
            self.logger.info(f"📋 Retrieved {total_rows:,} rows for insertion")
            
            # Step 2: Apply user's column type corrections
            if column_corrections:
                self.logger.info(f"🔧 Applying {len(column_corrections)} column type corrections")
            
            # Step 3: Create table with corrected schema
            with self.postgres_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build CREATE TABLE statement with user corrections
                column_defs = []
                for col_name in df.columns:
                    clean_name = col_name.replace(' ', '_').replace('-', '_').lower()
                    
                    # Use user correction if provided, otherwise auto-detect
                    if column_corrections and clean_name in column_corrections:
                        pg_type = column_corrections[clean_name]
                        self.logger.debug(f"Using user correction: {clean_name} -> {pg_type}")
                    else:
                        # Get sample data for intelligent VARCHAR sizing
                        sample_data = df[col_name].dropna().head(5).tolist()
                        pg_type = self.map_pandas_to_postgres_type(df[col_name].dtype, sample_data)
                        self.logger.debug(f"Using auto-detected: {clean_name} -> {pg_type}")
                    
                    column_defs.append(f"    {clean_name} {pg_type}")
                
                columns_sql = ",\n".join(column_defs)
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                    id BIGSERIAL PRIMARY KEY,
                {columns_sql},
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                self.logger.info(f"🔨 Creating table: {schema}.{table_name}")
                cursor.execute(create_sql)
                conn.commit()
                
                table_creation_time = time.time() - start_time
                self.logger.info(f"✅ Table created in {table_creation_time:.2f}s")
                
                # Step 4: Insert data in batches
                self.logger.info(f"📥 Starting data insertion: {total_rows:,} rows")
                
                # Prepare column names for INSERT
                clean_columns = [col.replace(' ', '_').replace('-', '_').lower() for col in df.columns]
                columns_list = ", ".join(clean_columns)
                placeholders = ", ".join(["%s"] * len(clean_columns))
                
                insert_sql = f"""
                INSERT INTO {schema}.{table_name} ({columns_list}) 
                VALUES ({placeholders})
                """
                
                # Insert in smaller batches to prevent timeout and memory issues
                batch_size = 500
                total_batches = (total_rows + batch_size - 1) // batch_size
                inserted_rows = 0
                
                self.logger.info(f"📦 Inserting in {total_batches} batches of {batch_size} rows")
                
                for batch_num in range(total_batches):
                    batch_start = batch_num * batch_size
                    batch_end = min((batch_num + 1) * batch_size, total_rows)
                    batch_df = df.iloc[batch_start:batch_end]
                    
                    # Convert DataFrame rows to list of tuples
                    batch_data = []
                    for _, row in batch_df.iterrows():
                        # Convert numpy types to Python types
                        row_data = []
                        for val in row:
                            if hasattr(val, 'item'):  # numpy scalar
                                row_data.append(val.item())
                            elif pd.isna(val):  # Handle NaN values
                                row_data.append(None)
                            else:
                                row_data.append(val)
                        batch_data.append(tuple(row_data))
                    
                    # Execute batch insert
                    cursor.executemany(insert_sql, batch_data)
                    conn.commit()
                    
                    inserted_rows += len(batch_data)
                    progress = (batch_num + 1) / total_batches * 100
                    
                    self.logger.info(f"📊 Progress: {progress:.1f}% ({inserted_rows:,}/{total_rows:,} rows)")
                
                total_time = time.time() - start_time
                
                # Step 5: Verify insertion
                cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                final_count = cursor.fetchone()[0]
                
                self.logger.info(f"🎉 Data insertion completed!")
                self.logger.info(f"📊 Final verification: {final_count:,} rows in table")
                
                return {
                    'success': True,
                    'table_name': table_name,
                    'schema': schema,
                    'full_table_name': f"{schema}.{table_name}",
                    'total_rows_inserted': int(final_count),
                    'expected_rows': int(total_rows),
                    'insertion_successful': final_count == total_rows,
                    'total_time_seconds': round(total_time, 2),
                    'table_creation_time': round(table_creation_time, 2),
                    'insertion_time': round(total_time - table_creation_time, 2),
                    'rows_per_second': round(total_rows / (total_time - table_creation_time), 0),
                    'batches_processed': total_batches,
                    'batch_size': batch_size,
                    'create_sql': create_sql.strip(),
                    'message': f"Successfully created table and inserted {final_count:,} rows in {total_time:.1f}s"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error in table creation and data insertion: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Table creation failed: {str(e)}'
            }

    def create_table_from_dataframe(self, df: pd.DataFrame, schema: str, table_name: str) -> bool:
        """Create PostgreSQL table based on pandas DataFrame structure"""
        try:
            columns = []
            for column_name, dtype in df.dtypes.items():
                pg_type = self.map_pandas_to_postgres_type(dtype)
                clean_name = column_name.replace(' ', '_').replace('-', '_')
                columns.append(f"{clean_name} {pg_type}")
            
            columns_sql = ",\n    ".join(columns)
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                id BIGSERIAL PRIMARY KEY,
                {columns_sql},
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
            
            with self.postgres_service.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_sql)
                conn.commit()
                
                self.logger.info(f"✅ Created table: {schema}.{table_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create table {schema}.{table_name}: {e}")
            return False
