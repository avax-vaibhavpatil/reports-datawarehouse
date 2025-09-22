import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import logging
from ..config import UPLOAD_DIR, ALLOWED_EXTENSIONS

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
            
            if file_path.endswith(('.xlsx', '.xls')):
                logger.info("Reading Excel file headers...")
                try:
                    df = pd.read_excel(file_path, nrows=0, engine='openpyxl')
                except Exception as e:
                    logger.warning(f"Excel reading failed: {e}")
                    # Check if file is actually a CSV with wrong extension
                    if "Excel file format cannot be determined" in str(e) or "not a zip file" in str(e):
                        logger.info("File appears to be CSV with wrong extension, trying CSV method...")
                        try:
                            df = pd.read_csv(file_path, nrows=0, low_memory=False)
                            logger.info("Successfully read as CSV file")
                        except Exception as csv_e:
                            logger.error(f"CSV method also failed: {csv_e}")
                            return []
                    else:
                        # Try alternative Excel engines
                        try:
                            logger.info("Trying xlrd engine...")
                            df = pd.read_excel(file_path, nrows=0, engine='xlrd')
                        except Exception as xlrd_e:
                            logger.error(f"Xlrd engine failed: {xlrd_e}")
                            return []
                            
            elif file_path.endswith('.csv'):
                logger.info("Reading CSV file headers...")
                df = pd.read_csv(file_path, nrows=0, low_memory=False)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return []
            
            columns = df.columns.tolist()
            logger.info(f"Successfully extracted {len(columns)} columns: {columns}")
            return columns
            
        except Exception as e:
            logger.error(f"Error extracting columns from {file_path}: {e}")
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
        
        for file_path in self.upload_dir.glob('*'):
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
    
    def read_file_data(self, filename: str, sample_size: int = 100) -> Dict:
        """Read actual data from a single file"""
        try:
            file_path = self.upload_dir / filename
            
            if not file_path.exists():
                logger.error(f"File not found: {filename}")
                return {"error": f"File {filename} not found", "data": []}
            
            if not self.is_valid_file(filename):
                logger.error(f"Invalid file type: {filename}")
                return {"error": f"Invalid file type: {filename}", "data": []}
            
            logger.info(f"Reading data from {filename}, sample size: {sample_size}")
            
            # Read the file based on extension
            if filename.endswith(('.xlsx', '.xls')):
                try:
                    df = pd.read_excel(file_path, nrows=sample_size)
                except Exception as e:
                    logger.warning(f"Excel reading failed: {e}")
                    # Try to read as CSV if Excel fails
                    if "Excel file format cannot be determined" in str(e) or "not a zip file" in str(e):
                        logger.info("Trying to read as CSV...")
                        df = pd.read_csv(file_path, nrows=sample_size)
                    else:
                        raise e
            elif filename.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=sample_size)
            else:
                logger.error(f"Unsupported file type: {filename}")
                return {"error": f"Unsupported file type: {filename}", "data": []}
            
            # Convert DataFrame to list of dictionaries with proper NaN handling
            def clean_value(value):
                try:
                    # Handle pandas NaN - this is the most important check
                    if pd.isna(value):
                        return None
                    # Handle numpy NaN
                    elif hasattr(value, '__class__') and str(value) == 'nan':
                        return None
                    # Handle numpy types
                    elif hasattr(value, 'item'):  # numpy scalar
                        try:
                            return value.item()
                        except:
                            return str(value)
                    # Handle infinity
                    elif isinstance(value, float) and (value == float('inf') or value == float('-inf')):
                        return None
                    else:
                        return value
                except Exception:
                    # If anything fails, convert to string
                    return str(value)
            
            # Apply cleaning to all values directly from the original DataFrame
            data = []
            for _, row in df.iterrows():
                clean_row = {}
                for col, value in row.items():
                    clean_row[col] = clean_value(value)
                data.append(clean_row)
            
            result = {
                "filename": filename,
                "data": data,
                "total_rows": len(data),
                "columns": df.columns.tolist()
            }
            
            logger.info(f"Successfully read {len(data)} rows from {filename}")
            logger.info(f"Sample data from {filename}: {data[:2] if data else 'No data'}")
            return result
            
        except Exception as e:
            logger.error(f"Error reading file data from {filename}: {e}")
            return {"error": str(e), "data": []}
    
    def get_multiple_files_data(self, filenames: List[str], sample_size: int = 100) -> Dict[str, List[Dict]]:
        """Read data from multiple files"""
        try:
            logger.info(f"Reading data from {len(filenames)} files, sample size: {sample_size}")
            
            files_data = {}
            
            for filename in filenames:
                logger.info(f"Processing file: {filename}")
                file_result = self.read_file_data(filename, sample_size)
                
                if "error" in file_result:
                    logger.warning(f"Error reading {filename}: {file_result['error']}")
                    files_data[filename] = []
                else:
                    files_data[filename] = file_result["data"]
                    logger.info(f"Successfully read {len(file_result['data'])} rows from {filename}")
            
            logger.info(f"Completed reading data from {len(filenames)} files")
            return files_data
            
        except Exception as e:
            logger.error(f"Error reading multiple files data: {e}")
            return {}

    def get_joined_data(self, filenames: List[str], join_conditions: List[Dict], selected_columns: List[str] = None, sample_size: int = 100) -> Dict:
        """Get joined data from multiple files based on join conditions
        
        Args:
            filenames: List of file names to join
            join_conditions: List of join conditions like [{"table1": "file1.csv", "column1": "col1", "table2": "file2.csv", "column2": "col2"}]
            sample_size: Number of rows to sample from each file
        """
        try:
            logger.info(f"Getting joined data from {len(filenames)} files with {len(join_conditions)} join conditions")
            
            # Read data from all files
            files_data = {}
            for filename in filenames:
                file_result = self.read_file_data(filename, sample_size)
                if "error" not in file_result:
                    files_data[filename] = file_result["data"]
                else:
                    logger.error(f"Error reading {filename}: {file_result['error']}")
                    return {"error": f"Error reading {filename}", "data": []}
            
            if len(files_data) < 2:
                logger.error("Need at least 2 files to perform join")
                return {"error": "Need at least 2 files to perform join", "data": []}
            
            # Convert to pandas DataFrames for easier joining
            import pandas as pd
            dataframes = {}
            for filename, data in files_data.items():
                if data:  # Only create DataFrame if data exists
                    df = pd.DataFrame(data)
                    dataframes[filename] = df
                    logger.info(f"Created DataFrame for {filename} with {len(df)} rows and {len(df.columns)} columns")
            
            if len(dataframes) < 2:
                logger.error("Need at least 2 files with data to perform join")
                return {"error": "Need at least 2 files with data to perform join", "data": []}
            
            # Perform the join
            result_df = None
            file_names = list(dataframes.keys())
            
            # Start with the first file
            result_df = dataframes[file_names[0]].copy()
            logger.info(f"Starting join with {file_names[0]} ({len(result_df)} rows)")
            
            # Join with remaining files
            for i in range(1, len(file_names)):
                current_file = file_names[i]
                current_df = dataframes[current_file]
                
                # Find matching join conditions for this file pair
                matching_conditions = []
                for condition in join_conditions:
                    if (condition.get("table1") == file_names[0] and condition.get("table2") == current_file) or \
                       (condition.get("table1") == current_file and condition.get("table2") == file_names[0]):
                        matching_conditions.append(condition)
                
                if not matching_conditions:
                    logger.warning(f"No join conditions found between {file_names[0]} and {current_file}")
                    continue
                
                # Prepare join columns for multi-column join
                left_on = []
                right_on = []
                
                for condition in matching_conditions:
                    left_col = condition.get("column1")
                    right_col = condition.get("column2")
                    
                    if condition.get("table1") == current_file:
                        left_col, right_col = right_col, left_col
                    
                    if left_col in result_df.columns and right_col in current_df.columns:
                        left_on.append(left_col)
                        right_on.append(right_col)
                        logger.info(f"Adding join condition: {left_col} = {right_col}")
                    else:
                        logger.warning(f"Columns {left_col} or {right_col} not found for join")
                
                if left_on and right_on:
                    # Perform multi-column inner join
                    result_df = pd.merge(result_df, current_df, left_on=left_on, right_on=right_on, how='inner')
                    logger.info(f"After multi-column join with {current_file}: {len(result_df)} rows, {len(result_df.columns)} columns")
                else:
                    logger.warning(f"No valid join columns found for {current_file}")
            
            # Convert result back to list of dictionaries
            if result_df is not None and not result_df.empty:
                # Filter to only selected columns if specified
                if selected_columns and len(selected_columns) > 0:
                    # Find columns that exist in the joined data
                    available_columns = [col for col in selected_columns if col in result_df.columns]
                    if available_columns:
                        result_df = result_df[available_columns]
                        logger.info(f"Filtered to {len(available_columns)} selected columns: {available_columns}")
                    else:
                        logger.warning(f"None of the selected columns {selected_columns} found in joined data")
                
                # Limit the number of rows to prevent performance issues
                max_rows = min(sample_size, 50)  # Never return more than 50 rows
                if len(result_df) > max_rows:
                    result_df = result_df.head(max_rows)
                    logger.info(f"Limited joined data to {max_rows} rows (was {len(result_df)} rows)")
                
                # Clean the data for JSON serialization
                def clean_value(value):
                    try:
                        if pd.isna(value):
                            return None
                        elif hasattr(value, '__class__') and str(value) == 'nan':
                            return None
                        elif hasattr(value, 'item'):  # numpy scalar
                            return value.item()
                        elif isinstance(value, (float, int)) and (value == float('inf') or value == float('-inf')):
                            return None
                        else:
                            return value
                    except:
                        try:
                            return str(value)
                        except:
                            return None
                
                joined_data = []
                for _, row in result_df.iterrows():
                    clean_row = {col: clean_value(row[col]) for col in result_df.columns}
                    joined_data.append(clean_row)
                
                logger.info(f"Successfully created joined data with {len(joined_data)} rows and {len(result_df.columns)} columns")
                return {
                    "data": joined_data,
                    "total_rows": len(joined_data),
                    "columns": result_df.columns.tolist(),
                    "join_conditions": join_conditions
                }
            else:
                logger.warning("No data after join operation")
                return {"error": "No data after join operation", "data": []}
                
        except Exception as e:
            logger.error(f"Error performing join operation: {e}")
            return {"error": str(e), "data": []} 
        