# ==========================================
# SAP CO-PA ANALYTICAL COPILOT - COLAB SETUP v2.1
# Enhanced with Fuzzy Matching, Verification & Entity Information Queries
# ==========================================

# ==========================================
# 1. MOUNT GOOGLE DRIVE
# ==========================================
from google.colab import drive
drive.mount('/content/drive')

# Paths - DOUBLE CHECK THESE
BACKEND_DIR = "/content/drive/MyDrive/SAP_RAG/backend"
DATA_DIR = "/content/drive/MyDrive/SAP_RAG/data"

print(f"📁 Backend Directory: {BACKEND_DIR}")
print(f"📁 Data Directory: {DATA_DIR}")

# ==========================================
# 2. INSTALL NECESSARY LIBRARIES
# ==========================================
print("\n📦 Installing required libraries...")
!pip install -q pyngrok nest-asyncio
!pip install -q fastapi uvicorn duckdb pandas requests pydantic

print("✅ Libraries installed successfully")

# ==========================================
# 3. SETUP PERSISTENT MODEL STORAGE
# ==========================================
import os
OLLAMA_DRIVE_PATH = "/content/drive/MyDrive/SAP_RAG/ollama_models"
os.makedirs(OLLAMA_DRIVE_PATH, exist_ok=True)

print(f"\n💾 Setting up persistent model storage...")
print(f"📁 Ollama models will be stored at: {OLLAMA_DRIVE_PATH}")

# Link Colab's internal Ollama folder to your Drive
!rm -rf /root/.ollama
!ln -s {OLLAMA_DRIVE_PATH} /root/.ollama

print("✅ Persistent storage configured")

# ==========================================
# 4. INSTALL & START OLLAMA
# ==========================================
print("\n🔧 Installing extraction tools (zstd)...")
!apt-get update -qq && apt-get install -y -qq zstd

print("🔧 Installing Ollama engine...")
!curl -fsSL https://ollama.com/install.sh | sh

import subprocess
import time

print("🚀 Starting Ollama service...")
# Using full path to ensure it finds the command
subprocess.Popen(["/usr/local/bin/ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(15)

# Check if it installed correctly
if os.path.exists("/usr/local/bin/ollama"):
    print("✅ Ollama installed and service started successfully!")
else:
    print("❌ Ollama installation failed. Please check output above.")
    raise SystemExit("Ollama installation failed")

# ==========================================
# 5. PULL MODEL (Persistent on Drive)
# ==========================================
print("\n🤖 Verifying/Pulling qwen2.5:7b model...")
print("⏳ This may take a while if downloading for the first time...")
!ollama pull qwen2.5:7b
print("✅ Model ready")

# ==========================================
# 6. FILE SANITY CHECK (Critical!)
# ==========================================
print("\n🔍 Verifying data files...")

csv_path = os.path.join(DATA_DIR, "sap_copa_master.csv")
backend_file = os.path.join(BACKEND_DIR, "query_engine.py")

files_ok = True

if not os.path.exists(csv_path):
    print(f"❌ ERROR: CSV file not found at {csv_path}")
    print("   Please check your Drive folder name and file name (case-sensitive!)")
    files_ok = False
else:
    print(f"✅ CSV found at {csv_path}")

if not os.path.exists(backend_file):
    print(f"❌ ERROR: query_engine.py not found at {backend_file}")
    print("   Please ensure the updated query_engine.py is uploaded to your backend folder")
    files_ok = False
else:
    print(f"✅ query_engine.py found at {backend_file}")

if not files_ok:
    raise SystemExit("Required files missing. Please fix paths and try again.")

# ==========================================
# 7. VERIFY QUERY ENGINE UPDATE
# ==========================================
print("\n🔍 Verifying query_engine.py contains v2.1 features...")

with open(backend_file, 'r') as f:
    engine_code = f.read()

required_features = [
    ("FuzzyColumnMatcher", "Fuzzy column matching class"),
    ("normalize_plant", "Plant normalization method"),
    ("query_cache", "Deterministic caching"),
    ("preprocess_query", "Query preprocessing"),
    ("verify_and_explain", "Verification & explanation"),
    ("COMPREHENSIVE ENTITY INFORMATION QUERIES", "Entity information queries"),
]

missing_features = []
for feature, description in required_features:
    if feature not in engine_code:
        missing_features.append(f"  ❌ {description} ({feature})")

if missing_features:
    print("⚠️  WARNING: query_engine.py may not have v2.1 updates:")
    for msg in missing_features:
        print(msg)
    print("\n   Please upload the updated query_engine.py with all v2.1 features")
    response = input("Continue anyway? (yes/no): ")
    if response.lower() != 'yes':
        raise SystemExit("Setup cancelled. Please update query_engine.py first.")
else:
    print("✅ All v2.1 features detected in query_engine.py")

# ==========================================
# 8. CONFIGURE BACKEND RUNNER WITH v2.1 ENDPOINTS
# ==========================================
print("\n📝 Configuring backend runner...")

colab_main_content = f"""
import os
import uvicorn
import nest_asyncio
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

sys.path.append("{BACKEND_DIR}")
from query_engine import SAPQueryEngine

nest_asyncio.apply()

# ==========================================
# FASTAPI APPLICATION
# ==========================================
app = FastAPI(
    title="SAP CO-PA Analytical Copilot API v2.1",
    description="Enterprise SAP CO-PA Query Engine with Fuzzy Matching, Verification & Entity Queries",
    version="2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

engine = None

# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================
class ChatRequest(BaseModel):
    prompt: str

# ==========================================
# STARTUP
# ==========================================
@app.on_event("startup")
async def startup():
    global engine
    print("="*60)
    print("🚀 Initializing SAP CO-PA Query Engine v2.1...")
    print("="*60)
    engine = SAPQueryEngine(data_dir="{DATA_DIR}")
    print("✅ Backend is READY with:")
    print("   - Fuzzy column matching")
    print("   - Plant normalization")
    print("   - Verification queries")
    print("   - Entity information queries")
    print("   - Streaming progress updates")
    print("="*60)

# ==========================================
# ENDPOINTS
# ==========================================
@app.post("/chat")
async def chat(request: ChatRequest):
    \"\"\"
    Main chat endpoint with streaming progress updates.
    Returns a STREAM of JSON objects separated by newlines (NDJSON format).
    \"\"\"
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    return StreamingResponse(
        engine.ask_stream(request.prompt), 
        media_type="application/x-ndjson"
    )

@app.get("/dashboard")
async def dashboard():
    \"\"\"
    Get high-level dashboard statistics.
    Returns: Total revenue, margins, variances, top plants.
    \"\"\"
    return engine.get_dashboard_summary()

@app.get("/reporting")
async def reporting(limit: int = 5000):
    \"\"\"
    Get raw master data for reporting.
    Query param: limit (default 5000)
    \"\"\"
    if limit > 10000:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 10000")
    return engine.get_master_data(limit=limit)

@app.post("/clear-cache")
async def clear_cache():
    \"\"\"
    Clear query cache (useful for testing).
    Forces fresh execution for all queries.
    \"\"\"
    cache_size = len(engine.query_cache)
    engine.clear_cache()
    return {{
        "message": "Query cache cleared successfully",
        "note": "All subsequent queries will be executed fresh",
        "cleared_entries": cache_size
    }}

@app.get("/cache-status")
async def cache_status():
    \"\"\"
    Get current cache status and contents.
    Useful for debugging cache-related issues.
    \"\"\"
    return {{
        "cache_size": len(engine.query_cache),
        "cached_queries": list(engine.query_cache.keys()),
        "note": "Only successful queries are cached. Errors are not cached to allow retries."
    }}

@app.get("/health")
async def health_check():
    \"\"\"
    Health check endpoint.
    \"\"\"
    return {{
        "status": "healthy",
        "version": "2.1",
        "features": [
            "fuzzy_column_matching",
            "plant_normalization",
            "verification_queries",
            "entity_information_queries",
            "smart_caching",
            "extended_timeout"
        ]
    }}

@app.get("/schema")
async def get_schema():
    \"\"\"
    Get available schema columns and normalization rules.
    \"\"\"
    from query_engine import FuzzyColumnMatcher

    return {{
        "table": "copa_analytical_fact",
        "columns": FuzzyColumnMatcher.SCHEMA_COLUMNS,
        "plant_mappings": FuzzyColumnMatcher.PLANT_MAPPINGS,
        "ambiguous_keywords": FuzzyColumnMatcher.AMBIGUOUS_KEYWORDS,
        "multi_column_triggers": FuzzyColumnMatcher.MULTI_COLUMN_TRIGGERS
    }}

# ==========================================
# RUN SERVER
# ==========================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
"""

with open("/content/run_backend.py", "w") as f:
    f.write(colab_main_content)

print("✅ Backend runner configured with v2.1 endpoints")
print("   - /chat (with fuzzy matching, verification & entity queries)")
print("   - /dashboard")
print("   - /reporting")
print("   - /clear-cache")
print("   - /cache-status (NEW)")
print("   - /health")
print("   - /schema")

# ==========================================
# 9. START NGROK TUNNEL
# ==========================================
print("\n🌐 Setting up public URL with ngrok...")

from pyngrok import ngrok

# --- GET TOKEN FROM: https://dashboard.ngrok.com/get-started/your-authtoken ---
NGROK_TOKEN = "39Q95oIkBkhnO8n2WthPrZFgS10_5Prwz9bcbRzquyDHpdoAv"
ngrok.set_auth_token(NGROK_TOKEN)

# Kill any existing tunnels
ngrok.kill()

# Create new tunnel
public_url = ngrok.connect(8000).public_url

print(f"\n\n{'='*70}")
print(f"{'🟢 SAP CO-PA ANALYTICAL COPILOT v2.1 - BACKEND ONLINE':^70}")
print(f"{'='*70}")
print(f"\n🔗 PUBLIC URL: {public_url}")
print(f"\n📋 AVAILABLE ENDPOINTS:")
print(f"   • {public_url}/chat           - Main query endpoint")
print(f"   • {public_url}/dashboard      - Dashboard statistics")
print(f"   • {public_url}/reporting      - Raw master data")
print(f"   • {public_url}/clear-cache    - Clear query cache")
print(f"   • {public_url}/cache-status   - View cache contents (NEW)")
print(f"   • {public_url}/health         - Health check")
print(f"   • {public_url}/schema         - Schema information")
print(f"   • {public_url}/docs           - Interactive API docs")
print(f"\n📢 NEXT STEPS:")
print(f"   1. Copy the PUBLIC URL above")
print(f"   2. Paste it into your frontend App.jsx (replace BASE_URL)")
print(f"   3. Test with these sample queries:")
print(f"      - 'What is the total overhead for plant 1?'")
print(f"      - 'Show me material MAT200000'")
print(f"      - 'Give me information of plant 2'")
print(f"      - 'Information about customer VitaStore'")
print(f"      - 'Verify that plant 2 net revenue is 50000'")
print(f"\n{'='*70}\n")

# ==========================================
# 10. RUN THE SERVER
# ==========================================
print("🚀 Starting FastAPI server...\n")
print("⚠️  Keep this cell running - DO NOT interrupt!")
print("="*70 + "\n")

%cd {BACKEND_DIR}
!python /content/run_backend.py
