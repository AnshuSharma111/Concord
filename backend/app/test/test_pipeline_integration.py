"""
Integration test showing complete pipeline: Evidence -> Claims -> Analysis -> Display
This demonstrates how the three-tier information architecture plugs into the existing system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from claims.claim_model import Claim, ArtifactSource, ClaimCategory
from analysis.analysis import analyse_claims
from analysis.evaluation import evaluate_bucket
from display.display_processor import create_display_context
from display.display_formatter import (
    format_canonical_unit_card, format_endpoint_summary,
    format_risk_driven_view, format_coverage_view, format_display_summary
)

def simulate_pipeline_with_display():
    """Simulate complete pipeline with three-tier display output."""
    
    print("🔄 COMPLETE PIPELINE: Evidence → Claims → Analysis → Display")
    print("=" * 70)
    
    # Simulate extracted claims from evidence (normally from extract.py + evidence_to_claim.py)
    print("Step 1: Simulating Evidence Extraction & Claim Generation")
    print("(In real pipeline: extract.py → evidence_to_claim.py)")
    
    claims = [
        # Critical contradiction case
        Claim(
            endpoint="POST /api/orders",
            category=ClaimCategory.OUTPUT_GUARANTEE, 
            condition="valid order data",
            assertion="OUT_HTTP_200",  # Success response
            confidence=0.8,
            source=ArtifactSource.README
        ),
        Claim(
            endpoint="POST /api/orders",
            category=ClaimCategory.OUTPUT_GUARANTEE,
            condition="valid order data", 
            assertion="OUT_HTTP_201",  # Different success response - CONFLICT!
            confidence=0.95,
            source=ArtifactSource.TEST
        ),
        Claim(
            endpoint="POST /api/orders",
            category=ClaimCategory.OUTPUT_GUARANTEE,
            condition="valid order data",
            assertion="OUT_HTTP_201",  # Agrees with test
            confidence=0.9,
            source=ArtifactSource.API_SPEC
        ),
        
        # Documentation-only case
        Claim(
            endpoint="GET /api/orders/{id}",
            category=ClaimCategory.ERROR_SEMANTICS,
            condition="order not found",
            assertion="ERR_HTTP_404", 
            confidence=0.7,
            source=ArtifactSource.README
        ),
        
        # Perfect agreement case
        Claim(
            endpoint="GET /api/health",
            category=ClaimCategory.OUTPUT_GUARANTEE,
            condition=None,
            assertion="OUT_HTTP_200",
            confidence=0.98,
            source=ArtifactSource.TEST
        ),
        Claim(
            endpoint="GET /api/health",  
            category=ClaimCategory.OUTPUT_GUARANTEE,
            condition=None,
            assertion="OUT_HTTP_200",
            confidence=0.85,
            source=ArtifactSource.API_SPEC
        )
    ]
    
    print(f"✓ Generated {len(claims)} claims from evidence")
    
    # Step 2: Analysis (pure facts)
    print("\nStep 2: Analysis Layer - Structural Facts Only")
    print("(analysis.py - epistemic discipline maintained)")
    
    analyses = analyse_claims(claims)
    print(f"✓ Analyzed {len(analyses)} behavioral units")
    for analysis in analyses:
        finding_count = len(analysis.findings)
        print(f"  - {analysis.endpoint}: {finding_count} structural findings")
    
    # Step 3: Evaluation (heuristics & scoring)
    print("\nStep 3: Evaluation Layer - Heuristic Scoring") 
    print("(evaluation.py - risk assessment & confidence scoring)")
    
    evaluations = []
    for analysis in analyses:
        evaluation = evaluate_bucket(analysis.claims, analysis.findings)
        evaluations.append(evaluation)
        print(f"  - {evaluation.endpoint}: {evaluation.risk_level} risk, {evaluation.coverage_score:.1f} coverage")
    
    # Step 4: Display transformation 
    print("\nStep 4: Display Context Creation")
    print("(display_processor.py - three-tier information architecture)")
    
    display_context = create_display_context(analyses, evaluations)
    print(f"✓ Created display context with {display_context.total_behaviors()} behavioral units")
    
    # Step 5: Show formatted output for different UI components
    print("\n" + "=" * 70)
    print("🎯 THREE-TIER DISPLAY OUTPUT (Ready for UI)")
    print("=" * 70)
    
    # Individual behavior cards (main detail view)
    print("\n📋 INDIVIDUAL BEHAVIOR CARDS")
    print("-" * 35)
    for i, unit_card in enumerate(display_context.behavioral_units, 1):
        print(f"\n[Behavior {i}]")
        print(format_canonical_unit_card(unit_card, show_context=False))
    
    # Endpoint summaries (navigation/overview)  
    print("\n📡 ENDPOINT SUMMARIES")
    print("-" * 25)
    for summary in display_context.endpoint_summaries:
        print(format_endpoint_summary(summary))
        print()
    
    # Risk-driven view (priority triage)
    print("🚨 RISK-DRIVEN PRIORITY VIEW")
    print("-" * 30)
    print(format_risk_driven_view(display_context.risk_driven_view))
    
    # Coverage gaps (quality assurance)
    print("\n📊 COVERAGE GAP ANALYSIS") 
    print("-" * 25)
    print(format_coverage_view(display_context.coverage_view))
    
    # High-level summary (dashboard)
    print("\n📈 SYSTEM SUMMARY")
    print("-" * 18)
    print(format_display_summary(display_context))
    
    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE - All data formatted for UI consumption")
    print("=" * 70)
    
    return display_context

if __name__ == "__main__":
    display_context = simulate_pipeline_with_display()
    
    print("\n🎨 UI INTEGRATION NOTES:")
    print("-" * 25)
    print("• Tier 1 (Required Truth): Show always, never hide")  
    print("• Tier 2 (Structural Warnings): Show when present, labels not essays")
    print("• Tier 3 (Heuristic Context): Collapsible, helps with prioritization")
    print("• Aggregation Views: Built from same unit cards, different groupings")
    print("• Gemini Integration: Explains selected cards, doesn't replace display")
    print("\nAll text is pre-formatted and ready for frontend rendering! 🚀")