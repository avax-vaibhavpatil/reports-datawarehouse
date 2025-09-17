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
    
    def map_pandas_to_postgres_type(self, pandas_dtype: str) -> str:
        """Convert pandas data types to PostgreSQL data types"""
        type_mapping = {
            'int64': 'BIGINT',
            'int32': 'INTEGER', 
            'int16': 'SMALLINT',
            'float64': 'DOUBLE PRECISION',
            'float32': 'REAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP',
            'object': 'TEXT',
        }
        dtype_str = str(pandas_dtype)
        postgres_type = type_mapping.get(dtype_str, 'TEXT')
        self.logger.debug(f"Mapped {dtype_str} -> {postgres_type}")
        return postgres_type
    
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
