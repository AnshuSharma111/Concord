import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.claims.claim_model import Claim, ArtifactSource, ClaimCategory
from app.analysis.analysis import analyse_claims
from app.analysis.evaluation import evaluate_bucket
from app.display.display_processor import create_display_context
from app.display.display_formatter import format_complete_display, format_canonical_unit_card

print("Testing Three-Tier Information Display System")
print("=" * 60)

# Create test claims that will trigger different findings
test_claims = [
    # GET /users - Multiple success variants (CONTRADICTION)
    Claim(
        endpoint="GET /api/users",
        category=ClaimCategory.OUTPUT_GUARANTEE,
        condition="valid request",
        assertion="OUT_HTTP_200",
        confidence=0.9,
        source=ArtifactSource.TEST
    ),
    Claim(
        endpoint="GET /api/users",
        category=ClaimCategory.OUTPUT_GUARANTEE,
        condition="valid request",
        assertion="OUT_HTTP_201",  # Conflicts with 200
        confidence=0.7,
        source=ArtifactSource.API_SPEC
    ),
    
    # POST /users - Documentation only (no tests)
    Claim(
        endpoint="POST /api/users",
        category=ClaimCategory.ERROR_SEMANTICS,
        condition="invalid data",
        assertion="ERR_HTTP_400",
        confidence=0.8,
        source=ArtifactSource.README
    ),
    Claim(
        endpoint="POST /api/users",
        category=ClaimCategory.ERROR_SEMANTICS,
        condition="invalid data",
        assertion="ERR_HTTP_400",
        confidence=0.6,
        source=ArtifactSource.API_SPEC
    ),
    
    # DELETE /users/{id} - Implementation only (tests but no docs)
    Claim(
        endpoint="DELETE /api/users/{id}",
        category=ClaimCategory.OUTPUT_GUARANTEE,
        condition="user exists",
        assertion="OUT_HTTP_204",
        confidence=0.95,
        source=ArtifactSource.TEST
    ),
    
    # GET /health - Perfect agreement across all sources
    Claim(
        endpoint="GET /health",
        category=ClaimCategory.OUTPUT_GUARANTEE,
        condition=None,
        assertion="OUT_HTTP_200",
        confidence=0.98,
        source=ArtifactSource.TEST
    ),
    Claim(
        endpoint="GET /health",
        category=ClaimCategory.OUTPUT_GUARANTEE,
        condition=None,
        assertion="OUT_HTTP_200",
        confidence=0.85,
        source=ArtifactSource.API_SPEC
    ),
    Claim(
        endpoint="GET /health",
        category=ClaimCategory.OUTPUT_GUARANTEE,
        condition=None,
        assertion="OUT_HTTP_200",
        confidence=0.90,
        source=ArtifactSource.README
    )
]

print(f"Created {len(test_claims)} test claims across 4 endpoints")

# Step 1: Analyze claims (pure facts)
print("\nStep 1: Analysis Layer (Pure Facts)")
print("-" * 40)
analysis_results = analyse_claims(test_claims)
print(f"Generated {len(analysis_results)} behavioral analysis units")

# Step 2: Evaluate claims (heuristics)  
print("\nStep 2: Evaluation Layer (Heuristics & Scoring)")
print("-" * 50)
evaluations = []
for analysis in analysis_results:
    evaluation = evaluate_bucket(analysis.claims, analysis.findings)
    evaluations.append(evaluation)
    print(f"  {evaluation.endpoint}: Risk={evaluation.risk_level}, Coverage={evaluation.coverage_score:.2f}")

# Step 3: Transform to display context
print("\nStep 3: Display Transformation")
print("-" * 35)
display_context = create_display_context(analysis_results, evaluations)
print(f"Created display context with {len(display_context.behavioral_units)} unit cards")

# Step 4: Show canonical unit card examples
print("\n" + "=" * 80)
print("CANONICAL UNIT CARDS (Individual Behaviors)")
print("=" * 80)

for i, unit_card in enumerate(display_context.behavioral_units):
    print(f"\n[Card {i+1}] " + "-" * 50)
    print(format_canonical_unit_card(unit_card, show_context=True))

# Step 5: Show complete three-tier display
print("\n" + "=" * 80) 
print("COMPLETE THREE-TIER DISPLAY SYSTEM")
print("=" * 80)
complete_display = format_complete_display(display_context, show_context=False)
print(complete_display)

print("\n" + "=" * 80)
print("✅ THREE-TIER INFORMATION ARCHITECTURE COMPLETE")
print("=" * 80)
print()
print("Ready for UI integration:")
print("• Tier 1: Required Truth (endpoint, assertions, sources)")
print("• Tier 2: Structural Warnings (labels, not essays)")
print("• Tier 3: Heuristic Context (scores, risk bands)")
print()
print("All text is formatted and ready for frontend consumption!")