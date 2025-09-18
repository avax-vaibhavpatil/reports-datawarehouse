from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import file_routes, relationship_routes, column_mapping_routes, sql_query_routes, schema_editor_routes
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="Excel Generator API",
    description="A FastAPI backend for processing Excel files with relationship detection",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(file_routes.router)
app.include_router(relationship_routes.router)
app.include_router(column_mapping_routes.router)
app.include_router(sql_query_routes.router)
app.include_router(schema_editor_routes.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Excel Generator API with relationship detection...")
    logger.info("API is ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Excel Generator API...")

@app.get("/")
async def root():
    return {
        "message": "Excel Generator API with Relationship Detection",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/files/health",
        "relationships": "/api/relationships/health",
        "column-mapping": "/api/column-mapping/health",
        "sql-query": "/api/sql-query/tables"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
#sahil 
#vaibhav
