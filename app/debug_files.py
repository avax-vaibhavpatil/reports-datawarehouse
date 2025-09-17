import os
from pathlib import Path
from services.file_service import FileService

def debug_file_scanning():
    """Debug why demo files aren't being detected"""
    
    print("🔍 Debugging file scanning...")
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check data/uploads directory
    data_dir = Path("data/uploads")
    print(f"Data directory: {data_dir}")
    print(f"Data directory exists: {data_dir.exists()}")
    
    # List all files in the directory
    print("\n📁 All files in data/uploads:")
    for file_path in data_dir.iterdir():
        if file_path.is_file():
            print(f"  - {file_path.name} (size: {file_path.stat().st_size} bytes)")
    
    # Check specific demo files
    demo_files = ["customers.xlsx", "orders.xlsx", "products.xlsx", "employees.xlsx", "sales.xlsx"]
    print(f"\n🎯 Checking demo files:")
    for filename in demo_files:
        file_path = data_dir / filename
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0
        print(f"  - {filename}: exists={exists}, size={size}")
    
    # Test FileService directly
    print(f"\n🔧 Testing FileService:")
    file_service = FileService()
    
    # Test file validation
    print(f"\n✅ File validation test:")
    for filename in demo_files:
        is_valid = file_service.is_valid_file(filename)
        print(f"  - {filename}: valid={is_valid}")
    
    # Test column extraction
    print(f"\n📊 Column extraction test:")
    for filename in demo_files:
        file_path = data_dir / filename
        if file_path.exists():
            try:
                columns = file_service.extract_columns(str(file_path))
                print(f"  - {filename}: {len(columns)} columns - {columns}")
            except Exception as e:
                print(f"  - {filename}: ERROR - {e}")
    
    # Test get_all_files_metadata
    print(f"\n📋 get_all_files_metadata test:")
    all_files = file_service.get_all_files_metadata()
    print(f"Total files found: {len(all_files)}")
    for file_info in all_files:
        print(f"  - {file_info['filename']}: {len(file_info['columns'])} columns")

if __name__ == "__main__":
    debug_file_scanning() 