import re
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ColumnMatchingService:
    """Service for automatically detecting column relationships between tables"""
    
    def __init__(self):
        self.logger = logger
    
    def extract_table_prefix(self, column_name: str) -> Tuple[str, str]:
        """
        Extract table prefix and suffix from column name
        Returns: (prefix, suffix)
        Examples:
        - 'lg_voucher_no' -> ('lg_', 'voucher_no')
        - 'lgd_acc_code' -> ('lgd_', 'acc_code')
        - 'ins_siscon_code' -> ('ins_', 'siscon_code')
        """
        # Common table prefixes pattern (2-4 characters followed by underscore)
        match = re.match(r'^([a-z]{2,4})_(.+)$', column_name.lower())
        if match:
            return match.group(1) + '_', match.group(2)
        return '', column_name
    
    def find_matching_columns(self, left_columns: List[str], right_columns: List[str]) -> List[Dict]:
        """
        Find matching columns between two tables based on exact suffix matching
        
        Args:
            left_columns: List of column names from left table
            right_columns: List of column names from right table
            
        Returns:
            List of matching relationships with confidence scores
        """
        matches = []
        
        # Extract suffixes from both tables
        left_suffixes = {}
        right_suffixes = {}
        
        for col in left_columns:
            prefix, suffix = self.extract_table_prefix(col)
            if suffix:  # Only process if we found a suffix
                left_suffixes[suffix] = col
        
        for col in right_columns:
            prefix, suffix = self.extract_table_prefix(col)
            if suffix:  # Only process if we found a suffix
                right_suffixes[suffix] = col
        
        # Find exact matches
        for suffix, left_col in left_suffixes.items():
            if suffix in right_suffixes:
                right_col = right_suffixes[suffix]
                matches.append({
                    'left_column': left_col,
                    'right_column': right_col,
                    'suffix': suffix,
                    'confidence': 1.0,  # Exact match
                    'match_type': 'exact'
                })
        
        # Sort by confidence (exact matches first)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.logger.info(f"Found {len(matches)} matching columns between tables")
        return matches
    
    def suggest_relationships(self, left_table: str, left_columns: List[str], 
                           right_table: str, right_columns: List[str]) -> Dict:
        """
        Suggest relationships between two tables
        
        Args:
            left_table: Name of left table
            left_columns: List of column names from left table
            right_table: Name of right table  
            right_columns: List of column names from right table
            
        Returns:
            Dictionary with suggested relationships and metadata
        """
        try:
            matches = self.find_matching_columns(left_columns, right_columns)
            
            # Convert to relationship format expected by frontend
            relationships = []
            for match in matches:
                relationships.append({
                    'left_table': left_table,
                    'left_column': match['left_column'],
                    'operator': '=',
                    'right_table': right_table,
                    'right_column': match['right_column'],
                    'is_auto_suggested': True,
                    'confidence': match['confidence'],
                    'suffix': match['suffix']
                })
            
            return {
                'success': True,
                'relationships': relationships,
                'total_matches': len(relationships),
                'left_table': left_table,
                'right_table': right_table,
                'message': f"Found {len(relationships)} potential relationships"
            }
            
        except Exception as e:
            self.logger.error(f"Error suggesting relationships: {e}")
            return {
                'success': False,
                'relationships': [],
                'total_matches': 0,
                'error': str(e)
            }
    
    def get_table_columns(self, table_name: str, all_tables: List[Dict]) -> List[str]:
        """
        Get columns for a specific table from the tables metadata
        
        Args:
            table_name: Name of the table
            all_tables: List of table metadata from API
            
        Returns:
            List of column names for the table
        """
        for table in all_tables:
            if table['name'] == table_name:
                return table['columns']
        return []
    
    def suggest_all_relationships(self, tables: List[Dict]) -> Dict:
        """
        Suggest relationships for all possible table combinations
        
        Args:
            tables: List of table metadata
            
        Returns:
            Dictionary with all possible relationships
        """
        all_suggestions = {}
        
        for i, left_table in enumerate(tables):
            left_name = left_table['name']
            left_columns = left_table['columns']
            
            for j, right_table in enumerate(tables):
                if i != j:  # Don't match table with itself
                    right_name = right_table['name']
                    right_columns = right_table['columns']
                    
                    key = f"{left_name}->{right_name}"
                    suggestion = self.suggest_relationships(
                        left_name, left_columns, right_name, right_columns
                    )
                    all_suggestions[key] = suggestion
        
        return {
            'success': True,
            'suggestions': all_suggestions,
            'total_combinations': len(all_suggestions)
        }