# Semantic Contract Consistency Checker

A pre-release sanity check for software behavior that detects inconsistencies between documentation, API specifications, and tests.

## Overview

Modern software systems often ship with subtle but dangerous inconsistencies between what they claim to do (documentation, specs) and what they actually enforce (tests). This tool analyzes your codebase to determine whether your documentation, API specifications, and tests describe the same externally observable behavior.

**The tool does not verify correctness. It verifies agreement.**

## Problem Statement

Teams rely on multiple artifacts to describe system behavior:
- **README files** describe intent
- **API specs** formalize interfaces  
- **Tests** enforce assumptions

Over time, these artifacts drift. When they disagree, teams ship software that behaves differently depending on which artifact a consumer trusts.

## Features

- 🔍 **Detect contradictions** between declared and enforced behavior
- 📋 **Surface undocumented behavior** relied upon by tests
- 📖 **Provide precise evidence** with source-backed findings and line numbers
- 🛡️ **Operate reliably** even with missing or partial artifacts
- 🚦 **Release readiness signal** with clear risk assessment

## Supported Inputs

The tool operates on a single repository snapshot, provided as:
- A public Git repository URL, or
- An uploaded archive

### Behavioral Artifacts

| Artifact | Required | Role |
|----------|----------|------|
| `README.md` | Optional | Informal declaration of intent |
| OpenAPI spec (YAML/JSON) | Optional | Formal interface contract |
| Test files (single framework) | Optional | Enforced behavior |

**Absence is treated as signal, not error.**

## Core Concepts

### Claims
A **claim** is a falsifiable statement about externally observable system behavior that must be:
- Observable by an external client
- Behavioral (not implementation detail)
- Testable or falsifiable

### Claim Categories
The system only reasons about claims in these categories:
- Endpoint Existence
- Input Preconditions
- Output Guarantees
- Error Semantics
- Idempotency / Side Effects

### Consistency Outcomes
For each behavior, the system produces one of three outcomes:

- **Reinforcement**: Multiple sources assert the same behavior
- **Contradiction**: Different sources assert mutually exclusive behavior  
- **Silence**: A behavior is asserted by only one source

## Release Readiness Signal

The tool produces a single high-level assessment:

- 🟥 **High Risk — Review Required**: Contradictions detected
- 🟨 **Moderate Risk — Review Recommended**: No contradictions but multiple silence findings
- 🟩 **Low Risk — No Blocking Issues Detected**: Reinforced behavior with minimal silence

## Getting Started

### Prerequisites

- **Node.js** 18+ with npm (for frontend)
- **Python** 3.8+ with pip (for backend) 
- **Git** for cloning the repository
- **Gemini API Key** (optional, for semantic descriptions)

### Repository Structure

```
Concord/
├── frontend/          # React frontend application
│   ├── src/          # React components and logic
│   ├── public/       # Static assets
│   ├── package.json  # Node dependencies
│   └── vite.config.js # Build configuration
├── backend/           # FastAPI backend service  
│   ├── app/          # Application source code
│   │   ├── analysis/ # Semantic analysis engine
│   │   ├── claims/   # Claims generation logic
│   │   ├── display/  # Result formatting
│   │   ├── ingest/   # Evidence extraction
│   │   └── api_server.py # FastAPI server
│   ├── samples/      # Sample test files
│   └── requirements.txt # Python dependencies
└── render.yaml       # Deployment configuration
```

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AnshuSharma111/Concord.git
cd Concord
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Set up Gemini API key for semantic descriptions
# Create .env file in backend/ directory:
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory  
cd ../frontend

# Install Node.js dependencies
npm install
```

## Local Development

### Start Backend Server

```bash
cd backend
python -m uvicorn app.api_server:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Start Frontend Development Server

```bash
cd frontend  
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## Usage

### Web Interface

1. Open your browser to `http://localhost:5173`
2. Upload your repository files:
   - **README file** (e.g., `README.md`)
   - **API specification** (e.g., `openapi.yml`)  
   - **Test file** (e.g., `test_api.py`)
3. Click **"Analyze Repository"**
4. Review the consistency analysis results

### Sample Files

Test the system with provided sample files in `backend/samples/`:
- `sample_readme_agree.md` - README documentation
- `sample_spec_agree.yml` - OpenAPI specification  
- `sample_test_agree.py` - Test assertions

### API Endpoints

The backend provides these REST endpoints:

- `GET /health` - Health check
- `POST /api/analyze` - Upload files for analysis
- `GET /api/debug/logs` - View debug logs
- `GET /api/debug/logs/{session_id}` - Get specific session logs

## Deployed Application

### Live Demo

- **Frontend**: https://concord-otix.onrender.com/
- **Backend API**: https://concord-backend-zhc5.onrender.com/

### Deployment

The application is deployed on Render using the included `render.yaml` blueprint:

```bash
# Deploy to Render
# 1. Fork this repository  
# 2. Connect to Render
# 3. Create new Blueprint
# 4. Select your repository
# 5. Render will auto-deploy from render.yaml
```

## Configuration

### Environment Variables

**Backend** (optional):
- `GEMINI_API_KEY` - Google Gemini API key for semantic descriptions
- `ENVIRONMENT` - Set to `production` for deployed environments

**Frontend**:
- Production API endpoint is configured in `src/config.js`
- Automatically detects development vs production mode

## Troubleshooting

### Common Issues

**"Cannot connect to analysis server"**
- Ensure backend is running on port 8000
- Check firewall settings
- Verify CORS configuration in `api_server.py`

**"Failed to fetch" in deployed app**
- Check CORS settings allow your frontend domain
- Verify backend URL in `frontend/src/config.js`
- Ensure both services are deployed and healthy

**Dependency installation errors**
- Update pip: `pip install --upgrade pip`
- Use specific Python version: `python3.8` or `python3.9`
- Try: `pip install --no-cache-dir -r requirements.txt`

### Debug Information

The system generates comprehensive debug logs in `backend/debug/`:
- `session_summary_*.log` - High-level session info
- `process_details_*.txt` - Detailed processing data
- `session_data_*.json` - Raw analysis data

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add new feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## Architecture Overview

- **Frontend**: React + Vite for fast development and build
- **Backend**: FastAPI for high-performance async API
- **Analysis Engine**: Multi-stage pipeline with evidence extraction, claims generation, and semantic analysis
- **AI Integration**: Google Gemini for natural language conflict descriptions
- **Deployment**: Render platform with auto-deploy from Git

## Failure Philosophy

The system is conservative by design:
- Ambiguity leads to abstention
- Missing data lowers confidence  
- Silence is surfaced as risk, not error

This prevents hallucinated certainty and builds trust.

## Support

For questions or issues, please [create an issue](../../issues) in this repository.

---

**Remember**: This tool answers one question: *Do our docs, specs, and tests still agree on what this system does?*

It doesn't promise correctness. **It promises clarity.**

And that clarity is often the difference between a clean release and a painful rollback.