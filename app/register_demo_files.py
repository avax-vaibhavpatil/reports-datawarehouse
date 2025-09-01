import pandas as pd
from pathlib import Path
import logging
from services.file_service import FileService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_demo_files():
    """Register demo Excel files in the file service for relationship analysis"""
    
    file_service = FileService()
    data_dir = Path("data/uploads")
    
    logger.info("Registering demo Excel files in the file service...")
    
    # List of demo files to register
    demo_files = [
        "customers.xlsx",
        "orders.xlsx", 
        "products.xlsx",
        "employees.xlsx",
        "sales.xlsx"
    ]
    
    registered_count = 0
    
    for filename in demo_files:
        file_path = data_dir / filename
        
        if file_path.exists():
            try:
                # Extract columns from the file
                columns = file_service.extract_columns(str(file_path))
                
                if columns:
                    # Register the file
                    file_service.register_file(filename, columns)
                    logger.info(f"✅ Registered {filename} with {len(columns)} columns")
                    registered_count += 1
                else:
                    logger.warning(f"⚠️ Could not extract columns from {filename}")
                    
            except Exception as e:
                logger.error(f"❌ Error registering {filename}: {e}")
        else:
            logger.warning(f"⚠️ File {filename} not found")
    
    logger.info(f"🎯 Registration complete! {registered_count}/{len(demo_files)} files registered")
    
    # Show all registered files
    all_files = file_service.get_all_files_metadata()
    logger.info(f"📋 Total files in system: {len(all_files)}")
    
    for file_info in all_files:
        logger.info(f"   - {file_info['filename']}: {len(file_info['columns'])} columns")
    
    return registered_count

if __name__ == "__main__":
    register_demo_files() 