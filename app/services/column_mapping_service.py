import pandas as pd
from typing import List, Dict, Set, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ColumnMappingService:
    def __init__(self):
        self.logger = logger
        self.selected_columns: Dict[str, List[str]] = {}  # table_name -> [columns]
        self.column_mappings: List[Dict] = []  # relationships between selected columns
        
    def select_columns(self, table_name: str, columns: List[str]) -> Dict:
        """Select columns from a specific table"""
        # If table already has selected columns, add to them (avoid duplicates)
        if table_name in self.selected_columns:
            existing_columns = set(self.selected_columns[table_name])
            new_columns = set(columns)
            # Add new columns to existing ones
            all_columns = list(existing_columns.union(new_columns))
            self.selected_columns[table_name] = all_columns
            self.logger.info(f"Added columns to {table_name}: {columns}. Total: {all_columns}")
        else:   
            # New table selection
            self.selected_columns[table_name] = columns
            self.logger.info(f"Selected columns from {table_name}: {columns}")
        
        # Update mappings when new columns are selected
        self._update_mappings()
        
        return {
            "table_name": table_name,
            "selected_columns": self.selected_columns[table_name],
            "message": f"Selected {len(self.selected_columns[table_name])} columns from {table_name}"
        }
    
    def deselect_columns(self, table_name: str, columns: List[str]) -> Dict:
        """Deselect columns from a specific table"""
        if table_name in self.selected_columns:
            current_selected = set(self.selected_columns[table_name])
            to_remove = set(columns)
            remaining = list(current_selected - to_remove)
            
            if remaining:
                self.selected_columns[table_name] = remaining
                self.logger.info(f"Deselected columns from {table_name}: {columns}. Remaining: {remaining}")
            else:
                del self.selected_columns[table_name]
                self.logger.info(f"Deselected all columns from {table_name}")
                
            self._update_mappings()
            
            return {
                "table_name": table_name,
                "selected_columns": remaining if remaining else [],
                "message": f"Deselected {len(columns)} columns from {table_name}"
            }
        
        return {"message": f"No columns selected for table {table_name}"}
    
    def get_selected_columns_summary(self) -> Dict:
        """Get summary of all selected columns across tables"""
        total_tables = len(self.selected_columns)
        total_columns = sum(len(cols) for cols in self.selected_columns.values())
        
        return {
            "total_tables": total_tables,
            "total_columns": total_columns,
            "tables": [
                {
                    "table_name": table_name,
                    "selected_columns": columns,
                    "column_count": len(columns)
                }
                for table_name, columns in self.selected_columns.items()    
            ]
        }
    
    def _update_mappings(self):
        """Update column mappings based on current selections"""
        self.column_mappings = []
        
        if len(self.selected_columns) < 2:
            return
            
        # Get all selected columns across tables
        all_selections = []
        for table_name, columns in self.selected_columns.items():
            for column in columns:
                all_selections.append({
                    "table": table_name,
                    "column": column,
                    "full_name": f"{table_name}.{column}"
                })
        
        self.logger.info(f"Analyzing relationships between {len(all_selections)} selected columns")
        
        # Find relationships between selected columns
        for i, sel1 in enumerate(all_selections):
            for j, sel2 in enumerate(all_selections):
                if i >= j:  # Skip self and duplicate comparisons
                    continue
                    
                relationship = self._analyze_column_relationship(sel1, sel2)
                if relationship:
                    self.column_mappings.append(relationship)
                    self.logger.info(f"Found relationship: {relationship['description']}")
        
        self.logger.info(f"Total relationships found: {len(self.column_mappings)}")
    
    def _analyze_column_relationship(self, sel1: Dict, sel2: Dict) -> Dict:
        """Analyze relationship between two selected columns"""
        # Check if columns have the same name
        name_match = sel1["column"].lower() == sel2["column"].lower()
        
        # Check if they're from different tables
        different_tables = sel1["table"] != sel2["table"]
        
        # Only create mapping if columns are related and from different tables
        if name_match and different_tables:
            return {
                "from_table": sel1["table"],
                "from_column": sel1["column"],
                "to_table": sel2["table"],
                "to_column": sel2["column"],
                "relationship": "=",
                "description": f"{sel1['table']}.{sel1['column']} = {sel2['table']}.{sel2['column']}",
                "type": "same_name_relationship"
            }
        
        return None

    def manual_relationship(self, from_table: str, from_column: str, to_table: str, to_column: str, relationship: str) -> Dict:
        """Create a manual relationship between two columns"""
        return {
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column,
            "relationship": relationship,
            "description": f"{from_table}.{from_column} {relationship} {to_table}.{to_column}",
            "type": "manual_relationship"
        }
    
    def get_column_mappings(self) -> List[Dict]:
        """Get all column mappings"""
        return self.column_mappings
    
    def get_mapping_summary(self) -> Dict:
        """Get summary of column mappings"""
        return {
            "total_mappings": len(self.column_mappings),
            "mappings": self.column_mappings,
            "summary": f"Found {len(self.column_mappings)} column relationships"
        }
    
    def clear_all_selections(self) -> Dict:
        """Clear all column selections and mappings"""
        self.selected_columns.clear()
        self.column_mappings.clear()
        self.logger.info("Cleared all column selections and mappings")
        
        return {
            "message": "All column selections and mappings cleared",
            "total_tables": 0,
            "total_columns": 0
        }
    
    def get_combined_table_structure(self) -> Dict:
        """Get the structure for the new combined table"""
        if not self.selected_columns:
            return {"message": "No columns selected"}
        
        # Collect all unique column names
        all_columns = set()
        for columns in self.selected_columns.values():
            all_columns.update(columns)
        
        # Create table structure
        table_structure = {
            "table_name": "combined_table",
            "columns": sorted(list(all_columns)),
            "source_tables": list(self.selected_columns.keys()),
            "column_count": len(all_columns),
            "mappings": self.column_mappings
        }
        
        return table_structure 