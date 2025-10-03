from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from app.services.database_connection_service import DatabaseConnectionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/database-connection", tags=["database-connection"])

# Initialize service
db_connection_service = DatabaseConnectionService()

class DatabaseConnectionRequest(BaseModel):
    connection_id: Optional[str] = None
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    connection_name: Optional[str] = None

class TableDiscoveryRequest(BaseModel):
    connection_id: Optional[str] = None
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str

class QueryExecutionRequest(BaseModel):
    connection_id: Optional[str] = None
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    query: str
    limit: int = 1000

@router.post("/test")
async def test_connection(request: DatabaseConnectionRequest):
    """Test database connection"""
    try:
        connection_config = {
            "connection_id": request.connection_id,
            "db_type": request.db_type,
            "host": request.host,
            "port": request.port,
            "database": request.database,
            "username": request.username,
            "password": request.password,
            "connection_name": request.connection_name
        }
        
        result = db_connection_service.test_connection(connection_config)
        return result
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_connection(request: DatabaseConnectionRequest):
    """Save database connection"""
    try:
        connection_config = {
            "connection_id": request.connection_id,
            "db_type": request.db_type,
            "host": request.host,
            "port": request.port,
            "database": request.database,
            "username": request.username,
            "password": request.password,
            "connection_name": request.connection_name
        }
        
        result = db_connection_service.save_connection(connection_config)
        return result
    except Exception as e:
        logger.error(f"Error saving connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def get_connections():
    """Get all saved connections"""
    try:
        connections = db_connection_service.get_connections()
        return {
            "success": True,
            "connections": connections
        }
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}")
async def get_connection(connection_id: str):
    """Get a specific connection"""
    try:
        connection = db_connection_service.get_connection(connection_id)
        if connection:
            return {
                "success": True,
                "connection": connection
            }
        else:
            raise HTTPException(status_code=404, detail="Connection not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """Delete a connection"""
    try:
        result = db_connection_service.delete_connection(connection_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discover-tables")
async def discover_tables(request: TableDiscoveryRequest):
    """Discover tables in the connected database"""
    try:
        connection_config = {
            "connection_id": request.connection_id,
            "db_type": request.db_type,
            "host": request.host,
            "port": request.port,
            "database": request.database,
            "username": request.username,
            "password": request.password
        }
        
        result = db_connection_service.get_tables_with_password(connection_config)
        return result
    except Exception as e:
        logger.error(f"Error discovering tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-query")
async def execute_query(request: QueryExecutionRequest):
    """Execute a query on the connected database"""
    try:
        connection_config = {
            "connection_id": request.connection_id,
            "db_type": request.db_type,
            "host": request.host,
            "port": request.port,
            "database": request.database,
            "username": request.username,
            "password": request.password
        }
        
        result = db_connection_service.execute_query(
            connection_config, 
            request.query, 
            request.limit
        )
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-databases")
async def get_supported_databases():
    """Get list of supported database types"""
    return {
        "success": True,
        "databases": [
            {
                "type": "postgresql",
                "name": "PostgreSQL",
                "default_port": 5432,
                "description": "PostgreSQL database"
            },
            {
                "type": "mysql",
                "name": "MySQL",
                "default_port": 3306,
                "description": "MySQL database"
            },
            {
                "type": "sqlserver",
                "name": "SQL Server",
                "default_port": 1433,
                "description": "Microsoft SQL Server"
            },
            {
                "type": "oracle",
                "name": "Oracle",
                "default_port": 1521,
                "description": "Oracle Database"
            }
        ]
    }