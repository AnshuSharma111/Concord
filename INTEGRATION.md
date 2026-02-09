# 🔄 Frontend-Backend Integration Guide

**Concord Semantic Analysis** - Complete integration between React frontend and FastAPI backend with automatic debug logging.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

**Windows:**
```bash
# Run from project root
start-dev.bat
```

**Mac/Linux:**
```bash
# Run from project root  
chmod +x start-dev.sh
./start-dev.sh
```

### Option 2: Manual Setup

**Terminal 1 (Backend):**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cd app
python api_server.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Access Points

- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 📋 API Endpoints

### `POST /api/analyze`
Upload files for semantic analysis
- **Files:** `readme`, `spec`, `test` (at least one required)
- **Returns:** Complete behavioral analysis with three-tier display format
- **Auto-logging:** Every request generates debug logs

### `GET /api/debug/logs`
List all debug sessions

### `GET /api/debug/logs/{session_id}`
Get detailed debug log for a specific session

## 🧪 Testing Integration

```bash
# Test the API integration
python test_integration.py
```

This will:
- ✅ Verify backend is running
- ✅ Upload sample files
- ✅ Test complete analysis pipeline
- ✅ Check debug logging
- ✅ Validate response format

## 🔍 How It Works

### File Upload Flow
1. **Frontend**: User selects files in React app
2. **API Call**: Files sent to `POST /api/analyze`  
3. **Backend**: FastAPI receives files, saves to temp directory
4. **Processing**: Files analyzed through complete semantic pipeline
5. **Logging**: Comprehensive debug log generated automatically
6. **Response**: JSON results returned to frontend
7. **Display**: React app shows three-tier analysis results
8. **Cleanup**: Temporary files removed

### Debug Logging
Every API call automatically generates:
- **Text log**: `backend/debug/process_log_TIMESTAMP.txt` - Human-readable
- **JSON summary**: `backend/debug/process_log_TIMESTAMP.json` - Machine-readable

## 📊 Response Format

```json
{
  "behavioral_units": [
    {
      "endpoint": "GET /api/users",
      "condition": "valid request", 
      "assertion_state": {
        "assertions": [...],
        "has_conflicts": false
      },
      "source_coverage": {...},
      "structural_warnings": [...],
      "risk_band": "medium",
      "coverage_score": 0.75,
      "confidence_score": 0.85
    }
  ],
  "total_behaviors": 2,
  "total_contradictions": 0,
  "risk_distribution": {
    "critical": 0,
    "high": 0, 
    "medium": 1,
    "low": 1
  },
  "processing_info": {
    "evidence_count": 15,
    "claims_count": 8,
    "analysis_count": 2,
    "evaluation_count": 2,
    "files_processed": 2,
    "session_logged": true
  }
}
```

## 🔧 Configuration

### Backend Environment Variables
```bash
# backend/app/.env
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
GEMINI_API_KEY=your_api_key_here
```

### Frontend Environment Variables  
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

## 🐛 Troubleshooting

### "Cannot connect to analysis server"
- ✅ Ensure backend is running on localhost:8000
- ✅ Check CORS settings in `api_server.py`
- ✅ Verify no firewall blocking port 8000

### "Analysis failed"
- ✅ Check backend console for error messages
- ✅ Review debug logs in `backend/debug/`
- ✅ Ensure file types are supported (.md, .py, .yml, etc.)

### "Module not found" errors
- ✅ Activate Python virtual environment
- ✅ Install requirements: `pip install -r requirements.txt`
- ✅ Verify you're in `backend/app/` directory when running server

## 📁 Project Structure

```
Concord/
├── backend/
│   ├── app/
│   │   ├── api_server.py     ← FastAPI server
│   │   ├── process.py        ← Main analysis pipeline
│   │   ├── debug_logger.py   ← Comprehensive logging
│   │   └── ...
│   ├── debug/                ← Debug logs auto-generated here
│   └── requirements.txt      ← Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          ← Updated with real API calls
│   │   └── ...
│   └── package.json         ← React dependencies
├── start-dev.bat            ← Windows startup script
├── start-dev.sh             ← Unix startup script
└── test_integration.py      ← Integration test script
```

## 🚀 Production Deployment

### Option 1: Single VPS
```bash
# Build frontend
cd frontend && npm run build

# Serve with nginx
# Backend runs on :8000
# Frontend static files served from dist/
```

### Option 2: Separate Hosting
```bash
# Backend: Deploy to Railway/Render/Heroku
# Frontend: Deploy to Vercel/Netlify
# Update CORS origins and API URLs
```

### Option 3: Docker
```yaml
# docker-compose.yml ready for container deployment
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    ports: ["80:80"]
```

## ✨ Features

- **🔄 Real-time Analysis**: Upload files and get immediate semantic analysis
- **📊 Three-Tier Display**: Required Truth, Structural Warnings, Heuristic Context
- **📋 Automatic Logging**: Every request logged with complete pipeline details
- **🔍 Debug Access**: View processing logs through web interface
- **🚀 Development Ready**: Hot-reload for both frontend and backend
- **📱 Production Ready**: Easy deployment to any hosting platform
- **🛡️ CORS Enabled**: Secure cross-origin requests
- **⚡ Fast Processing**: Efficient file handling and cleanup

---

🎯 **You're now ready for full frontend-backend integration!** 

Upload files through the beautiful React interface and watch them get processed through your complete semantic analysis pipeline with automatic debug logging.