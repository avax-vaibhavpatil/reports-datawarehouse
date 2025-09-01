import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import logging
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self._init_storage()
    
    def _init_storage(self):
        """Initialize storage directories"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage initialized at: {self.upload_dir}")
    
    def _clean_data_for_json(self, data: List[Dict]) -> List[Dict]:
        """Clean data to make it JSON serializable by handling NaN and inf values"""
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for key, value in row.items():
                if pd.isna(value):
                    cleaned_row[key] = None
                elif isinstance(value, (int, float)) and (pd.isna(value) or (isinstance(value, float) and (value == float('inf') or value == float('-inf')))):
                    cleaned_row[key] = None
                else:
                    cleaned_row[key] = value
            cleaned_data.append(cleaned_row)
        return cleaned_data
    
    def is_valid_file(self, filename: str) -> bool:
        """Check if file has valid extension"""
        extension = Path(filename).suffix.lower()
        is_valid = extension in ALLOWED_EXTENSIONS
        logger.info(f"File {filename} validation: {is_valid} (extension: {extension})")
        return is_valid
    
    def get_table_name(self, filename: str) -> str:
        """Generate table name from filename (remove extension)"""
        table_name = Path(filename).stem.lower().replace(' ', '_').replace('-', '_')
        logger.info(f"Generated table name '{table_name}' for file '{filename}'")
        return table_name
    
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk"""
        try:
            file_path = self.upload_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            logger.info(f"File saved successfully: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise
    
    def extract_columns(self, file_path: str) -> List[str]:
        """Extract column headers from Excel/CSV file using pandas"""
        try:
            logger.info(f"Extracting columns from: {file_path}")
            
            if file_path.endswith('.xlsx'):
                logger.info("Reading Excel .xlsx file headers...")
                df = pd.read_excel(file_path, nrows=0, engine='openpyxl')
            elif file_path.endswith('.xls'):
                logger.info("Reading Excel .xls file headers...")
                df = pd.read_excel(file_path, nrows=0, engine='xlrd')
            elif file_path.endswith('.csv'):
                logger.info("Reading CSV file headers...")
                df = pd.read_csv(file_path, nrows=0)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return []
            
            columns = df.columns.tolist()
            logger.info(f"Successfully extracted {len(columns)} columns: {columns}")
            return columns
            
        except Exception as e:
            logger.error(f"Error extracting columns from {file_path}: {e}")
            # Try alternative methods for Excel files
            if file_path.endswith('.xlsx'):
                try:
                    logger.info("Trying alternative .xlsx reading method...")
                    df = pd.read_excel(file_path, nrows=0)
                    columns = df.columns.tolist()
                    logger.info(f"Alternative method successful: {len(columns)} columns")
                    return columns
                except Exception as alt_e:
                    logger.error(f"Alternative method also failed: {alt_e}")
            elif file_path.endswith('.xls'):
                try:
                    logger.info("Trying alternative .xls reading method...")
                    df = pd.read_excel(file_path, nrows=0)
                    columns = df.columns.tolist()
                    return columns
                except Exception as alt_e:
                    logger.error(f"Alternative method also failed: {alt_e}")
            
            return []
    
    def get_file_metadata(self, filename: str) -> Dict:
        """Get basic file metadata"""
        file_path = self.upload_dir / filename
        if file_path.exists():
            stat = file_path.stat()
            return {
                "filename": filename,
                "size": stat.st_size,
                "modified": stat.st_mtime
            }
        return {}
    
    def get_all_files_metadata(self) -> List[Dict]:
        """Get metadata for all uploaded files"""
        files = []
        logger.info("Scanning for uploaded files...")
        logger.info(f"Upload directory: {self.upload_dir}")
        logger.info(f"Upload directory absolute: {self.upload_dir.absolute()}")
        
        # List all files in directory for debugging
        all_files_in_dir = list(self.upload_dir.glob('*'))
        logger.info(f"All files found in directory: {[f.name for f in all_files_in_dir if f.is_file()]}")
        
        for file_path in all_files_in_dir:
            if file_path.is_file() and self.is_valid_file(file_path.name):
                try:
                    columns = self.extract_columns(str(file_path))
                    files.append({
                        "filename": file_path.name,
                        "columns": columns,
                        "size": file_path.stat().st_size,
                        "table_name": self.get_table_name(file_path.name)
                    })
                    logger.info(f"Processed file: {file_path.name} with {len(columns)} columns")
                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {e}")
                    files.append({
                        "filename": file_path.name,
                        "columns": [],
                        "size": file_path.stat().st_size,
                        "table_name": self.get_table_name(file_path.name)
                    })
        
        logger.info(f"Found {len(files)} files")
        return files
    
    def process_upload(self, file_content: bytes, filename: str) -> Optional[Dict]:
        """Process uploaded file: save and extract columns"""
        logger.info(f"Processing upload: {filename} ({len(file_content)} bytes)")
        
        if not self.is_valid_file(filename):
            logger.warning(f"Invalid file type: {filename}")
            return None
        
        try:
            # Save file
            file_path = self.save_file(file_content, filename)
            logger.info(f"File saved to: {file_path}")
            
            # Extract columns
            columns = self.extract_columns(file_path)
            if not columns:
                logger.warning(f"No columns extracted from {filename}, but file was saved")
                # Return partial success - file was saved even if columns couldn't be extracted
                columns = []
            
            # Generate table name
            table_name = self.get_table_name(filename)
            
            result = {
                "filename": filename,
                "table_name": table_name,
                "columns": columns,
                "file_path": file_path
            }
            
            logger.info(f"Upload processing completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing upload {filename}: {e}")
            return None
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage"""
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {filename}")
                return True
            logger.warning(f"File not found for deletion: {filename}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False
    
    def read_file_data(self, filename: str, sample_size: int = 100) -> Optional[List[Dict]]:
        """Read actual data from Excel/CSV file"""
        try:
            file_path = self.upload_dir / filename
            logger.info(f"Looking for file at: {file_path}")
            logger.info(f"Upload dir: {self.upload_dir}")
            logger.info(f"File path exists: {file_path.exists()}")
            logger.info(f"File path absolute: {file_path.absolute()}")
            
            if not file_path.exists():
                logger.error(f"File not found: {filename}")
                return None
            
            logger.info(f"Reading data from {filename} with sample size {sample_size}")
            
            if filename.endswith('.xlsx'):
                logger.info("Reading Excel .xlsx file data...")
                df = pd.read_excel(file_path, nrows=sample_size, engine='openpyxl')
            elif filename.endswith('.xls'):
                logger.info("Reading Excel .xls file data...")
                try:
                    df = pd.read_excel(file_path, nrows=sample_size, engine='xlrd')
                except Exception as e:
                    logger.info(f"xlrd engine failed, trying default engine: {e}")
                    df = pd.read_excel(file_path, nrows=sample_size)
            elif filename.endswith('.csv'):
                logger.info("Reading CSV file data...")
                df = pd.read_csv(file_path, nrows=sample_size)
            else:
                logger.warning(f"Unsupported file type: {filename}")
                return None
            
            # Convert DataFrame to list of dictionaries
            data = df.to_dict('records')
            
            # Clean NaN values to make them JSON serializable
            cleaned_data = self._clean_data_for_json(data)
            
            logger.info(f"Successfully read {len(cleaned_data)} rows from {filename}")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error reading data from {filename}: {e}")
            # Try alternative methods for Excel files
            if filename.endswith('.xlsx'):
                try:
                    logger.info("Trying alternative .xlsx reading method...")
                    df = pd.read_excel(file_path, nrows=sample_size)
                    data = df.to_dict('records')
                    
                    # Clean NaN values in alternative method too
                    cleaned_data = self._clean_data_for_json(data)
                    
                    logger.info(f"Alternative method successful: {len(cleaned_data)} rows")
                    return cleaned_data
                except Exception as alt_e:
                    logger.error(f"Alternative method also failed: {alt_e}")
            elif filename.endswith('.xls'):
                try:
                    logger.info("Trying alternative .xls reading method...")
                    df = pd.read_excel(file_path, nrows=sample_size)
                    data = df.to_dict('records')
                    
                    # Clean NaN values in alternative method too
                    cleaned_data = self._clean_data_for_json(data)
                    
                    logger.info(f"Alternative method successful: {len(cleaned_data)} rows")
                    return cleaned_data
                except Exception as alt_e:
                    logger.error(f"Alternative method also failed: {alt_e}")
            
            return None
    
    def get_multiple_files_data(self, filenames: List[str], sample_size: int = 100) -> Dict[str, List[Dict]]:
        """Get data from multiple files"""
        result = {}
        for filename in filenames:
            data = self.read_file_data(filename, sample_size)
            if data is not None:
                result[filename] = data
            else:
                result[filename] = []
                logger.warning(f"Could not read data from {filename}")
        
        return result 