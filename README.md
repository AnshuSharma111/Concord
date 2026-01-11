# Design Document  
## Semantic Contract Consistency Checker  
*A pre-release sanity check for software behavior*

---

## 1. Overview

Modern software systems often ship with subtle but dangerous inconsistencies between what they claim to do (documentation, specs) and what they actually enforce (tests). These inconsistencies frequently survive code review and CI, surfacing only after release.

This project is a **semantic consistency checker** designed to be run as a final, quick verification step before shipping. It analyzes documentation, API specifications, and tests to determine whether these artifacts describe the same externally observable behavior.

> **The tool does not verify correctness.  
> It verifies agreement.**

---

## 2. Problem Statement

Teams rely on multiple artifacts to describe system behavior:

- **README files** describe intent  
- **API specs** formalize interfaces  
- **Tests** enforce assumptions  

Over time, these artifacts drift. When they disagree, teams ship software that behaves differently depending on which artifact a consumer trusts.

Existing tools validate syntax, types, or execution—but none check whether these sources still tell the same story.

---

## 3. Design Goals

### Primary Goals

- Detect contradictions between declared and enforced behavior  
- Surface undocumented behavior relied upon by tests  
- Provide precise, source-backed evidence for every finding  
- Operate reliably even with missing or partial artifacts  

### Explicit Non-Goals

- Proving correctness  
- Executing code or tests  
- Deep static or dynamic analysis  
- Security, performance, or compliance validation  

---

## 4. Supported Inputs (MVP Scope)

The tool operates on a single repository snapshot, provided as:

- a public Git repository URL, or  
- an uploaded archive  

### Behavioral Artifacts

| Artifact                    | Required | Role                           |
|----------------------------|----------|--------------------------------|
| `README.md`                | Optional | Informal declaration of intent |
| OpenAPI spec (YAML/JSON)   | Optional | Formal interface contract      |
| Test files (single framework) | Optional | Enforced behavior              |

The system never fails due to missing artifacts.  
**Absence is treated as signal, not error.**

---

## 5. Core Concept: Claims

### Definition

A **claim** is a falsifiable statement about externally observable system behavior.

To qualify, a claim must be:

- Observable by an external client  
- Behavioral (not implementation detail)  
- Testable or falsifiable  

Statements that are vague, non-behavioral, or non-falsifiable are intentionally ignored.

---

## 6. Claim Taxonomy (Closed Set)

The system only reasons about claims belonging to these categories:

- Endpoint Existence  
- Input Preconditions  
- Output Guarantees  
- Error Semantics  
- Idempotency / Side Effects  

This bounded vocabulary prevents hallucination and scope creep.

---

## 7. Claim Extraction Strategy

### Hybrid Approach

- Heuristics define where claims may exist (**anchors**)  
- **Gemini 3** performs semantic extraction within those bounds  

### Anchors

- README sections related to usage or API behavior  
- OpenAPI fields (paths, responses, parameters)  
- Test assertions (expected status codes, error handling)  

### Gemini’s Role

Gemini 3:

- Extracts claims from anchored text  
- Normalizes them into structured form  
- Assigns confidence  
- Provides exact source excerpts with line numbers  

Gemini does **not**:

- invent claims  
- decide contradictions  
- judge correctness  

---

## 8. Claim Structure

Each extracted claim includes:

```json
{
  "category": "error_semantics",
  "endpoint": "GET /users/{id}",
  "condition": "not_found",
  "assertion": "returns HTTP 404",
  "source": {
    "file": "README.md",
    "lines": "26–28",
    "excerpt": "If the user does not exist, the endpoint returns 404."
  },
  "authority": "informal",
  "confidence": "high"
}

## 9. Claim Identity & Matching

Two claims refer to the same behavior if they share the same canonical tuple:

(endpoint, HTTP method, condition, category)


### Canonicalization Rules

- Paths are normalized  
  - `/users/123` → `/users/{id}`

- Conditions are mapped to coarse buckets:
  - `success`
  - `not_found`
  - `unauthenticated`
  - `invalid_input`
  - `conflict`
  - `unknown`

Gemini assists in classification but **abstains when unclear**.

---

## 10. Consistency Outcomes (Trinary Logic)

For each equivalence class of claims, the system produces **exactly one** outcome:

### Reinforcement
Multiple sources assert the same behavior.

### Contradiction
Different sources assert mutually exclusive behavior.

### Silence
A behavior is asserted by only one source.

No probabilistic or fuzzy outcomes are allowed.

---

## 11. Findings vs Claims

**Claims are evidence.  
Findings are insight.**

The system presents **findings**, not raw claims.

Each finding:

- Names the affected behavior
- Shows all supporting or conflicting claims
- Includes exact source excerpts
- Explains why it matters

---

## 12. Release Readiness Signal

The tool produces a single high-level signal:

- 🟥 **High Risk — Review Required**
- 🟨 **Moderate Risk — Review Recommended**
- 🟩 **Low Risk — No Blocking Issues Detected**

### Determination Rules

- Any contradiction → 🟥 **High Risk**
- No contradictions but multiple silence findings → 🟨 **Moderate Risk**
- Reinforced behavior with minimal silence → 🟩 **Low Risk**

No numeric scores or averages are used.

---

## 13. Output Structure

- Release Readiness Signal
- Findings Summary (counts only)
- Findings List
  - Contradictions (expanded)
  - Silence (collapsed)
  - Reinforcements (collapsed)
- Evidence View
  - Source excerpts
  - Line numbers
  - File paths

---

## 14. Why Gemini 3 Is Essential

Gemini 3 is used for:

- Long-context multi-document reasoning
- Semantic extraction from informal text
- Structured claim normalization
- Confidence-aware inference under partial information

The application relies on Gemini as a **reasoning engine**, not a chatbot.

---

## 15. Failure Philosophy

The system is conservative by design:

- Ambiguity leads to abstention
- Missing data lowers confidence
- Silence is surfaced as risk, not error

This prevents hallucinated certainty and builds trust.

---

## 16. Intended Usage

This tool is designed to be run:

- after tests pass
- before release
- when fixes are still cheap

It answers one question:

> **Do our docs, specs, and tests still agree on what this system does?**

---

## 17. Summary

This project delivers a narrowly scoped, defensible, and execution-friendly tool that detects semantic drift between software artifacts using Gemini 3’s reasoning capabilities.

It does **not** promise correctness.  
**It promises clarity.**

And that clarity is often the difference between a clean release and a painful rollback.