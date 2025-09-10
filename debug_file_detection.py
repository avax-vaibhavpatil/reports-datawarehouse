#!/usr/bin/env python3
"""
Debug script to test file detection
"""
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.services.file_service import FileService
from app.config import UPLOAD_DIR

def main():
    print("🔍 Debugging File Detection")
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Upload directory exists: {UPLOAD_DIR.exists()}")
    
    # List all files
    print("\n📁 Files in upload directory:")
    if UPLOAD_DIR.exists():
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                print(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
    
    # Test FileService
    print("\n🔧 Testing FileService:")
    file_service = FileService()
    
    try:
        metadata = file_service.get_all_files_metadata()
        print(f"✅ Found {len(metadata)} files:")
        for file_data in metadata:
            print(f"  - {file_data['filename']}: {len(file_data['columns'])} columns")
            print(f"    Columns: {file_data['columns'][:5]}{'...' if len(file_data['columns']) > 5 else ''}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 