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
            count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) as subquery"
            count_result = self.db_connection_service.execute_query(connection_config, count_query)
            
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
            # Check if query already has LIMIT clause
            if "LIMIT" in sql_query.upper():
                sample_query = sql_query
            else:
                sample_query = f"{sql_query} LIMIT 100"
            sample_result = self.db_connection_service.execute_query(connection_config, sample_query)
            
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
            
            # Calculate offset for descending order if needed
            offset = 0
            
            while inserted_rows < total_rows:
                # Calculate current chunk size
                remaining_rows = total_rows - inserted_rows
                current_chunk_size = min(chunk_size, remaining_rows)
                
                # Build query for current chunk
                if preserve_order:
                    # For descending order, we need to reverse the order
                    # Remove existing LIMIT if present
                    base_query = sql_query
                    if "LIMIT" in base_query.upper():
                        base_query = base_query.rsplit("LIMIT", 1)[0].strip()
                    
                    chunk_query = f"""
                        SELECT * FROM (
                            {base_query}
                        ) as ordered_data
                        ORDER BY row_number() OVER (ORDER BY (SELECT NULL)) DESC
                        LIMIT {current_chunk_size} OFFSET {offset}
                    """
                else:
                    # Remove existing LIMIT if present and add new one
                    base_query = sql_query
                    if "LIMIT" in base_query.upper():
                        base_query = base_query.rsplit("LIMIT", 1)[0].strip()
                    chunk_query = f"{base_query} LIMIT {current_chunk_size} OFFSET {offset}"
                
                # Execute chunk query
                chunk_result = self.db_connection_service.execute_query(
                    connection_config, 
                    chunk_query
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
            # For simplicity, we'll extract schema from the first table in the query
            # In a real implementation, you'd parse the SQL to identify all tables
            
            # Get sample data to identify columns
            sample_result = self.db_connection_service.execute_query(connection_config, sql_query, limit=1)
            
            if not sample_result["success"]:
                return {
                    "success": False,
                    "message": "Failed to get sample data for schema extraction"
                }
            
            # Get column information from the query result
            columns = sample_result.get("columns", [])
            
            if not columns:
                return {
                    "success": False,
                    "message": "No columns found in query result"
                }
            
            # Try to get exact schema from the source table
            # For now, we'll use a simple approach - assume the first table in the query
            # In a real implementation, you'd parse the SQL to get the actual table name
            table_name = self._extract_table_name_from_query(sql_query)
            
            if table_name:
                # Get exact schema from the source table
                schema_result = self.db_connection_service.get_table_schema(
                    connection_config, table_name, 'public'
                )
                
                if schema_result["success"]:
                    # Map the source schema to our query columns
                    column_schemas = []
                    source_columns = {col["name"]: col for col in schema_result["columns"]}
                    
                    for column_name in columns:
                        if column_name in source_columns:
                            source_col = source_columns[column_name]
                            # Map the source data type to PostgreSQL
                            pg_type = self.db_connection_service.map_data_type_to_postgres(
                                source_col["data_type"],
                                source_col.get("max_length"),
                                source_col.get("precision"),
                                source_col.get("scale")
                            )
                            column_schemas.append({
                                "name": column_name,
                                "type": pg_type,
                                "nullable": source_col["nullable"]
                            })
                        else:
                            # Fallback for computed columns or columns not in source table
                            column_schemas.append({
                                "name": column_name,
                                "type": "TEXT",
                                "nullable": True
                            })
                    
                    return {
                        "success": True,
                        "columns": column_schemas,
                        "column_count": len(column_schemas)
                    }
            
            # Fallback: create columns with default types
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
            
        except Exception as e:
            self.logger.error(f"Error extracting schema from query: {e}")
            return {
                "success": False,
                "message": f"Schema extraction failed: {str(e)}"
            }
    
    def _extract_table_name_from_query(self, sql_query: str) -> str:
        """Extract table name from SQL query (simplified approach)"""
        try:
            # Simple regex to extract table name from SELECT statement
            import re
            
            # Look for FROM clause
            match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Look for JOIN clause
            match = re.search(r'JOIN\s+(\w+)', sql_query, re.IGNORECASE)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting table name: {e}")
            return None
    
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