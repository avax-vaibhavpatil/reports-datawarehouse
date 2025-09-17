import pandas as pd
from typing import List, Dict, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RelationshipService:
    def __init__(self):
        self.logger = logger
        
    def analyze_relationships(self, files_metadata: List[Dict]) -> List[Dict]:
        """
        Analyze relationships between columns across different files
        """
        self.logger.info(f"Analyzing relationships for {len(files_metadata)} files")
        
        relationships = []
        
        # Compare each file with every other file
        for i, file1 in enumerate(files_metadata):
            for j, file2 in enumerate(files_metadata):
                if i >= j:  # Skip self-comparison and duplicate comparisons
                    continue
                    
                self.logger.info(f"Comparing {file1['filename']} with {file2['filename']}")
                
                # Get file paths for data analysis
                file1_path = Path("data/uploads") / file1['filename']
                file2_path = Path("data/uploads") / file2['filename']
                
                # Analyze relationships between these two files
                file_relationships = self._analyze_file_relationships(
                    file1, file2, file1_path, file2_path
                )
                
                relationships.extend(file_relationships)
        
        self.logger.info(f"Found {len(relationships)} relationships")
        return relationships
    
    def _analyze_file_relationships(self, file1: Dict, file2: Dict, 
                                  file1_path: Path, file2_path: Path) -> List[Dict]:
        """
        Analyze relationships between two specific files
        """
        relationships = []
        
        # Compare each column in file1 with each column in file2
        for col1 in file1['columns']:
            for col2 in file2['columns']:
                relationship = self._analyze_column_relationship(
                    file1['filename'], col1, file2['filename'], col2,
                    file1_path, file2_path
                )
                
                if relationship:
                    relationships.append(relationship)
        
        return relationships
    
    def _analyze_column_relationship(self, file1_name: str, col1: str,
                                   file2_name: str, col2: str,
                                   file1_path: Path, file2_path: Path) -> Dict:
        """
        Analyze relationship between two specific columns
        """
        self.logger.info(f"Analyzing: {file1_name}.{col1} vs {file2_name}.{col2}")
        
        # Rule 1: Column Name Matching
        name_match = col1.lower() == col2.lower()
        name_score = 1 if name_match else 0
        
        # Rule 2: Data Type Matching
        type_match, data_type1, data_type2 = self._check_data_types(file1_path, col1, file2_path, col2)
        type_score = 1 if type_match else 0
        
        # Rule 3: Value Overlap Analysis
        overlap_score = self._check_value_overlap(file1_path, col1, file2_path, col2)
        
        # Calculate total score
        total_score = name_score + type_score + overlap_score
        
        # Determine relationship strength
        if total_score >= 2:
            strength = "strong"
        elif total_score == 1:
            strength = "medium"
        else:
            strength = "weak"
        
        # Only return relationships with at least medium strength
        if total_score >= 1:
            return {
                "from_table": file1_name,
                "from_column": col1,
                "to_table": file2_name,
                "to_column": col2,
                "strength": strength,
                "score": total_score,
                "name_match": name_match,
                "type_match": type_match,
                "value_overlap": overlap_score > 0,
                "data_types": {
                    "from": data_type1,
                    "to": data_type2
                }
            }
        
        return None
    
    def _check_data_types(self, file1_path: Path, col1: str, 
                          file2_path: Path, col2: str) -> Tuple[bool, str, str]:
        """
        Check if two columns have the same data type
        """
        try:
            # Read small sample of data to determine types
            if file1_path.suffix in ['.xlsx', '.xls']:
                df1 = pd.read_excel(file1_path, usecols=[col1], nrows=100)
            else:
                df1 = pd.read_csv(file1_path, usecols=[col1], nrows=100)
                
            if file2_path.suffix in ['.xlsx', '.xls']:
                df2 = pd.read_excel(file2_path, usecols=[col2], nrows=100)
            else:
                df2 = pd.read_csv(file2_path, usecols=[col2], nrows=100)
            
            # Get data types
            type1 = str(df1[col1].dtype)
            type2 = str(df2[col2].dtype)
            
            # Check if types are compatible
            type_match = self._are_types_compatible(type1, type2)
            
            return type_match, type1, type2
            
        except Exception as e:
            self.logger.warning(f"Error checking data types: {e}")
            return False, "unknown", "unknown"
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """
        Check if two data types are compatible for relationships
        """
        # Group compatible types
        numeric_types = ['int64', 'float64', 'int32', 'float32']
        text_types = ['object', 'string']
        
        # Both numeric
        if type1 in numeric_types and type2 in numeric_types:
            return True
        
        # Both text
        if type1 in text_types and type2 in text_types:
            return True
        
        # Exact match
        if type1 == type2:
            return True
        
        return False
    
    def _check_value_overlap(self, file1_path: Path, col1: str, 
                            file2_path: Path, col2: str) -> int:
        """
        Check if there's any value overlap between two columns
        """
        try:
            # Read small sample of data for overlap analysis
            if file1_path.suffix in ['.xlsx', '.xls']:
                df1 = pd.read_excel(file1_path, usecols=[col1], nrows=1000)
            else:
                df1 = pd.read_csv(file1_path, usecols=[col1], nrows=1000)
                
            if file2_path.suffix in ['.xlsx', '.xls']:
                df2 = pd.read_excel(file2_path, usecols=[col2], nrows=1000)
            else:
                df2 = pd.read_csv(file2_path, usecols=[col2], nrows=1000)
            
            # Get unique values
            values1 = set(df1[col1].dropna().astype(str))
            values2 = set(df2[col2].dropna().astype(str))
            
            # Check for overlap
            overlap = values1.intersection(values2)
            
            if len(overlap) > 0:
                self.logger.info(f"Found {len(overlap)} overlapping values between {col1} and {col2}")
                return 1
            else:
                return 0
                
        except Exception as e:
            self.logger.warning(f"Error checking value overlap: {e}")
            return 0
    
    def get_relationship_summary(self, relationships: List[Dict]) -> Dict:
        """
        Get a summary of all detected relationships
        """
        if not relationships:
            return {"total_relationships": 0, "summary": "No relationships detected"}
        
        strong_count = len([r for r in relationships if r['strength'] == 'strong'])
        medium_count = len([r for r in relationships if r['strength'] == 'medium'])
        weak_count = len([r for r in relationships if r['strength'] == 'weak'])
        
        return {
            "total_relationships": len(relationships),
            "strong_relationships": strong_count,
            "medium_relationships": medium_count,
            "weak_relationships": weak_count,
            "summary": f"Found {len(relationships)} relationships: {strong_count} strong, {medium_count} medium, {weak_count} weak"
        } 