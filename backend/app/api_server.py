"""
FastAPI backend server for the Concord semantic analysis system.

Provides REST API endpoints for the React frontend to upload files
and receive semantic analysis results with comprehensive debug logging.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import tempfile
import os
from pathlib import Path
import shutil
import json

# Import the semantic analysis pipeline
from app.process import analyze_files, ProcessResult
from display.display_model import DisplayContext

app = FastAPI(
    title="Concord Semantic Analysis API",
    description="REST API for behavioral consistency analysis of codebases",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisAPI:
    """API handlers for semantic analysis endpoints."""
    
    def __init__(self):
        # Ensure temp directory exists
        self.temp_dir = Path("temp_uploads")
        self.temp_dir.mkdir(exist_ok=True)
    
    def cleanup_temp_files(self, file_paths: List[Path]):
        """Clean up temporary uploaded files."""
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Warning: Could not delete temp file {file_path}: {e}")

api = AnalysisAPI()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Concord Semantic Analysis API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "api": "online",
        "semantic_engine": "ready",
        "debug_logging": "enabled"
    }

@app.post("/api/analyze")
async def analyze_files_endpoint(
    readme: Optional[UploadFile] = File(None),
    spec: Optional[UploadFile] = File(None), 
    test: Optional[UploadFile] = File(None)
):
    """
    Analyze uploaded files for behavioral consistency.
    
    Args:
        readme: README documentation file (.md, .txt, .rst)
        spec: API specification file (.yml, .yaml, .json)
        test: Test file (.py, .java, .js, .ts, .cs, .go, .rs)
    
    Returns:
        DisplayContext: Three-tier analysis results ready for UI display
    """
    
    # Validate at least one file is provided
    uploaded_files = [f for f in [readme, spec, test] if f is not None]
    if not uploaded_files:
        raise HTTPException(
            status_code=400,
            detail="At least one file must be uploaded (readme, spec, or test)"
        )
    
    temp_file_paths = []
    
    try:
        # Save uploaded files to temporary directory
        file_paths = []
        
        for file_obj in uploaded_files:
            if file_obj.filename:
                # Create temporary file with original extension
                temp_file = api.temp_dir / f"{file_obj.filename}"
                temp_file_paths.append(temp_file)
                
                # Save file contents
                with open(temp_file, "wb") as buffer:
                    content = await file_obj.read()
                    buffer.write(content)
                
                file_paths.append(temp_file)
        
        # Run semantic analysis with debug logging enabled
        print(f"🔍 Analyzing {len(file_paths)} files: {[f.name for f in file_paths]}")
        display_context = analyze_files(file_paths)
        
        # Format response for frontend
        response_data = {
            "behavioral_units": [],
            "total_behaviors": 0,
            "total_contradictions": 0,
            "risk_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "processing_info": {
                "evidence_count": 0,  # TODO: Track evidence count
                "claims_count": len([claim for unit in display_context.behavioral_units for claim in unit.claims]),
                "analysis_count": len(display_context.behavioral_units),
                "evaluation_count": len(display_context.behavioral_units),
                "files_processed": len(file_paths),
                "session_logged": True
            }
        }
        
        # Extract behavioral units
        if hasattr(display_context, 'behavioral_units') and display_context.behavioral_units:
            response_data["behavioral_units"] = []
            
            for i, unit in enumerate(display_context.behavioral_units):
                # Handle source coverage - convert Pydantic model to dict
                source_coverage = getattr(unit, 'source_coverage', None)
                if source_coverage:
                    source_coverage_dict = {
                        "test": getattr(source_coverage, 'test', False),
                        "api_spec": getattr(source_coverage, 'api_spec', False),
                        "readme": getattr(source_coverage, 'readme', False)
                    }
                else:
                    source_coverage_dict = {"test": False, "api_spec": False, "readme": False}
                
                # Handle structural warnings - convert enums to strings
                warnings = getattr(unit, 'structural_warnings', [])
                warnings_list = [w.value if hasattr(w, 'value') else str(w) for w in warnings] if warnings else []
                
                # Handle risk band - convert enum to string  
                risk_band = getattr(unit, 'risk_band', None)
                risk_band_str = risk_band.value if risk_band and hasattr(risk_band, 'value') else 'medium'
                
                unit_data = {
                    "endpoint": getattr(unit, 'endpoint', f"Unit {i+1}"),
                    "condition": getattr(unit, 'condition', "default"),
                    "assertion_state": {
                        "assertions": [],
                        "has_conflicts": False
                    },
                    "source_coverage": source_coverage_dict,
                    "structural_warnings": warnings_list,
                    "risk_band": risk_band_str,
                    "coverage_score": getattr(unit, 'coverage_score', 0.5),
                    "confidence_score": getattr(unit, 'confidence_score', 0.5),
                    "semantic_description": getattr(unit, 'semantic_description', None)
                }
                
                # Extract assertion state
                if hasattr(unit, 'assertion_state'):
                    assertion_state = unit.assertion_state
                    unit_data["assertion_state"]["has_conflicts"] = getattr(assertion_state, 'has_conflicts', False)
                    
                    if hasattr(assertion_state, 'assertions'):
                        for assertion in assertion_state.assertions:
                            # Convert set to list for JSON serialization
                            sources = getattr(assertion, 'sources', set())
                            sources_list = [s.value if hasattr(s, 'value') else str(s) for s in sources] if sources else []
                            
                            unit_data["assertion_state"]["assertions"].append({
                                "assertion": getattr(assertion, 'assertion', str(assertion)),
                                "sources": sources_list,
                                "is_conflicted": getattr(assertion, 'is_conflicted', False)
                            })
                
                response_data["behavioral_units"].append(unit_data)
        
        # Calculate totals
        response_data["total_behaviors"] = len(response_data["behavioral_units"])
        response_data["total_contradictions"] = sum(
            1 for unit in response_data["behavioral_units"] 
            if unit["assertion_state"]["has_conflicts"]
        )
        
        # Calculate risk distribution
        for unit in response_data["behavioral_units"]:
            risk_band = unit.get("risk_band", "medium")
            if risk_band in response_data["risk_distribution"]:
                response_data["risk_distribution"][risk_band] += 1
        
        print(f"✅ Analysis complete: {response_data['total_behaviors']} behaviors, {response_data['total_contradictions']} contradictions")
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    finally:
        # Clean up temporary files
        api.cleanup_temp_files(temp_file_paths)

@app.get("/api/debug/logs")
async def list_debug_logs():
    """List available debug log files."""
    debug_dir = Path("../debug")  # backend/debug/ directory
    if not debug_dir.exists():
        return {"logs": []}
    
    log_files = []
    for file in debug_dir.glob("process_log_*.txt"):
        log_files.append({
            "filename": file.name,
            "size": file.stat().st_size,
            "created": file.stat().st_ctime,
            "session_id": file.stem.replace("process_log_", "")
        })
    
    # Sort by creation time (newest first)
    log_files.sort(key=lambda x: x["created"], reverse=True)
    
    return {"logs": log_files}

@app.get("/api/debug/logs/{session_id}")
async def get_debug_log(session_id: str):
    """Get a specific debug log by session ID."""
    debug_dir = Path("../debug")
    log_file = debug_dir / f"process_log_{session_id}.txt"
    json_file = debug_dir / f"process_log_{session_id}.json"
    
    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Debug log not found for session {session_id}"
        )
    
    # Read log contents
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    json_content = None
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
    
    return {
        "session_id": session_id,
        "log_content": log_content,
        "json_summary": json_content
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Concord Semantic Analysis API...")
    print("📋 Available endpoints:")
    print("   GET  / - Health check")
    print("   POST /api/analyze - File analysis")
    print("   GET  /api/debug/logs - List debug logs")
    print("   GET  /api/debug/logs/{session_id} - Get specific log")
    print("🌐 Frontend CORS enabled for localhost:5173 and localhost:3000")
    print("📁 Debug logs will be saved to debug/ directory")
    print("📖 API documentation available at http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )