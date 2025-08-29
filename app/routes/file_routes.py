from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import logging
from services.file_service import FileService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])

# Dependency to get FileService instance
def get_file_service():
    return FileService()

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload multiple Excel/CSV files and extract their column metadata
    """
    logger.info(f"Upload request received for {len(files)} files")
    
    if not files:
        logger.warning("No files provided in upload request")
        raise HTTPException(status_code=400, detail="No files provided")
    
    uploaded_files = []
    errors = []
    
    for file in files:
        logger.info(f"Processing file: {file.filename}")
        
        try:
            # Validate file
            if not file_service.is_valid_file(file.filename):
                error_msg = f"Invalid file type: {file.filename}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
            
            # Read file content
            content = await file.read()
            logger.info(f"Read {len(content)} bytes from {file.filename}")
            
            # Process file
            result = file_service.process_upload(content, file.filename)
            
            if result:
                uploaded_files.append({
                    "filename": result["filename"],
                    "columns": result["columns"]
                })
                logger.info(f"Successfully processed: {file.filename}")
            else:
                error_msg = f"Failed to process: {file.filename}"
                logger.error(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Error processing {file.filename}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    # Return response
    response = {
        "files": uploaded_files,
        "total_uploaded": len(uploaded_files),
        "total_files": len(files),
        "errors": errors
    }
    
    logger.info(f"Upload response: {response}")
    
    if uploaded_files:
        return JSONResponse(content=response, status_code=200)
    else:
        return JSONResponse(content=response, status_code=400)

@router.get("/metadata")
async def get_files_metadata(
    file_service: FileService = Depends(get_file_service)
):
    """
    Get metadata for all uploaded files
    """
    logger.info("Metadata request received")
    
    try:
        metadata = file_service.get_all_files_metadata()
        response = {
            "files": [
                {
                    "filename": file["filename"],
                    "columns": file["columns"]
                }
                for file in metadata
            ],
            "total_files": len(metadata)
        }
        logger.info(f"Metadata response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error retrieving metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve file metadata")

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    logger.info("Health check request received")
    return {"status": "healthy", "service": "Excel Generator API"} 