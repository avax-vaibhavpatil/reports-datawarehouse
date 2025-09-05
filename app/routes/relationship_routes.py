from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging
from ..services.relationship_service import RelationshipService
from ..services.file_service import FileService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/relationships", tags=["relationships"])

def get_relationship_service():
    return RelationshipService()

def get_file_service():
    return FileService()

@router.get("/analyze")
async def analyze_relationships(
    relationship_service: RelationshipService = Depends(get_relationship_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Analyze relationships between all uploaded files
    """
    logger.info("Relationship analysis request received")
    
    try:
        # Get all files metadata first
        files_metadata = file_service.get_all_files_metadata()
        
        if not files_metadata:
            return JSONResponse(
                content={"message": "No files found for analysis", "relationships": []},
                status_code=200
            )
        
        logger.info(f"Analyzing relationships for {len(files_metadata)} files")
        
        # Analyze relationships
        relationships = relationship_service.analyze_relationships(files_metadata)
        
        # Get summary
        summary = relationship_service.get_relationship_summary(relationships)
        
        response = {
            "files_analyzed": len(files_metadata),
            "relationships": relationships,
            "summary": summary
        }
        
        logger.info(f"Relationship analysis completed: {summary['summary']}")
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        logger.error(f"Error analyzing relationships: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing relationships: {str(e)}"
        )

@router.get("/summary")
async def get_relationships_summary(
    relationship_service: RelationshipService = Depends(get_relationship_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Get a summary of detected relationships
    """
    logger.info("Relationship summary request received")
    
    try:
        # Get all files metadata
        files_metadata = file_service.get_all_files_metadata()
        
        if not files_metadata:
            return JSONResponse(
                content={"message": "No files found", "summary": "No relationships to analyze"},
                status_code=200
            )
        
        # Analyze relationships
        relationships = relationship_service.analyze_relationships(files_metadata)
        
        # Get summary
        summary = relationship_service.get_relationship_summary(relationships)
        
        response = {
            "files_count": len(files_metadata),
            "summary": summary
        }
        
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        logger.error(f"Error getting relationship summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting relationship summary: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check for relationship service
    """
    return {"status": "healthy", "service": "relationship-detection"} 