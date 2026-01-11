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

- Node.js (for frontend)
- Python 3.8+ (for backend)
- Access to Gemini 3 API

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Concord
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
```bash
cd ../backend
pip install -r requirements.txt
```

### Usage

1. Start the backend server:
```bash
cd backend
python app/main.py
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Open your browser and navigate to the local development URL

4. Upload your repository archive or provide a Git repository URL

5. Review the consistency findings and release readiness assessment

## Output Structure

The tool provides:
- **Release Readiness Signal** with risk level
- **Findings Summary** with counts of contradictions, silence, and reinforcements
- **Detailed Findings** with source excerpts, line numbers, and file paths
- **Evidence View** showing exact claims and their sources

## Architecture

- **Frontend**: React-based web interface for uploading repositories and viewing results
- **Backend**: Python service that orchestrates analysis and integrates with Gemini 3
- **Analysis Engine**: Hybrid approach combining heuristics and AI-powered semantic extraction

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