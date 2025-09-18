from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import pandas as pd
import sqlite3
import logging
from pydantic import BaseModel

from ..services.data_pipeline_service import DataPipelineService
from ..services.sql_query_service import SQLQueryService

# Configure logging
logger = logging.getLogger(__name__)

# Create router for schema editor endpoints
router = APIRouter(prefix="/api/schema-editor", tags=["Schema Editor"])

# Pydantic models for request/response validation
class SchemaPreviewRequest(BaseModel):
    """Request model for generating schema preview"""
    query_sql: str                          # The SQL query that was executed
    db_schema: str = "processed_data"       # PostgreSQL schema name
    user_table_name: str                    # User-provided table name (required)
    limit: Optional[int] = 1000            # Limit for data analysis

class TableValidationRequest(BaseModel):
    """Request model for table name validation"""
    table_name: str                         # Table name to validate
    db_schema: str = "processed_data"       # PostgreSQL schema name

class TableCreationRequest(BaseModel):
    """Request model for creating table with data"""
    query_sql: str                          # Original SQL query
    db_schema: str = "processed_data"       # PostgreSQL schema name  
    user_table_name: str                    # User-provided table name
    column_corrections: Dict[str, str]      # User's data type corrections
    limit: Optional[int] = None             # None = insert all data

# Dependency to get services
def get_data_pipeline_service() -> DataPipelineService:
    """Dependency to provide DataPipelineService instance"""
    return DataPipelineService()

def get_sql_query_service() -> SQLQueryService:
    """Dependency to provide SQLQueryService instance"""
    return SQLQueryService()

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
        query_result = sql_service.execute_raw_sql(
            sql_query=request.query_sql,
            limit=request.limit
        )
        
        # execute_raw_sql returns data directly, not a success/error structure
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
            query_sql=request.query_sql
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