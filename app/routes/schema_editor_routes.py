from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import pandas as pd
import sqlite3
import logging
import json
import asyncio
from pydantic import BaseModel

from ..services.data_pipeline_service import DataPipelineService
from ..services.sql_query_service import SQLQueryService
from ..services.chunked_insertion_service import ChunkedInsertionService

# Configure logging
logger = logging.getLogger(__name__)

# Create router for schema editor endpoints
router = APIRouter(prefix="/api/schema-editor", tags=["Schema Editor"])

# Pydantic models for request/response validation
class SchemaPreviewRequest(BaseModel):
    """Request model for generating schema preview"""
    query_sql: str                          # The SQL query that was executed
    db_schema: str = "processed_data"       # PostgreSQL schema name (default to processed_data for warehouse)
    user_table_name: str                    # User-provided table name (required)
    limit: Optional[int] = 1000            # Limit for data analysis
    is_database_mode: Optional[bool] = False # Whether this is database mode
    connection_config: Optional[Dict[str, Any]] = None # Database connection config

class TableValidationRequest(BaseModel):
    """Request model for table name validation"""
    table_name: str                         # Table name to validate
    db_schema: str = "processed_data"       # PostgreSQL schema name (default to processed_data for warehouse)

class TableCreationRequest(BaseModel):
    """Request model for creating table with data"""
    query_sql: str                          # Original SQL query
    db_schema: str = "processed_data"       # PostgreSQL schema name (default to processed_data for warehouse)
    user_table_name: str                    # User-provided table name
    column_corrections: Dict[str, str]      # User's data type corrections
    limit: Optional[int] = None             # None = insert all data
    is_database_mode: Optional[bool] = False # Whether this is database mode
    connection_config: Optional[Dict[str, Any]] = None # Database connection config

class DatabaseSchemaDetectionRequest(BaseModel):
    """Request model for detecting database schemas"""
    connection_config: Dict[str, Any]       # Database connection configuration

class TableOnlyCreationRequest(BaseModel):
    """Request model for creating table only (no data insertion)"""
    query_sql: str                          # Original SQL query
    db_schema: str = "processed_data"       # PostgreSQL schema name (default to processed_data for warehouse)
    user_table_name: str                    # User-provided table name
    column_corrections: Dict[str, str]      # User's data type corrections
    is_database_mode: Optional[bool] = False # Whether this is database mode
    connection_config: Optional[Dict[str, Any]] = None # Database connection config

class DataInsertionRequest(BaseModel):
    """Request model for inserting data into existing table with progress tracking"""
    query_sql: str                          # Original SQL query
    db_schema: str = "processed_data"       # PostgreSQL schema name
    user_table_name: str                    # User-provided table name
    limit: Optional[int] = None             # None = insert all data
    is_database_mode: Optional[bool] = False # Whether this is database mode
    connection_config: Optional[Dict[str, Any]] = None # Database connection config

# Dependency to get services
def get_data_pipeline_service() -> DataPipelineService:
    """Dependency to provide DataPipelineService instance"""
    return DataPipelineService()

def get_sql_query_service() -> SQLQueryService:
    """Dependency to provide SQLQueryService instance"""
    return SQLQueryService()

def get_chunked_insertion_service() -> ChunkedInsertionService:
    """Dependency to provide ChunkedInsertionService instance"""
    return ChunkedInsertionService()

@router.post("/preview")
def generate_schema_preview(
    request: SchemaPreviewRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
) -> Dict[str, Any]:
    """
    Generate schema preview for user review and editing.
    
    This endpoint:
    1. Executes the SQL query to get sample data
    2. Analyzes column types and generates PostgreSQL schema
    3. Validates user-provided table name
    4. Checks if table already exists
    5. Returns complete preview for frontend schema editor
    
    Args:
        request: Schema preview request with query and table name
        
    Returns:
        Dict containing schema preview, validation results, and CREATE TABLE SQL
        
    Raises:
        HTTPException: If query execution fails or validation errors occur
    """
    try:
        logger.info(f"🔍 Schema preview requested for table: {request.user_table_name}")
        
        # Step 1: Execute SQL query to get data for analysis
        logger.info("📊 Executing SQL query for schema analysis...")
        
        if request.is_database_mode and request.connection_config:
            # For database mode, execute query against source database to get real schema
            logger.info("🔍 Database mode: Executing query against source database for real schema extraction")
            from ..services.database_connection_service import DatabaseConnectionService
            db_service = DatabaseConnectionService()
            query_result = db_service.execute_query(
                connection_config=request.connection_config,
                query=request.query_sql,
                limit=request.limit or 100
            )
        else:
            # For file mode, use SQLite persistent database
            logger.info("📁 File mode: Using SQLite persistent database")
            query_result = sql_service.execute_raw_sql(
                sql_query=request.query_sql,
                limit=request.limit
            )
        
        # Handle different response formats from different services
        if request.is_database_mode and request.connection_config:
            # Database connection service returns success/error structure
            if not query_result.get('success', False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Database query execution failed: {query_result.get('error', 'Unknown error')}"
                )
        else:
            # SQLite service returns data directly
            if not query_result or 'data' not in query_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"Query execution failed: No data returned"
                )
        
        # Step 2: Convert query results to DataFrame for analysis
        sample_data = query_result['data']
        columns = query_result['columns']
        
        if not sample_data or not columns:
            raise HTTPException(
                status_code=400,
                detail="Query returned no data for schema analysis"
            )
        
        # Create DataFrame from query results
        df = pd.DataFrame(sample_data, columns=columns)
        logger.info(f"📋 Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
        # Step 3: Generate schema preview using our pipeline service
        preview_result = pipeline_service.generate_schema_preview(
            df=df,
            schema=request.db_schema,
            user_table_name=request.user_table_name,
            query_sql=request.query_sql,
            is_database_mode=request.is_database_mode or False,
            connection_config=request.connection_config
        )
        
        if not preview_result.get('success', False):
            raise HTTPException(
                status_code=400,
                detail=f"Schema preview generation failed: {preview_result.get('error', 'Unknown error')}"
            )
        
        # Step 4: Add original query metadata
        preview_result['original_query'] = {
            'sql': request.query_sql,
            'total_rows_available': query_result.get('total_rows', 0),
            'sample_rows_analyzed': len(df),
            'execution_time': query_result.get('execution_time', 'N/A')
        }
        
        logger.info(f"✅ Schema preview generated successfully for {request.user_table_name}")
        return preview_result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in schema preview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/validate-table-name")
def validate_table_name(
    request: TableValidationRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service)
) -> Dict[str, Any]:
    """
    Validate table name and check for duplicates.
    
    This endpoint:
    1. Validates table name against PostgreSQL rules
    2. Checks if table already exists in database
    3. Returns validation results and suggestions
    
    Args:
        request: Table validation request with name and schema
        
    Returns:
        Dict containing validation results and existence check
    """
    try:
        logger.info(f"🔍 Validating table name: {request.db_schema}.{request.table_name}")
        
        # Step 1: Validate table name format
        name_validation = pipeline_service.validate_table_name(request.table_name)
        
        # Step 2: Check if table exists
        existence_check = pipeline_service.check_table_exists(request.db_schema, request.table_name)
        
        # Step 3: Combine results
        validation_result = {
            'success': True,
            'table_name': request.table_name,
            'schema': request.db_schema,
            'full_table_name': f"{request.db_schema}.{request.table_name}",
            'name_validation': name_validation,
            'table_exists': existence_check,
            'can_create': (
                name_validation['is_valid'] and 
                not existence_check['exists'] and 
                existence_check['success']
            ),
            'message': 'Table name validation completed'
        }
        
        logger.info(f"✅ Table validation completed: Can create = {validation_result['can_create']}")
        return validation_result
        
    except Exception as e:
        logger.error(f"❌ Error in table name validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )

@router.post("/create-table")
async def create_table_with_data(
    request: TableCreationRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
) -> Dict[str, Any]:
    """
    Create PostgreSQL table with user-corrected schema and insert data.
    
    This endpoint:
    1. Validates table name and checks for duplicates
    2. Executes SQL query to get all data
    3. Applies user's column type corrections
    4. Creates PostgreSQL table with corrected schema
    5. Inserts all data into the new table
    
    Args:
        request: Table creation request with schema corrections
        
    Returns:
        Dict containing creation results and insertion statistics
        
    Note:
        This function will be implemented in the next step
    """
    try:
        logger.info(f"🏗️ Table creation requested: {request.db_schema}.{request.user_table_name}")
        
        # Step 1: Validate table name and check for duplicates
        name_validation = pipeline_service.validate_table_name(request.user_table_name)
        existence_check = pipeline_service.check_table_exists(request.db_schema, request.user_table_name)
        
        if not name_validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table name: {', '.join(name_validation['errors'])}"
            )
        
        if existence_check['exists']:
            raise HTTPException(
                status_code=400,
                detail=f"Table already exists: {existence_check['message']}"
            )
        
        # Step 2: Execute table creation and data insertion
        logger.info(f"🚀 Starting table creation and data insertion...")
        
        creation_result = pipeline_service.create_table_and_insert_data(
            query_sql=request.query_sql,
            schema=request.db_schema,
            table_name=request.user_table_name,
            column_corrections=request.column_corrections
        )
        
        if creation_result['success']:
            logger.info(f"✅ Table creation completed: {creation_result['message']}")
        else:
            logger.error(f"❌ Table creation failed: {creation_result.get('error')}")
        
        return creation_result
        
    except Exception as e:
        logger.error(f"❌ Error in table creation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Table creation error: {str(e)}"
        )

@router.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint for schema editor service.
    
    Returns:
        Dict with service status
    """
    return {
        'status': 'healthy',
        'service': 'Schema Editor API',
        'message': 'Schema editor endpoints are operational'
    }

@router.get("/test-services")
def test_services() -> Dict[str, Any]:
    """Test endpoint to verify service dependencies are working"""
    try:
        # Test 1: Import pandas
        import pandas as pd
        
        # Test 2: Create services
        pipeline_service = DataPipelineService()
        sql_service = SQLQueryService()
        
        # Test 3: Simple service call
        validation = pipeline_service.validate_table_name("test_table")
        
        return {
            'success': True,
            'pandas_version': pd.__version__,
            'services_created': True,
            'validation_test': validation['is_valid'],
            'message': 'All services working correctly'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Service test failed'
        }

@router.post("/create-table-database")
async def create_table_with_data_database(
    request: TableCreationRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
) -> Dict[str, Any]:
    """
    Create PostgreSQL table with user-corrected schema and insert data from database.
    
    This endpoint:
    1. Validates table name and checks for duplicates
    2. Executes SQL query on connected database to get all data
    3. Applies user's column type corrections
    4. Creates PostgreSQL table with corrected schema
    5. Inserts all data into the new table using chunked insertion
    
    Args:
        request: Table creation request with schema corrections and database connection
        
    Returns:
        Dict containing creation results and insertion statistics
    """
    try:
        logger.info(f"🏗️ Database table creation requested: {request.db_schema}.{request.user_table_name}")
        
        # Step 1: Validate table name and check for duplicates
        name_validation = pipeline_service.validate_table_name(request.user_table_name)
        existence_check = pipeline_service.check_table_exists(request.db_schema, request.user_table_name)
        
        if not name_validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table name: {', '.join(name_validation['errors'])}"
            )
        
        if existence_check['exists']:
            raise HTTPException(
                status_code=400,
                detail=f"Table already exists: {existence_check['message']}"
            )
        
        # Step 2: Execute database query to get all data
        logger.info(f"🚀 Starting database table creation and data insertion...")
        
        # Use chunked insertion service for database mode
        from ..services.chunked_insertion_service import ChunkedInsertionService
        chunked_service = ChunkedInsertionService()
        
        creation_result = chunked_service.insert_data_with_progress(
            connection_config=request.connection_config,
            sql_query=request.query_sql,
            target_table_name=request.user_table_name,
            target_schema=request.db_schema,
            chunk_size=1000,
            preserve_order=True
        )
        
        if creation_result['success']:
            logger.info(f"✅ Database table creation completed: {creation_result['message']}")
            return {
                'success': True,
                'table_name': creation_result['table_name'],
                'schema': request.db_schema,
                'total_rows_inserted': creation_result['inserted_rows'],
                'total_time_seconds': creation_result['total_time'],
                'rows_per_second': creation_result['rows_per_second'],
                'message': creation_result['message']
            }
        else:
            logger.error(f"❌ Database table creation failed: {creation_result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=creation_result.get('message', 'Database table creation failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in database table creation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/create-table-only")
async def create_table_only(
    request: TableOnlyCreationRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
) -> Dict[str, Any]:
    """
    Create PostgreSQL table with correct schema only (no data insertion).
    
    This endpoint:
    1. Validates table name and checks for duplicates
    2. Uses DataPipelineService to extract real schema from source database
    3. Creates PostgreSQL table with correct schema
    4. Returns success message (no data insertion)
    
    Args:
        request: Table creation request with schema corrections
        
    Returns:
        Dict containing creation results and table information
    """
    try:
        logger.info(f"🏗️ Table-only creation requested: {request.db_schema}.{request.user_table_name}")
        
        # Step 1: Validate table name and check for duplicates
        name_validation = pipeline_service.validate_table_name(request.user_table_name)
        existence_check = pipeline_service.check_table_exists(request.db_schema, request.user_table_name)
        
        if not name_validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table name: {', '.join(name_validation['errors'])}"
            )
        
        if existence_check['exists']:
            raise HTTPException(
                status_code=400,
                detail=f"Table already exists: {existence_check['message']}"
            )
        
        # Step 2: Execute SQL query to get sample data for schema analysis
        logger.info("📊 Executing SQL query for schema analysis...")
        
        if request.is_database_mode and request.connection_config:
            # For database mode, execute query against source database to get real schema
            logger.info("🔍 Database mode: Executing query against source database for real schema extraction")
            from ..services.database_connection_service import DatabaseConnectionService
            db_service = DatabaseConnectionService()
            query_result = db_service.execute_query(
                connection_config=request.connection_config,
                query=request.query_sql,
                limit=100
            )
        else:
            # For file mode, use SQLite persistent database
            logger.info("📁 File mode: Using SQLite persistent database")
            query_result = sql_service.execute_raw_sql(
                sql_query=request.query_sql,
                limit=100
            )
        
        # Handle different response formats from different services
        if request.is_database_mode and request.connection_config:
            # Database connection service returns success/error structure
            if not query_result.get('success', False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Database query execution failed: {query_result.get('error', 'Unknown error')}"
                )
        else:
            # SQLite service returns data directly
            if not query_result or 'data' not in query_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"Query execution failed: No data returned"
                )
        
        # Step 3: Convert query results to DataFrame for analysis
        sample_data = query_result['data']
        columns = query_result['columns']
        
        if not sample_data or not columns:
            raise HTTPException(
                status_code=400,
                detail="Query returned no data for schema analysis"
            )
        
        # Create DataFrame from query results
        df = pd.DataFrame(sample_data, columns=columns)
        logger.info(f"📋 Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
        # Step 4: Generate schema preview using our pipeline service
        preview_result = pipeline_service.generate_schema_preview(
            df=df,
            schema=request.db_schema,
            user_table_name=request.user_table_name,
            query_sql=request.query_sql,
            is_database_mode=request.is_database_mode or False,
            connection_config=request.connection_config
        )
        
        if not preview_result.get('success', False):
            raise HTTPException(
                status_code=400,
                detail=f"Schema preview generation failed: {preview_result.get('error', 'Unknown error')}"
            )
        
        # Step 5: Apply user's column corrections to the schema
        logger.info("🔧 Applying user's column corrections...")
        corrected_columns = []
        for column in preview_result['columns']:
            column_name = column['original_name']
            if column_name in request.column_corrections:
                corrected_type = request.column_corrections[column_name]
                logger.info(f"📝 Correcting {column_name}: {column['suggested_pg_type']} → {corrected_type}")
                column['suggested_pg_type'] = corrected_type
            corrected_columns.append(column)
        
        # Step 6: Create table with corrected schema
        logger.info(f"🏗️ Creating table {request.db_schema}.{request.user_table_name} with corrected schema...")
        
        creation_result = pipeline_service.create_table_with_schema(
            schema=request.db_schema,
            table_name=request.user_table_name,
            columns=corrected_columns
        )
        
        if creation_result['success']:
            logger.info(f"✅ Table creation completed: {creation_result['message']}")
            return {
                'success': True,
                'table_name': request.user_table_name,
                'schema': request.db_schema,
                'full_table_name': f"{request.db_schema}.{request.user_table_name}",
                'columns_created': len(corrected_columns),
                'schema_applied': [col['suggested_pg_type'] for col in corrected_columns],
                'message': f"Table '{request.user_table_name}' created successfully in schema '{request.db_schema}' with correct schema"
            }
        else:
            logger.error(f"❌ Table creation failed: {creation_result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=creation_result.get('message', 'Table creation failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in table-only creation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/detect-schemas")
async def detect_database_schemas(
    request: DatabaseSchemaDetectionRequest
) -> Dict[str, Any]:
    """
    Detect all available schemas in the connected database
    
    This endpoint queries the database's information_schema to get all
    available schemas that the user can choose from for table creation.
    """
    try:
        from ..services.database_connection_service import DatabaseConnectionService
        
        logger.info(f"🔍 Detecting schemas for database: {request.connection_config.get('database', 'unknown')}")
        
        # Initialize database connection service
        db_service = DatabaseConnectionService()
        
        # Get all schemas from the database
        schemas_result = db_service.get_database_schemas(request.connection_config)
        
        if not schemas_result["success"]:
            logger.error(f"❌ Failed to detect schemas: {schemas_result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=400,
                detail=schemas_result.get('error', 'Failed to detect database schemas')
            )
        
        schemas = schemas_result.get("schemas", [])
        logger.info(f"✅ Detected {len(schemas)} schemas: {[s['name'] for s in schemas]}")
        
        return {
            "success": True,
            "schemas": schemas,
            "total_count": len(schemas),
            "message": f"Successfully detected {len(schemas)} schemas"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error detecting database schemas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/test-sse")
async def test_sse():
    """Test Server-Sent Events endpoint"""
    async def generate_test_stream():
        for i in range(5):
            yield f"data: {json.dumps({'type': 'test', 'message': f'Test message {i}', 'progress': i * 20})}\n\n"
            await asyncio.sleep(1)
        yield f"data: {json.dumps({'type': 'complete', 'message': 'Test completed', 'progress': 100})}\n\n"
    
    return StreamingResponse(
        generate_test_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.post("/insert-data-stream")
async def insert_data_with_progress(
    request: DataInsertionRequest,
    chunked_service: ChunkedInsertionService = Depends(get_chunked_insertion_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Insert data into existing table with real-time progress tracking via Server-Sent Events.
    
    Args:
        request: Data insertion request
        
    Returns:
        Server-Sent Events stream with progress updates
    """
    
    async def generate_progress_stream():
        try:
            logger.info(f"🚀 Starting data insertion with progress: {request.db_schema}.{request.user_table_name}")
            
            # Step 1: Validate table exists
            pipeline_service = DataPipelineService()
            existence_check = pipeline_service.check_table_exists(request.db_schema, request.user_table_name)
            
            if not existence_check['exists']:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Table {request.db_schema}.{request.user_table_name} does not exist. Please create table first.', 'progress': 0})}\n\n"
                return
            
            # Step 2: Send initial progress
            logger.info("📤 Sending initial progress")
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting data insertion...', 'progress': 0})}\n\n"
            
            # Step 3: Set up real-time progress tracking with a simpler approach
            import asyncio
            import threading
            progress_updates = []
            progress_lock = threading.Lock()
            insertion_complete = threading.Event()
            insertion_result = None
            
            def progress_callback(chunk_index: int, total_chunks: int, rows_inserted: int, total_rows: int, message: str):
                """Progress callback that stores updates in a thread-safe list"""
                percentage = int((rows_inserted / total_rows) * 100) if total_rows > 0 else 0
                progress_data = {
                    'type': 'progress',
                    'chunk_index': chunk_index,
                    'total_chunks': total_chunks,
                    'rows_inserted': rows_inserted,
                    'total_rows': total_rows,
                    'percentage': percentage,
                    'message': message,
                    'progress': percentage
                }
                logger.info(f"📊 Progress callback: {progress_data}")
                
                # Store progress update in thread-safe list
                with progress_lock:
                    progress_updates.append(progress_data)
            
            # Step 4: Run data insertion in a background thread
            def run_insertion():
                """Run the synchronous data insertion in a thread"""
                nonlocal insertion_result
                try:
                    logger.info("🔄 Starting data insertion in background thread...")
                    insertion_result = chunked_service.insert_data_with_progress(
                        request.query_sql,
                        request.db_schema,
                        request.user_table_name,
                        request.limit,
                        request.is_database_mode,
                        request.connection_config,
                        progress_callback
                    )
                    logger.info("✅ Data insertion completed in background thread")
                except Exception as e:
                    logger.error(f"❌ Error in insertion thread: {str(e)}")
                    insertion_result = {'success': False, 'error': str(e)}
                finally:
                    insertion_complete.set()
            
            # Step 5: Start insertion thread
            insertion_thread = threading.Thread(target=run_insertion)
            insertion_thread.start()
            
            # Step 6: Stream progress updates in real-time while insertion is running
            logger.info("📡 Starting real-time progress streaming...")
            last_sent_index = 0
            
            while not insertion_complete.is_set():
                # Check for new progress updates
                with progress_lock:
                    if len(progress_updates) > last_sent_index:
                        # Send new progress updates
                        for i in range(last_sent_index, len(progress_updates)):
                            progress_data = progress_updates[i]
                            logger.info(f"📤 Sending real-time progress update: {progress_data}")
                            yield f"data: {json.dumps(progress_data)}\n\n"
                        last_sent_index = len(progress_updates)
                
                # Wait a bit before checking again
                await asyncio.sleep(0.1)
            
            # Step 7: Wait for insertion thread to complete
            insertion_thread.join()
            
            # Step 8: Send completion message
            if insertion_result.get('success'):
                logger.info(f"✅ Data insertion completed: {insertion_result['inserted_rows']:,} rows")
                yield f"data: {json.dumps({'type': 'complete', 'message': f'Successfully inserted {insertion_result["inserted_rows"]:,} rows', 'progress': 100, 'inserted_rows': insertion_result['inserted_rows'], 'total_time': insertion_result['total_time'], 'rows_per_second': insertion_result['rows_per_second']})}\n\n"
            else:
                logger.error(f"❌ Data insertion failed: {insertion_result.get('error', 'Unknown error')}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'Data insertion failed: {insertion_result.get("error", "Unknown error")}', 'progress': 0})}\n\n"
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in data insertion: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Unexpected error: {str(e)}', 'progress': 0})}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    ) 