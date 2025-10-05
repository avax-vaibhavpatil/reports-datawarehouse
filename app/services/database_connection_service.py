import os
import json
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class DatabaseConnectionService:
    def __init__(self):
        self.connections = {}
        self.connection_config_file = "data/connections.json"
        self._load_connections()
    
    def _load_connections(self):
        """Load saved connections from file"""
        try:
            if os.path.exists(self.connection_config_file):
                with open(self.connection_config_file, 'r') as f:
                    self.connections = json.load(f)
        except Exception as e:
            logger.error(f"Error loading connections: {e}")
            self.connections = {}
    
    def _save_connections(self):
        """Save connections to file"""
        try:
            os.makedirs(os.path.dirname(self.connection_config_file), exist_ok=True)
            with open(self.connection_config_file, 'w') as f:
                json.dump(self.connections, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving connections: {e}")
    
    def test_connection(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection"""
        try:
            # Create connection string based on database type
            connection_string = self._build_connection_string(connection_config)
            
            # Test connection
            engine = create_engine(connection_string, echo=False)
            with engine.connect() as conn:
                # Test with a simple query
                result = conn.execute(text("SELECT 1 as test"))
                result.fetchone()
            
            return {
                "success": True,
                "message": "Connection successful",
                "connection_id": connection_config.get("connection_id")
            }
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "error": str(e)
            }
    
    def _build_connection_string(self, config: Dict[str, Any]) -> str:
        """Build SQLAlchemy connection string"""
        db_type = config.get("db_type", "").lower()
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        database = config.get("database", "")
        username = config.get("username", "")
        password = config.get("password", "")
        
        if db_type == "postgresql":
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mysql":
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "sqlserver":
            return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == "oracle":
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def save_connection(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new database connection"""
        try:
            # Test connection first
            test_result = self.test_connection(connection_config)
            if not test_result["success"]:
                return test_result
            
            # Generate connection ID
            connection_id = connection_config.get("connection_id") or f"conn_{len(self.connections) + 1}"
            connection_config["connection_id"] = connection_id
            
            # Save connection (without password in the saved config)
            safe_config = connection_config.copy()
            safe_config["password"] = "***"  # Don't save actual password
            
            self.connections[connection_id] = safe_config
            self._save_connections()
            
            return {
                "success": True,
                "message": "Connection saved successfully",
                "connection_id": connection_id
            }
        except Exception as e:
            logger.error(f"Error saving connection: {e}")
            return {
                "success": False,
                "message": f"Error saving connection: {str(e)}",
                "error": str(e)
            }
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Get all saved connections"""
        return list(self.connections.values())
    
    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific connection by ID"""
        return self.connections.get(connection_id)
    
    def delete_connection(self, connection_id: str) -> Dict[str, Any]:
        """Delete a connection"""
        try:
            if connection_id in self.connections:
                del self.connections[connection_id]
                self._save_connections()
                return {
                    "success": True,
                    "message": "Connection deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Connection not found"
                }
        except Exception as e:
            logger.error(f"Error deleting connection: {e}")
            return {
                "success": False,
                "message": f"Error deleting connection: {str(e)}",
                "error": str(e)
            }
    
    def get_tables(self, connection_id: str) -> Dict[str, Any]:
        """Get all tables from a connected database"""
        try:
            connection_config = self.get_connection(connection_id)
            if not connection_config:
                return {
                    "success": False,
                    "message": "Connection not found"
                }
            
            # Rebuild connection with actual password (you might want to store this securely)
            # For now, we'll ask user to re-enter password
            return {
                "success": False,
                "message": "Password required to access tables. Please reconnect."
            }
            
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return {
                "success": False,
                "message": f"Error getting tables: {str(e)}",
                "error": str(e)
            }
    
    def get_tables_with_password(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get all tables from database with password"""
        try:
            connection_string = self._build_connection_string(connection_config)
            engine = create_engine(connection_string, echo=False)
            
            with engine.connect() as conn:
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
                table_details = []
                for table_name in tables:
                    columns = inspector.get_columns(table_name)
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    
                    table_info = {
                        "table_name": table_name,
                        "columns": [
                            {
                                "name": col["name"],
                                "type": str(col["type"]),
                                "nullable": col["nullable"],
                                "primary_key": col.get("primary_key", False)
                            }
                            for col in columns
                        ],
                        "foreign_keys": [
                            {
                                "column": fk["constrained_columns"][0] if fk["constrained_columns"] else "",
                                "referenced_table": fk["referred_table"],
                                "referenced_column": fk["referred_columns"][0] if fk["referred_columns"] else ""
                            }
                            for fk in foreign_keys
                        ],
                        "row_count": self._get_table_row_count(conn, table_name)
                    }
                    table_details.append(table_info)
                
                return {
                    "success": True,
                    "tables": table_details,
                    "total_tables": len(tables)
                }
                
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return {
                "success": False,
                "message": f"Error getting tables: {str(e)}",
                "error": str(e)
            }
    
    def _get_table_row_count(self, conn, table_name: str) -> int:
        """Get row count for a table"""
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
        except:
            return 0
    
    def execute_query(self, connection_config: Dict[str, Any], query: str, limit: int = 1000) -> Dict[str, Any]:
        """Execute a query on the connected database"""
        try:
            connection_string = self._build_connection_string(connection_config)
            engine = create_engine(connection_string, echo=False)
            
            with engine.connect() as conn:
                # Add limit to query if not present
                if "LIMIT" not in query.upper():
                    query = f"{query} LIMIT {limit}"
                
                result = conn.execute(text(query))
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert rows to list of dictionaries
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "data": data,
                    "columns": list(columns),
                    "row_count": len(data),
                    "query": query
                }
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "success": False,
                "message": f"Error executing query: {str(e)}",
                "error": str(e)
            }

    def get_table_schema(self, connection_config: Dict[str, Any], table_name: str, schema_name: str = 'public') -> Dict[str, Any]:
        """Get exact table schema from INFORMATION_SCHEMA"""
        try:
            connection_string = self._build_connection_string(connection_config)
            engine = create_engine(connection_string, echo=False)
            
            with engine.connect() as conn:
                # Query INFORMATION_SCHEMA for exact column definitions
                query = text("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable,
                        column_default,
                        ordinal_position
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND table_schema = :schema_name
                    ORDER BY ordinal_position
                """)
                
                result = conn.execute(query, {
                    'table_name': table_name,
                    'schema_name': schema_name
                })
                
                columns = []
                for row in result:
                    column_info = {
                        'name': row.column_name,
                        'data_type': row.data_type,
                        'max_length': row.character_maximum_length,
                        'precision': row.numeric_precision,
                        'scale': row.numeric_scale,
                        'nullable': row.is_nullable == 'YES',
                        'default': row.column_default,
                        'position': row.ordinal_position
                    }
                    columns.append(column_info)
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "schema_name": schema_name,
                    "columns": columns,
                    "column_count": len(columns)
                }
                
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return {
                "success": False,
                "message": f"Error getting table schema: {str(e)}",
                "error": str(e)
            }

    def map_data_type_to_postgres(self, data_type: str, max_length: int = None, precision: int = None, scale: int = None) -> str:
        """Map database-specific data types to PostgreSQL equivalents"""
        data_type = data_type.lower()
        
        if data_type in ['varchar', 'char', 'character varying']:
            if max_length:
                return f"VARCHAR({max_length})"
            else:
                return "TEXT"
        elif data_type in ['text', 'longtext', 'mediumtext']:
            return "TEXT"
        elif data_type in ['int', 'integer', 'int4']:
            return "INTEGER"
        elif data_type in ['bigint', 'int8']:
            return "BIGINT"
        elif data_type in ['smallint', 'int2']:
            return "SMALLINT"
        elif data_type in ['decimal', 'numeric']:
            if precision and scale:
                return f"NUMERIC({precision},{scale})"
            elif precision:
                return f"NUMERIC({precision})"
            else:
                return "NUMERIC"
        elif data_type in ['float', 'real', 'float4']:
            return "REAL"
        elif data_type in ['double', 'double precision', 'float8']:
            return "DOUBLE PRECISION"
        elif data_type in ['boolean', 'bool']:
            return "BOOLEAN"
        elif data_type in ['date']:
            return "DATE"
        elif data_type in ['timestamp', 'datetime']:
            return "TIMESTAMP"
        elif data_type in ['time']:
            return "TIME"
        elif data_type in ['json']:
            return "JSON"
        elif data_type in ['jsonb']:
            return "JSONB"
        else:
            # Default fallback
            return "TEXT"

    def get_database_schemas(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get all available schemas from the connected database
        
        Args:
            connection_config: Database connection configuration
            
        Returns:
            Dict containing success status and list of schemas
        """
        try:
            connection_string = self._build_connection_string(connection_config)
            engine = create_engine(connection_string, echo=False)
            
            with engine.connect() as conn:
                # Query to get all schemas accessible to the current user
                query = text("""
                    SELECT 
                        schema_name,
                        schema_owner
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """)
                
                result = conn.execute(query)
                
                schemas = []
                for row in result:
                    schema_info = {
                        'name': row.schema_name,
                        'owner': row.schema_owner,
                        'description': f"Schema owned by {row.schema_owner}"
                    }
                    schemas.append(schema_info)
                
                return {
                    "success": True,
                    "schemas": schemas,
                    "total_count": len(schemas)
                }
                
        except Exception as e:
            logger.error(f"Error getting database schemas: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "schemas": [],
                "total_count": 0
            }