"""
SAP CO-PA Analytical Copilot - FastAPI Backend v2
Enhanced with Fuzzy Matching, Verification, and Deterministic Caching
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from query_engine import SAPQueryEngine, FuzzyColumnMatcher
import uvicorn
import traceback
import os
from typing import Optional, List, Dict, Any

# ==========================================
# FASTAPI APPLICATION
# ==========================================
app = FastAPI(
    title="SAP CO-PA Analytical Copilot API v2",
    description="Enterprise SAP CO-PA Query Engine with Fuzzy Matching, Verification & Deterministic Caching",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Global engine variable
engine = None

# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================
class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User's business question")

class ChatResponse(BaseModel):
    query: str
    normalized_query: Optional[str] = None
    sql: Optional[str] = None
    data: List[Dict[str, Any]] = []
    record_count: int = 0
    summary: str = ""
    error: Optional[str] = None
    clarification_needed: bool = False

class HealthResponse(BaseModel):
    status: str
    version: str
    features: List[str]
    tables_loaded: List[str] = []

class SchemaResponse(BaseModel):
    table: str
    columns: List[str]
    plant_mappings: Dict[str, str]
    ambiguous_keywords: Dict[str, List[str]]
    multi_column_triggers: Dict[str, List[str]]

# ==========================================
# STARTUP EVENT
# ==========================================
@app.on_event("startup")
async def startup_event():
    """Initialize the SAP Query Engine on server startup."""
    global engine
    print("\n" + "="*70)
    print("🚀 SAP CO-PA ANALYTICAL COPILOT v2.0 - INITIALIZING")
    print("="*70)
    
    try:
        # Get absolute path to data folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "..", "data")
        
        print(f"📁 Base directory: {base_dir}")
        print(f"📁 Data directory: {data_dir}")
        
        # Initialize engine with v2 features
        engine = SAPQueryEngine(data_dir=data_dir)
        
        print("\n✅ ENGINE INITIALIZED SUCCESSFULLY")
        print("\n🔧 ACTIVE FEATURES:")
        print("   ✓ Fuzzy Column Matching")
        print("   ✓ Plant Normalization (plant 1 → PL01)")
        print("   ✓ Verification Queries")
        print("   ✓ Deterministic Caching")
        print("   ✓ Multi-Column Material Queries")
        print("   ✓ Ambiguity Detection & Clarification")
        
        # Verify table is loaded
        tables = engine.con.execute("SHOW TABLES").fetchdf()['name'].tolist()
        print(f"\n📊 Loaded tables: {', '.join(tables)}")
        
        print("="*70 + "\n")
        
    except Exception as e:
        print("\n❌ CRITICAL: ENGINE INITIALIZATION FAILED!")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        print("="*70 + "\n")
        raise

# ==========================================
# CORE ENDPOINTS
# ==========================================
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "SAP CO-PA Analytical Copilot v2 API",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": {
            "chat": "POST /chat - Main query endpoint",
            "dashboard": "GET /dashboard - Dashboard statistics",
            "reporting": "GET /reporting - Raw master data",
            "schema": "GET /schema - Schema & normalization rules",
            "health": "GET /health - Health check",
            "clear_cache": "POST /clear-cache - Clear query cache"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns server status, version, features, and loaded tables.
    """
    if not engine:
        return {
            "status": "initializing",
            "version": "2.0.0",
            "features": [],
            "tables_loaded": []
        }
    
    try:
        tables = engine.con.execute("SHOW TABLES").fetchdf()['name'].tolist()
        return {
            "status": "healthy",
            "version": "2.0.0",
            "features": [
                "fuzzy_column_matching",
                "plant_normalization",
                "verification_queries",
                "deterministic_caching",
                "multi_column_material_response",
                "ambiguity_detection"
            ],
            "tables_loaded": tables
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "version": "2.0.0",
            "features": [],
            "tables_loaded": [],
            "error": str(e)
        }

@app.post("/chat")
async def chat(request: QueryRequest):
    """
    Main chat endpoint with fuzzy matching, verification, and entity queries.
    Returns a STREAM of JSON objects separated by newlines (NDJSON format).
    """
    print(f"\n{'─'*70}")
    print(f"💬 NEW QUERY: {request.prompt}")
    print(f"{'─'*70}")
    
    if not engine:
        raise HTTPException(
            status_code=503, 
            detail="Engine not initialized. Please ensure data is loaded."
        )
    
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # Use StreamingResponse over NDJSON format
    return StreamingResponse(
        engine.ask_stream(request.prompt), 
        media_type="application/x-ndjson"
    )

@app.get("/dashboard")
async def dashboard():
    """
    Get high-level dashboard statistics.
    
    Returns:
    - stats: Aggregated metrics (total revenue, margins, variances)
    - top_plants: Top 5 plants by net revenue
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        print("\n📊 Generating dashboard summary...")
        result = engine.get_dashboard_summary()
        print("✅ Dashboard generated\n")
        return result
    except Exception as e:
        print(f"❌ Dashboard error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reporting")
async def reporting(limit: int = 5000):
    """
    Get raw master data for reporting.
    
    Query parameters:
    - limit: Maximum number of records to return (default: 5000, max: 10000)
    
    Returns:
    - List of all records from copa_analytical_fact table
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    if limit > 50000:
        raise HTTPException(
            status_code=400, 
            detail="Limit cannot exceed 50000 records for performance reasons"
        )
    
    if limit > 10000:
        print("⚠️ WARNING: Large limit requested")
    
    try:
        print(f"\n📄 Fetching {limit} records for reporting...")
        result = engine.get_master_data(limit=limit)
        print(f"✅ Retrieved {len(result) if isinstance(result, list) else 0} records\n")
        return result
    except Exception as e:
        print(f"❌ Reporting error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """
    Get schema information and normalization rules.
    
    Returns:
    - table: Table name
    - columns: List of available columns
    - plant_mappings: Plant normalization mappings
    - ambiguous_keywords: Keywords requiring clarification
    - multi_column_triggers: Triggers for multi-column responses
    """
    return {
        "table": "copa_analytical_fact",
        "columns": FuzzyColumnMatcher.SCHEMA_COLUMNS,
        "plant_mappings": FuzzyColumnMatcher.PLANT_MAPPINGS,
        "ambiguous_keywords": FuzzyColumnMatcher.AMBIGUOUS_KEYWORDS,
        "multi_column_triggers": FuzzyColumnMatcher.MULTI_COLUMN_TRIGGERS
    }

@app.post("/clear-cache")
async def clear_cache():
    """
    Clear the query cache.
    Useful for testing or forcing fresh execution of all queries.
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        cache_size = len(engine.query_cache)
        engine.clear_cache()
        print("🧹 Query cache cleared\n")
        return {
            "message": "Query cache cleared successfully",
            "note": "All subsequent queries will be executed fresh",
            "cleared_entries": cache_size
        }
    except Exception as e:
        print(f"❌ Cache clear error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache-status")
async def cache_status():
    """
    Get current cache status and contents.
    Useful for debugging cache-related issues.
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        return {
            "cache_size": len(engine.query_cache),
            "cached_queries": list(engine.query_cache.keys()),
            "note": "Only successful queries are cached. Errors are not cached to allow retries."
        }
    except Exception as e:
        print(f"❌ Cache status error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ERROR HANDLERS
# ==========================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTP exceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Custom handler for unexpected exceptions."""
    print(f"🔥 Unhandled exception: {str(exc)}")
    traceback.print_exc()
    return {
        "error": "An unexpected error occurred",
        "detail": str(exc),
        "status_code": 500
    }

# ==========================================
# RUN SERVER
# ==========================================
if __name__ == "__main__":
    # Use 127.0.0.1 for Windows compatibility, 0.0.0.0 for Docker/Cloud
    uvicorn.run(
        app, 
        host="127.0.0.1",  # Change to "0.0.0.0" for cloud deployment
        port=8000, 
        log_level="info",
        reload=False  # Set to True for development
    )
