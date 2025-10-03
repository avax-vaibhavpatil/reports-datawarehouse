from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from ..services.column_matching_service import ColumnMatchingService
from ..services.sql_query_service import SQLQueryService

logger = logging.getLogger(__name__)

class ColumnMatchingRequest(BaseModel):
    left_table: str
    right_table: str
    connection_config: Optional[Dict] = None  # For database mode

class ColumnMatchingResponse(BaseModel):
    success: bool
    relationships: List[Dict]
    total_matches: int
    left_table: str
    right_table: str
    message: Optional[str] = None
    error: Optional[str] = None

router = APIRouter(prefix="/api/column-matching", tags=["column-matching"])

def get_column_matching_service() -> ColumnMatchingService:
    return ColumnMatchingService()

def get_sql_query_service() -> SQLQueryService:
    return SQLQueryService()

@router.post("/suggest", response_model=ColumnMatchingResponse)
async def suggest_column_relationships(
    request: ColumnMatchingRequest,
    matching_service: ColumnMatchingService = Depends(get_column_matching_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Suggest column relationships between two tables based on naming patterns
    """
    try:
        # Get tables metadata based on mode
        if request.connection_config:
            # Database mode - get tables from database
            db_response = sql_service.get_database_tables(request.connection_config)
            if not db_response.get('success', False):
                raise HTTPException(status_code=404, detail="Failed to get database tables")
            tables_metadata = db_response.get('tables', [])
        else:
            # File mode - get tables from uploaded files
            tables_metadata = sql_service.get_available_tables()
            if not tables_metadata:
                raise HTTPException(status_code=404, detail="No tables found")
        
        # Find the requested tables
        left_table_data = None
        right_table_data = None
        
        for table in tables_metadata:
            if table['name'] == request.left_table:
                left_table_data = table
            elif table['name'] == request.right_table:
                right_table_data = table
        
        if not left_table_data:
            raise HTTPException(status_code=404, detail=f"Left table '{request.left_table}' not found")
        if not right_table_data:
            raise HTTPException(status_code=404, detail=f"Right table '{request.right_table}' not found")
        
        # Get column suggestions
        result = matching_service.suggest_relationships(
            left_table=request.left_table,
            left_columns=left_table_data['columns'],
            right_table=request.right_table,
            right_columns=right_table_data['columns']
        )
        
        return ColumnMatchingResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in column matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest-all")
async def suggest_all_relationships(
    matching_service: ColumnMatchingService = Depends(get_column_matching_service),
    sql_service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Suggest relationships for all possible table combinations
    """
    try:
        # Get all tables metadata
        tables_metadata = sql_service.get_available_tables()
        if not tables_metadata:
            raise HTTPException(status_code=404, detail="No tables found")
        
        # Get suggestions for all combinations
        result = matching_service.suggest_all_relationships(tables_metadata)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in suggest all relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "column-matching"}