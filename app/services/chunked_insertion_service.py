import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import time
from sqlalchemy import create_engine, text
from app.services.database_connection_service import DatabaseConnectionService
from app.services.data_pipeline_service import DataPipelineService

logger = logging.getLogger(__name__)

class ChunkedInsertionService:
    """Service for chunked data insertion with progress tracking and transaction safety"""
    
    def __init__(self):
        self.logger = logger
        self.db_connection_service = DatabaseConnectionService()
        self.pipeline_service = DataPipelineService()
        
    def insert_data_with_progress(
        self,
        connection_config: Dict[str, Any],
        sql_query: str,
        target_table_name: str,
        target_schema: str = "processed_data",
        chunk_size: int = 1000,
        progress_callback: Optional[Callable] = None,
        preserve_order: bool = True
    ) -> Dict[str, Any]:
        """
        Insert data in chunks with progress tracking and transaction safety
        
        Args:
            connection_config: Database connection configuration
            sql_query: SQL query to execute on source database
            target_table_name: Name of target table in data warehouse
            target_schema: Schema name in data warehouse
            chunk_size: Number of rows per chunk
            progress_callback: Function to call with progress updates
            preserve_order: Whether to preserve row order (insert in descending order)
        """
        try:
            # Step 1: Get total row count
            self.logger.info("Getting total row count...")
            # Remove any existing LIMIT clause for count query
            base_query = sql_query
            if "LIMIT" in base_query.upper():
                base_query = base_query.rsplit("LIMIT", 1)[0].strip()
            
            count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
            count_result = self.db_connection_service.execute_query(connection_config, count_query, 1)
            
            if not count_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to get row count",
                    "message": count_result.get("message", "Unknown error")
                }
            
            total_rows = count_result["data"][0]["total"]
            self.logger.info(f"Total rows to insert: {total_rows}")
            
            # Step 2: Get sample data to determine schema
            self.logger.info("Getting sample data for schema analysis...")
            # Use the base query (without LIMIT) and add our own LIMIT
            sample_query = f"{base_query} LIMIT 100"
            sample_result = self.db_connection_service.execute_query(connection_config, sample_query, 100)
            
            if not sample_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to get sample data",
                    "message": sample_result.get("message", "Unknown error")
                }
            
            # Step 3: Extract exact schema from source database
            self.logger.info("Extracting exact schema from source database...")
            
            # Get the first table from the query to extract its schema
            # This is a simplified approach - in a real scenario, you'd parse the SQL query
            # to identify which tables are being queried
            schema_info = self._extract_schema_from_query(connection_config, sql_query)
            
            if not schema_info["success"]:
                return {
                    "success": False,
                    "error": "Failed to extract schema",
                    "message": schema_info.get("message", "Schema extraction failed")
                }
            
            # Step 4: Create table in data warehouse with exact schema
            self.logger.info(f"Creating table {target_schema}.{target_table_name} with exact schema...")
            create_table_result = self._create_table_with_exact_schema(
                schema_info=schema_info,
                target_schema=target_schema,
                table_name=target_table_name
            )
            
            if not create_table_result:
                return {
                    "success": False,
                    "error": "Failed to create table",
                    "message": "Table creation failed"
                }
            
            # Step 5: Insert data in chunks with transaction safety
            self.logger.info("Starting chunked data insertion...")
            return self._insert_data_in_chunks(
                connection_config=connection_config,
                sql_query=sql_query,
                target_schema=target_schema,
                target_table_name=target_table_name,
                total_rows=total_rows,
                chunk_size=chunk_size,
                progress_callback=progress_callback,
                preserve_order=preserve_order
            )
            
        except Exception as e:
            self.logger.error(f"Error in chunked insertion: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to insert data"
            }
    
    def _insert_data_in_chunks(
        self,
        connection_config: Dict[str, Any],
        sql_query: str,
        target_schema: str,
        target_table_name: str,
        total_rows: int,
        chunk_size: int,
        progress_callback: Optional[Callable],
        preserve_order: bool
    ) -> Dict[str, Any]:
        """Insert data in chunks with progress tracking"""
        
        inserted_rows = 0
        start_time = time.time()
        
        try:
            # Get PostgreSQL connection for data warehouse
            from app.services.postgresql_service import PostgreSQLService
            postgres_service = PostgreSQLService()
            
            # Remove any existing LIMIT clause from the base query
            base_query = sql_query
            if "LIMIT" in base_query.upper():
                base_query = base_query.rsplit("LIMIT", 1)[0].strip()
            
            # Calculate offset for descending order if needed
            offset = 0
            
            while inserted_rows < total_rows:
                # Calculate current chunk size
                remaining_rows = total_rows - inserted_rows
                current_chunk_size = min(chunk_size, remaining_rows)
                
                # Build query for current chunk
                if preserve_order:
                    # For descending order, we need to reverse the order
                    chunk_query = f"""
                        SELECT * FROM (
                            {base_query}
                        ) as ordered_data
                        ORDER BY row_number() OVER (ORDER BY (SELECT NULL)) DESC
                        LIMIT {current_chunk_size} OFFSET {offset}
                    """
                else:
                    # Use base query and add LIMIT/OFFSET
                    chunk_query = f"{base_query} LIMIT {current_chunk_size} OFFSET {offset}"
                
                # Execute chunk query
                chunk_result = self.db_connection_service.execute_query(
                    connection_config, 
                    chunk_query,
                    current_chunk_size
                )
                
                if not chunk_result["success"]:
                    # Rollback: delete all inserted data
                    self.logger.error(f"Chunk failed, rolling back...")
                    self._rollback_insertion(target_schema, target_table_name)
                    return {
                        "success": False,
                        "error": "Chunk insertion failed",
                        "message": chunk_result.get("message", "Unknown error"),
                        "inserted_rows": inserted_rows,
                        "total_rows": total_rows
                    }
                
                # Convert chunk data to DataFrame
                chunk_df = pd.DataFrame(chunk_result["data"])
                
                if len(chunk_df) == 0:
                    break
                
                # Insert chunk into data warehouse
                insert_result = self._insert_dataframe_chunk(
                    df=chunk_df,
                    schema=target_schema,
                    table_name=target_table_name
                )
                
                if not insert_result["success"]:
                    # Rollback: delete all inserted data
                    self.logger.error(f"Insertion failed, rolling back...")
                    self._rollback_insertion(target_schema, target_table_name)
                    return {
                        "success": False,
                        "error": "Data warehouse insertion failed",
                        "message": insert_result.get("message", "Unknown error"),
                        "inserted_rows": inserted_rows,
                        "total_rows": total_rows
                    }
                
                # Update progress
                inserted_rows += len(chunk_df)
                offset += current_chunk_size
                
                # Calculate progress
                progress_percentage = (inserted_rows / total_rows) * 100
                elapsed_time = time.time() - start_time
                
                # Estimate remaining time
                if inserted_rows > 0:
                    estimated_total_time = (elapsed_time / inserted_rows) * total_rows
                    remaining_time = estimated_total_time - elapsed_time
                else:
                    remaining_time = 0
                
                # Call progress callback if provided
                if progress_callback:
                    progress_data = {
                        "inserted_rows": inserted_rows,
                        "total_rows": total_rows,
                        "progress_percentage": round(progress_percentage, 2),
                        "elapsed_time": round(elapsed_time, 2),
                        "remaining_time": round(remaining_time, 2),
                        "chunk_size": current_chunk_size,
                        "rows_per_second": round(inserted_rows / elapsed_time, 2) if elapsed_time > 0 else 0
                    }
                    progress_callback(progress_data)
                
                self.logger.info(f"Inserted {inserted_rows}/{total_rows} rows ({progress_percentage:.1f}%)")
            
            # Success!
            total_time = time.time() - start_time
            return {
                "success": True,
                "message": f"Successfully inserted {inserted_rows} rows",
                "inserted_rows": inserted_rows,
                "total_rows": total_rows,
                "total_time": round(total_time, 2),
                "rows_per_second": round(inserted_rows / total_time, 2) if total_time > 0 else 0,
                "table_name": f"{target_schema}.{target_table_name}"
            }
            
        except Exception as e:
            # Rollback on any error
            self.logger.error(f"Unexpected error during insertion: {e}")
            self._rollback_insertion(target_schema, target_table_name)
            return {
                "success": False,
                "error": str(e),
                "message": "Unexpected error during insertion",
                "inserted_rows": inserted_rows,
                "total_rows": total_rows
            }
    
    def _insert_dataframe_chunk(self, df: pd.DataFrame, schema: str, table_name: str) -> Dict[str, Any]:
        """Insert a DataFrame chunk into PostgreSQL table"""
        try:
            from app.services.postgresql_service import PostgreSQLService
            postgres_service = PostgreSQLService()
            
            with postgres_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare column names for INSERT
                clean_columns = [col.replace(' ', '_').replace('-', '_').lower() for col in df.columns]
                columns_list = ", ".join(clean_columns)
                placeholders = ", ".join(["%s"] * len(clean_columns))
                
                insert_sql = f"""
                INSERT INTO {schema}.{table_name} ({columns_list}) 
                VALUES ({placeholders})
                """
                
                # Convert DataFrame rows to list of tuples
                batch_data = []
                for _, row in df.iterrows():
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
                
                return {
                    "success": True,
                    "inserted_rows": len(batch_data)
                }
                
        except Exception as e:
            self.logger.error(f"Error inserting DataFrame chunk: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to insert chunk: {str(e)}"
            }

    def _rollback_insertion(self, schema: str, table_name: str):
        """Delete all data from the table (rollback)"""
        try:
            from app.services.postgresql_service import PostgreSQLService
            postgres_service = PostgreSQLService()
            
            with postgres_service.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {schema}.{table_name}")
                conn.commit()
                self.logger.info(f"Rollback successful: deleted all data from {schema}.{table_name}")
                
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
    
    def _extract_schema_from_query(self, connection_config: Dict[str, Any], sql_query: str) -> Dict[str, Any]:
        """Extract schema information from the SQL query by getting exact schema from source tables"""
        try:
            # Use the same schema extraction logic as DataPipelineService
            # This ensures consistency between preview and table creation
            self.logger.info("🔍 Using DataPipelineService schema extraction logic")
            
            # Get sample data to identify columns
            sample_result = self.db_connection_service.execute_query(connection_config, sql_query, limit=100)
            
            if not sample_result["success"]:
                return {
                    "success": False,
                    "message": "Failed to get sample data for schema extraction"
                }
            
            # Get column information from the query result
            columns = sample_result.get("columns", [])
            sample_data = sample_result.get("data", [])
            
            if not columns or not sample_data:
                return {
                    "success": False,
                    "message": "No columns or data found in query result"
                }
            
            # Create DataFrame for schema analysis
            import pandas as pd
            df = pd.DataFrame(sample_data, columns=columns)
            
            # Use DataPipelineService to extract real schema from source database
            schema_result = self.pipeline_service._extract_source_database_schema(
                connection_config=connection_config,
                query_sql=sql_query
            )
            
            if schema_result["success"]:
                self.logger.info(f"✅ Successfully extracted real schema: {len(schema_result['columns'])} columns")
                return schema_result
            else:
                self.logger.warning(f"⚠️ Schema extraction failed: {schema_result.get('message', 'Unknown error')}")
                # Fallback to generic schema
                return self._create_fallback_schema(columns)
            
        except Exception as e:
            self.logger.error(f"Error extracting schema from query: {e}")
            return {
                "success": False,
                "message": f"Schema extraction failed: {str(e)}"
            }
    
    def _create_fallback_schema(self, columns: List[str]) -> Dict[str, Any]:
        """Create fallback schema with generic types"""
        self.logger.info("Using fallback schema creation with default types")
        column_schemas = []
        for column_name in columns:
            column_schemas.append({
                "name": column_name,
                "type": "TEXT",  # Default type
                "nullable": True
            })
        
        return {
            "success": True,
            "columns": column_schemas,
            "column_count": len(column_schemas)
        }
    
    def _infer_postgres_type(self, sample_value: Any, column_name: str) -> str:
        """Infer PostgreSQL data type from sample value"""
        try:
            if sample_value is None:
                return "TEXT"  # Default for null values
            
            # Convert to string for type checking
            value_str = str(sample_value)
            
            # Check for numeric types
            try:
                # Try integer
                int(value_str)
                return "INTEGER"
            except ValueError:
                try:
                    # Try decimal/float
                    float(value_str)
                    return "DECIMAL(15,2)"
                except ValueError:
                    pass
            
            # Check for boolean
            if value_str.lower() in ['true', 'false', '1', '0', 'yes', 'no']:
                return "BOOLEAN"
            
            # Check for date/time patterns
            if any(pattern in value_str for pattern in ['-', '/', ':']) and len(value_str) > 8:
                if ':' in value_str:
                    return "TIMESTAMP"
                else:
                    return "DATE"
            
            # Check string length for VARCHAR vs TEXT
            if len(value_str) <= 255:
                return f"VARCHAR({min(255, max(50, len(value_str) + 10))})"
            else:
                return "TEXT"
                
        except Exception as e:
            self.logger.error(f"Error inferring type for column {column_name}, value {sample_value}: {e}")
            return "TEXT"  # Default fallback
    
    def _create_table_with_exact_schema(self, schema_info: Dict[str, Any], target_schema: str, table_name: str) -> bool:
        """Create table in data warehouse with exact schema from source database"""
        try:
            from app.services.postgresql_service import PostgreSQLService
            postgres_service = PostgreSQLService()
            
            with postgres_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build CREATE TABLE statement
                columns_sql = []
                for col in schema_info["columns"]:
                    col_sql = f'"{col["name"]}" {col["type"]}'
                    if not col["nullable"]:
                        col_sql += " NOT NULL"
                    columns_sql.append(col_sql)
                
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {target_schema}.{table_name} (
                    {', '.join(columns_sql)}
                )
                """
                
                self.logger.info(f"Creating table with SQL: {create_sql}")
                cursor.execute(create_sql)
                conn.commit()
                
                self.logger.info(f"✅ Table {target_schema}.{table_name} created successfully with exact schema")
                return True
                
        except Exception as e:
            self.logger.error(f"Error creating table with exact schema: {e}")
            return False

    def get_insertion_progress(self, session_id: str) -> Dict[str, Any]:
        """Get current progress of an insertion operation"""
        # This could be implemented with Redis or database storage
        # For now, return a placeholder
        return {
            "success": True,
            "session_id": session_id,
            "status": "running",
            "progress_percentage": 0,
            "inserted_rows": 0,
            "total_rows": 0
        }

    def insert_data_with_progress(
        self,
        query_sql: str,
        schema: str,
        table_name: str,
        limit: Optional[int] = None,
        is_database_mode: bool = False,
        connection_config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Insert data into existing table with progress tracking.
        
        This method is designed to work with the new two-step process where
        the table is already created with the correct schema.
        
        Args:
            query_sql: SQL query to execute
            schema: Target schema name
            table_name: Target table name
            limit: Maximum rows to insert (None = all)
            is_database_mode: Whether using database mode
            connection_config: Database connection config
            progress_callback: Function to call with progress updates
            
        Returns:
            Dict with insertion results
        """
        try:
            start_time = time.time()
            self.logger.info(f"🚀 Starting data insertion into {schema}.{table_name}")
            
            # Step 1: Determine total rows
            self.logger.info("Determining total rows to insert...")
            
            # Remove any existing LIMIT clause from the base query for counting
            base_query = query_sql
            if "LIMIT" in base_query.upper():
                base_query = base_query.rsplit("LIMIT", 1)[0].strip()
                self.logger.info("Removed existing LIMIT clause from query for counting")
            
            if limit:
                # If limit is provided, use it
                total_rows = limit
                self.logger.info(f"Using provided limit: {total_rows} rows")
            else:
                # If no limit provided, get actual count of all data
                self.logger.info("No limit provided, counting all available rows...")
                
                if is_database_mode and connection_config:
                    # Count all rows from source database
                    count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
                    count_result = self.db_connection_service.execute_query(connection_config, count_query, 1)
                    
                    if count_result["success"] and count_result["data"]:
                        total_rows = count_result["data"][0]["total"]
                        self.logger.info(f"Found {total_rows:,} total rows in source data")
                    else:
                        self.logger.warning("Could not count rows, using default limit")
                        total_rows = 10000
                else:
                    # For file mode, we'll use a reasonable default
                    total_rows = 10000
                    self.logger.info(f"File mode: using default limit of {total_rows} rows")
            
            # Remove any existing LIMIT clause from the base query for data insertion
            if "LIMIT" in base_query.upper():
                base_query = base_query.rsplit("LIMIT", 1)[0].strip()
                self.logger.info("Removed existing LIMIT clause from query for data insertion")
            
            # Step 2: Insert data in chunks
            chunk_size = 1000
            inserted_rows = 0
            
            # Calculate number of chunks
            num_chunks = (total_rows + chunk_size - 1) // chunk_size
            
            # Send initial progress if callback provided
            if progress_callback:
                # Store progress data for the callback
                self.progress_data = {
                    'total_rows': total_rows,
                    'num_chunks': num_chunks,
                    'chunk_size': chunk_size
                }
                progress_callback(0, num_chunks, 0, total_rows, f"Starting insertion of {total_rows:,} rows in {num_chunks} chunks")
            
            for chunk_index in range(num_chunks):
                offset = chunk_index * chunk_size
                chunk_limit = min(chunk_size, total_rows - offset)
                
                # Build query with LIMIT and OFFSET
                if is_database_mode and connection_config:
                    chunk_query = f"{base_query} LIMIT {chunk_limit} OFFSET {offset}"
                    chunk_result = self.db_connection_service.execute_query(connection_config, chunk_query, chunk_limit)
                    
                    if not chunk_result["success"]:
                        return {
                            "success": False,
                            "error": f"Failed to get chunk {chunk_index + 1}",
                            "message": chunk_result.get("message", "Unknown error")
                        }
                    
                    chunk_data = chunk_result["data"]
                    columns = chunk_result["columns"]
                    
                else:
                    # File mode - use base_query without OFFSET for SQLite compatibility
                    chunk_query = f"{base_query} LIMIT {chunk_limit} OFFSET {offset}"
                    from ..services.sql_query_service import SQLQueryService
                    sql_service = SQLQueryService()
                    chunk_result = sql_service.execute_raw_sql(chunk_query)
                    
                    if not chunk_result or 'data' not in chunk_result:
                        return {
                            "success": False,
                            "error": f"Failed to get chunk {chunk_index + 1}",
                            "message": "No data returned"
                        }
                    
                    chunk_data = chunk_result['data']
                    columns = list(chunk_data[0].keys()) if chunk_data else []
                
                # Insert chunk into PostgreSQL
                if chunk_data:
                    df_chunk = pd.DataFrame(chunk_data, columns=columns)
                    
                    # Insert into PostgreSQL using SQLAlchemy engine
                    from ..services.postgresql_service import PostgreSQLService
                    from sqlalchemy import create_engine
                    
                    pg_service = PostgreSQLService()
                    connection_string = pg_service.get_connection_string()
                    engine = create_engine(connection_string)
                    
                    # Prepare data for insertion (exclude id column if it exists)
                    insert_columns = [col for col in df_chunk.columns if col != 'id']
                    df_insert = df_chunk[insert_columns] if insert_columns else df_chunk
                    
                    # Insert data using SQLAlchemy engine
                    df_insert.to_sql(
                        name=table_name,
                        con=engine,
                        schema=schema,
                        if_exists='append',
                        index=False,
                        method='multi'
                    )
                    
                    inserted_rows += len(chunk_data)
                    
                    # Log progress and send callback
                    self.logger.info(f"Inserted chunk {chunk_index + 1}/{num_chunks}: {len(chunk_data)} rows (Total: {inserted_rows:,})")
                    
                    # Send progress update if callback provided
                    if progress_callback:
                        self.logger.info(f"📊 Calling progress callback: chunk {chunk_index + 1}/{num_chunks}, rows {inserted_rows}/{total_rows}")
                        progress_callback(
                            chunk_index + 1, 
                            num_chunks, 
                            inserted_rows, 
                            total_rows, 
                            f"Inserted chunk {chunk_index + 1}/{num_chunks}: {len(chunk_data)} rows"
                        )
            
            # Calculate final statistics
            total_time = time.time() - start_time
            rows_per_second = inserted_rows / total_time if total_time > 0 else 0
            
            self.logger.info(f"✅ Data insertion completed: {inserted_rows:,} rows in {total_time:.2f}s ({rows_per_second:.1f} rows/sec)")
            
            return {
                "success": True,
                "inserted_rows": inserted_rows,
                "total_time": total_time,
                "rows_per_second": rows_per_second,
                "message": f"Successfully inserted {inserted_rows:,} rows"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in data insertion: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Data insertion failed: {str(e)}"
            }