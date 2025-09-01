from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
import logging
from services.column_mapping_service import ColumnMappingService

class ColumnSelectionRequest(BaseModel):
    table_name: str
    columns: List[str]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/column-mapping", tags=["column-mapping"])

# Create a singleton instance of the service
_column_mapping_service = ColumnMappingService()

def get_column_mapping_service():
    return _column_mapping_service

@router.post("/select-columns")
async def select_columns(
    request: ColumnSelectionRequest,
    service: ColumnMappingService = Depends(get_column_mapping_service)
):
    """Select columns from a specific table"""
    logger.info(f"Selecting columns {request.columns} from table {request.table_name}")
    
    try:
        result = service.select_columns(request.table_name, request.columns)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error selecting columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deselect-columns")
async def deselect_columns(
    request: ColumnSelectionRequest,
    service: ColumnMappingService = Depends(get_column_mapping_service)
):
    """Deselect columns from a specific table"""
    logger.info(f"Deselecting columns {request.columns} from table {request.table_name}")
    
    try:
        result = service.deselect_columns(request.table_name, request.columns)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error deselecting columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/selected-columns")
async def get_selected_columns(
    service: ColumnMappingService = Depends(get_column_mapping_service)
):
    """Get summary of all selected columns"""
    try:
        result = service.get_selected_columns_summary()
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error getting selected columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/column-mappings")
async def get_column_mappings(
    service: ColumnMappingService = Depends(get_column_mapping_service)
):
    """Get all column mappings/relationships"""
    try:
        result = service.get_mapping_summary()
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error getting column mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/combined-table-structure")
async def get_combined_table_structure(
    service: ColumnMappingService = Depends(get_column_mapping_service)
):
    """Get the structure for the new combined table"""
    try:
        result = service.get_combined_table_structure()
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error getting combined table structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear-selections")
async def clear_all_selections(
    service: ColumnMappingService = Depends(get_column_mapping_service)
):
    """Clear all column selections and mappings"""
    try:
        result = service.clear_all_selections()
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error clearing selections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for column mapping service"""
    return {"status": "healthy", "service": "column-mapping"} 