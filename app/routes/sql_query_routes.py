from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import csv
import io
from ..services.sql_query_service import SQLQueryService

# SQL Query Routes

class TableConfig(BaseModel):
    name: str
    alias: Optional[str] = None
    columns: List[str] = []
    custom_expressions: Optional[List[str]] = []

class JoinCondition(BaseModel):
    left_table: str
    left_column: str
    operator: str = "="
    right_table: str
    right_column: str

class JoinConfig(BaseModel):
    type: str
    table: str
    alias: Optional[str] = None
    columns: Optional[List[str]] = []
    conditions: List[JoinCondition]

class WhereCondition(BaseModel):
    left_side: str
    operator: str = "="
    right_side: str
    logical_operator: str = "AND"

class OrderByConfig(BaseModel):
    column: str
    direction: str = "ASC"

class SQLQueryRequest(BaseModel):
    tables: List[TableConfig]
    joins: Optional[List[JoinConfig]] = []
    where_conditions: Optional[List[WhereCondition]] = []
    group_by: Optional[List[str]] = []
    order_by: Optional[List[OrderByConfig]] = []
    limit: Optional[int] = None

class SQLQueryResponse(BaseModel):
    sql: str
    formatted_sql: str
    query_config: Dict[str, Any]
    generated_at: str
    join_count: int
    table_count: int

class QueryPreviewRequest(BaseModel):
    query_config: Dict[str, Any]
    sample_size: int = 100

class QueryPreviewResponse(BaseModel):
    success: bool
    sample_data: List[Dict]
    total_rows: int
    columns: List[str]
    execution_time: str
    error: Optional[str] = None

class CSVExportRequest(BaseModel):
    query_config: Dict[str, Any]
    filename: str
    limit: Optional[int] = None  # No default limit - use query's limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sql-query", tags=["sql-query"])

def get_sql_query_service() -> SQLQueryService:
    return SQLQueryService()

@router.get("/tables")
async def get_available_tables(
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Get list of available tables from uploaded files
    """
    try:
        tables = service.get_available_tables()
        return JSONResponse(content={
            "tables": tables,
            "count": len(tables)
        }, status_code=200)
    except Exception as e:
        logger.error(f"Error getting available tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/join-types")
async def get_supported_join_types():
    """
    Get list of supported JOIN types
    """
    return JSONResponse(content={
        "join_types": [
            {
                "type": "INNER JOIN",
                "description": "Returns only matching records from both tables",
                "example": "SELECT * FROM table1 INNER JOIN table2 ON table1.id = table2.id"
            },
            {
                "type": "LEFT JOIN",
                "description": "Returns all records from left table and matching records from right table",
                "example": "SELECT * FROM table1 LEFT JOIN table2 ON table1.id = table2.id"
            },
            {
                "type": "RIGHT JOIN", 
                "description": "Returns all records from right table and matching records from left table",
                "example": "SELECT * FROM table1 RIGHT JOIN table2 ON table1.id = table2.id"
            },
            {
                "type": "FULL OUTER JOIN",
                "description": "Returns all records when there is a match in either table",
                "example": "SELECT * FROM table1 FULL OUTER JOIN table2 ON table1.id = table2.id"
            },
            {
                "type": "CROSS JOIN",
                "description": "Returns Cartesian product of both tables",
                "example": "SELECT * FROM table1 CROSS JOIN table2"
            }
        ]
    }, status_code=200)

@router.post("/generate", response_model=SQLQueryResponse)
async def generate_sql_query(
    request: SQLQueryRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Generate SQL query based on configuration
    """
    try:
        # Convert Pydantic models to dict
        query_config = {
            "tables": [table.dict() for table in request.tables],
            "joins": [join.dict() for join in request.joins] if request.joins else [],
            "where_conditions": [where.dict() for where in request.where_conditions] if request.where_conditions else [],
            "group_by": request.group_by or [],
            "order_by": [order.dict() for order in request.order_by] if request.order_by else [],
            "limit": request.limit
        }
        
        # Validate configuration
        validation = service.validate_query_config(query_config)
        if not validation["valid"]:
            return JSONResponse(content={
                "error": "Invalid query configuration",
                "details": validation["errors"],
                "warnings": validation["warnings"]
            }, status_code=400)
        
        # Generate SQL
        result = service.generate_sql_query(query_config)
        
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        logger.error(f"Error generating SQL query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_query_config(
    request: SQLQueryRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Validate query configuration without generating SQL
    """
    try:
        query_config = {
            "tables": [table.dict() for table in request.tables],
            "joins": [join.dict() for join in request.joins] if request.joins else [],
            "where_conditions": [where.dict() for where in request.where_conditions] if request.where_conditions else [],
            "group_by": request.group_by or [],
            "order_by": [order.dict() for order in request.order_by] if request.order_by else [],
            "limit": request.limit
        }
        
        validation = service.validate_query_config(query_config)
        
        return JSONResponse(content=validation, status_code=200)
        
    except Exception as e:
        logger.error(f"Error validating query configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview", response_model=QueryPreviewResponse)
async def preview_query(
    request: QueryPreviewRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Preview query results with sample data
    """
    try:
        result = service.execute_query_preview(
            request.query_config, 
            request.sample_size
        )
        
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        logger.error(f"Error previewing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_query(
    request: QueryPreviewRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Execute query and return full results
    """
    try:
        result = service.execute_query_preview(
            request.query_config, 
            request.sample_size or 1000  # Default to 1000 rows for full execution
        )
        
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
async def get_query_examples():
    """
    Get example SQL queries for different scenarios
    """
    examples = [
        {
            "name": "Simple INNER JOIN",
            "description": "Join two tables with matching records",
            "sql": """SELECT l.lg_voucher_no, l.lg_voucher_date, ld.lgd_acc_code, ld.lgd_amount
FROM ledger l
INNER JOIN ledger_detail ld
    ON l.lg_voucher_no = ld.lgd_voucher_no""",
            "config": {
                "tables": [
                    {"name": "ledger", "alias": "l", "columns": ["lg_voucher_no", "lg_voucher_date"]},
                    {"name": "ledger_detail", "alias": "ld", "columns": ["lgd_acc_code", "lgd_amount"]}
                ],
                "joins": [{
                    "type": "INNER JOIN",
                    "table": "ledger_detail",
                    "alias": "ld",
                    "conditions": [{
                        "left_table": "l",
                        "left_column": "lg_voucher_no",
                        "operator": "=",
                        "right_table": "ld",
                        "right_column": "lgd_voucher_no"
                    }]
                }]
            }
        },
        {
            "name": "FULL OUTER JOIN",
            "description": "Get all records from both tables",
            "sql": """SELECT l.lg_voucher_no, l.lg_voucher_date, ld.lgd_acc_code, ld.lgd_amount
FROM ledger l
FULL OUTER JOIN ledger_detail ld
    ON l.lg_voucher_no = ld.lgd_voucher_no""",
            "config": {
                "tables": [
                    {"name": "ledger", "alias": "l", "columns": ["lg_voucher_no", "lg_voucher_date"]},
                    {"name": "ledger_detail", "alias": "ld", "columns": ["lgd_acc_code", "lgd_amount"]}
                ],
                "joins": [{
                    "type": "FULL OUTER JOIN",
                    "table": "ledger_detail",
                    "alias": "ld",
                    "conditions": [{
                        "left_table": "l",
                        "left_column": "lg_voucher_no",
                        "operator": "=",
                        "right_table": "ld",
                        "right_column": "lgd_voucher_no"
                    }]
                }]
            }
        },
        {
            "name": "Multi-condition JOIN",
            "description": "Join with multiple conditions",
            "sql": """SELECT i.ins_no, i.ins_amount, b.sbnk_name, b.sbnk_bbranch_name
FROM instrument i
INNER JOIN siscon_bank b
    ON i.ins_deposit_bank = b.sbnk_code
   AND i.ins_deposit_branch = b.sbnk_bbranch_code""",
            "config": {
                "tables": [
                    {"name": "instrument", "alias": "i", "columns": ["ins_no", "ins_amount"]},
                    {"name": "siscon_bank", "alias": "b", "columns": ["sbnk_name", "sbnk_bbranch_name"]}
                ],
                "joins": [{
                    "type": "INNER JOIN",
                    "table": "siscon_bank",
                    "alias": "b",
                    "conditions": [
                        {
                            "left_table": "i",
                            "left_column": "ins_deposit_bank",
                            "operator": "=",
                            "right_table": "b",
                            "right_column": "sbnk_code"
                        },
                        {
                            "left_table": "i",
                            "left_column": "ins_deposit_branch",
                            "operator": "=",
                            "right_table": "b",
                            "right_column": "sbnk_bbranch_code"
                        }
                    ]
                }]
            }
        }
    ]
    
    return JSONResponse(content={"examples": examples}, status_code=200)

@router.post("/recreate-indexes")
async def recreate_indexes():
    """Recreate database indexes to improve JOIN performance"""
    try:
        service = SQLQueryService()
        result = service.recreate_indexes_for_existing_data()
        
        if result["success"]:
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error recreating indexes: {e}")
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@router.post("/export-csv")
async def export_query_to_csv(
    request: CSVExportRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """
    Export query results to CSV with custom filename
    """
    try:
        logger.info(f"CSV export request received: filename={request.filename}, limit={request.limit}")
        
        # Execute the query - if no limit specified, get all data
        # If limit is specified, use it; otherwise get all available data
        limit = request.limit if request.limit is not None else 1000000  # Large number for "all data"
        result = service.execute_query_preview(
            request.query_config, 
            limit
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Query execution failed"))
        
        # Get the data and columns
        data = result.get("sample_data", [])
        columns = result.get("columns", [])
        
        if not data or not columns:
            raise HTTPException(status_code=400, detail="No data to export")
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        
        for row in data:
            # Clean the data for CSV (handle None values)
            clean_row = {}
            for col in columns:
                value = row.get(col)
                if value is None:
                    clean_row[col] = ""
                else:
                    clean_row[col] = str(value)
            writer.writerow(clean_row)
        
        csv_content = output.getvalue()
        output.close()
        
        # Ensure filename has .csv extension
        filename = request.filename
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        # Return CSV file as response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")

# Database Connection Routes

class DatabaseTableRequest(BaseModel):
    connection_config: Dict[str, Any]

class DatabaseQueryRequest(BaseModel):
    connection_config: Dict[str, Any]
    query_config: Dict[str, Any]

@router.post("/database-tables")
async def get_database_tables(
    request: DatabaseTableRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Get tables from connected database"""
    try:
        result = service.get_database_tables(request.connection_config)
        return result
    except Exception as e:
        logger.error(f"Error getting database tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database-generate")
async def generate_database_sql_query(
    request: DatabaseQueryRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Generate and execute SQL query on connected database"""
    try:
        result = service.generate_database_sql_query({
            "connection_config": request.connection_config,
            "query_config": request.query_config
        })
        return result
    except Exception as e:
        logger.error(f"Error generating database SQL query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database-execute")
async def execute_database_query(
    request: DatabaseQueryRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Execute query on connected database"""
    try:
        # Extract query from query_config
        query = request.query_config.get("sql", "")
        if not query:
            raise HTTPException(status_code=400, detail="No SQL query provided")
        
        result = service.execute_database_query(
            request.connection_config, 
            query,
            request.query_config.get("limit", 1000)
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing database query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class DatabasePreviewRequest(BaseModel):
    connection_config: Dict[str, Any]
    sql: str
    limit: Optional[int] = 1000

class DatabaseSaveRequest(BaseModel):
    connection_config: Dict[str, Any]
    sql: str
    table_name: str
    schema: Optional[str] = "processed_data"

class DatabaseChunkedSaveRequest(BaseModel):
    connection_config: Dict[str, Any]
    sql: str
    table_name: str
    schema: Optional[str] = "processed_data"
    chunk_size: Optional[int] = 1000
    preserve_order: Optional[bool] = True

class DatabaseSchemaRequest(BaseModel):
    connection_config: Dict[str, Any]
    table_name: str
    schema_name: Optional[str] = "public"

@router.post("/database-preview")
async def preview_database_query(
    request: DatabasePreviewRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Execute database query and return preview data (1000 rows)"""
    try:
        result = service.execute_database_query_preview({
            "connection_config": request.connection_config,
            "sql": request.sql,
            "limit": request.limit
        })
        return result
    except Exception as e:
        logger.error(f"Error previewing database query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database-save")
async def save_database_query_to_warehouse(
    request: DatabaseSaveRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Save database query results to data warehouse"""
    try:
        result = service.save_database_query_to_warehouse({
            "connection_config": request.connection_config,
            "sql": request.sql,
            "table_name": request.table_name,
            "schema": request.schema
        })
        return result
    except Exception as e:
        logger.error(f"Error saving database query to warehouse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database-save-chunked")
async def save_database_query_to_warehouse_chunked(
    request: DatabaseChunkedSaveRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Save database query results to data warehouse with chunked insertion and progress tracking"""
    try:
        result = service.save_database_query_to_warehouse_chunked({
            "connection_config": request.connection_config,
            "sql": request.sql,
            "table_name": request.table_name,
            "schema": request.schema,
            "chunk_size": request.chunk_size,
            "preserve_order": request.preserve_order
        })
        return result
    except Exception as e:
        logger.error(f"Error saving database query to warehouse with chunked insertion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database-schema")
async def get_database_table_schema(
    request: DatabaseSchemaRequest,
    service: SQLQueryService = Depends(get_sql_query_service)
):
    """Get exact table schema from INFORMATION_SCHEMA"""
    try:
        from app.services.database_connection_service import DatabaseConnectionService
        db_service = DatabaseConnectionService()
        
        result = db_service.get_table_schema(
            request.connection_config,
            request.table_name,
            request.schema_name
        )
        return result
    except Exception as e:
        logger.error(f"Error getting database table schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))