from typing import List, Dict, Set
from collections import defaultdict
from app.claims.claim_model import Claim, ArtifactSource, ClaimCategory
from app.analysis.analysis_model import AnalysisObject, Finding, FindingKind
from app.analysis.evaluation import EvaluationObject
from .display_model import (
    BehaviorUnitCard, AssertionInfo, AssertionState, SourceCoverage,
    EndpointSummary, RiskDrivenView, CoverageView, DisplayContext,
    RiskBand, DisplayTier
)
from app.gemini.inference import generate_semantic_description

# -------------------------Core Transformation Functions-------------------------------------

def create_assertion_state(claims: List[Claim]) -> AssertionState:
    """Transform claims into canonical assertion state."""
    assertion_groups = defaultdict(set)
    
    # Group sources by assertion
    for claim in claims:
        assertion_groups[claim.assertion].add(claim.source)
    
    # Create assertion info objects
    assertions = []
    has_conflicts = len(assertion_groups) > 1
    
    for assertion, sources in assertion_groups.items():
        assertions.append(AssertionInfo(
            assertion=assertion,
            sources=sources,
            is_conflicted=has_conflicts
        ))
    
    return AssertionState(
        assertions=assertions,
        has_conflicts=has_conflicts
    )

def create_source_coverage(claims: List[Claim]) -> SourceCoverage:
    """Extract source coverage from claims."""
    sources = {claim.source for claim in claims}
    
    return SourceCoverage(
        test=ArtifactSource.TEST in sources,
        api_spec=ArtifactSource.API_SPEC in sources,
        readme=ArtifactSource.README in sources
    )

def extract_structural_warnings(findings: List[Finding]) -> List[FindingKind]:
    """Extract only Tier 2 structural warning findings."""
    structural_kinds = {
        FindingKind.CONTRADICTION,
        FindingKind.DOCUMENTATION_ONLY,
        FindingKind.IMPLEMENTATION_ONLY,
        FindingKind.UNVERIFIED,
        FindingKind.MULTIPLE_SUCCESS_VARIANTS
    }
    
    return [f.kind for f in findings if f.kind in structural_kinds]

def map_risk_to_band(risk_level: str) -> RiskBand:
    """Map risk level string to RiskBand enum."""
    mapping = {
        "critical": RiskBand.CRITICAL,
        "high": RiskBand.HIGH,
        "medium": RiskBand.MEDIUM,
        "low": RiskBand.LOW
    }
    return mapping.get(risk_level, RiskBand.LOW)

def create_behavior_unit_card(analysis: AnalysisObject, evaluation: EvaluationObject) -> BehaviorUnitCard:
    """Transform analysis + evaluation into canonical unit card."""
    
    assertion_state = create_assertion_state(analysis.claims)
    source_coverage = create_source_coverage(analysis.claims)
    structural_warnings = extract_structural_warnings(analysis.findings)
    
    # Generate semantic description for conflicts
    semantic_description = None
    if assertion_state.has_conflicts and analysis.claims:
        try:
            # Convert behavioral unit data to dictionary for Gemini
            behavioral_unit_data = {
                "endpoint": analysis.endpoint,
                "condition": analysis.condition,
                "assertions": [
                    {
                        "assertion": assertion.assertion,
                        "sources": [str(src.value) for src in assertion.sources],
                        "is_conflicted": assertion.is_conflicted
                    }
                    for assertion in assertion_state.assertions
                ],
                "has_conflicts": assertion_state.has_conflicts,
                "source_coverage": {
                    "test": source_coverage.test,
                    "api_spec": source_coverage.api_spec, 
                    "readme": source_coverage.readme
                },
                "structural_warnings": [str(warning) for warning in structural_warnings],
                "risk_level": evaluation.risk_level,
                "confidence_score": evaluation.confidence_score
            }
            
            semantic_description = generate_semantic_description(behavioral_unit_data)
        except Exception as e:
            print(f"Failed to generate semantic description: {e}")
            semantic_description = None
    
    return BehaviorUnitCard(
        # Tier 1: Required Truth
        endpoint=analysis.endpoint,
        condition=analysis.condition,
        category=analysis.category,
        assertion_state=assertion_state,
        source_coverage=source_coverage,
        
        # Tier 2: Structural Warnings
        structural_warnings=structural_warnings,
        
        # Tier 3: Heuristic Context
        coverage_score=evaluation.coverage_score,
        confidence_score=evaluation.confidence_score,
        risk_band=map_risk_to_band(evaluation.risk_level),
        
        # Semantic Description
        semantic_description=semantic_description,
        
        # Internal data
        claims=analysis.claims,
        findings=analysis.findings
    )

# -------------------------Aggregation Functions-------------------------------------

def create_endpoint_summary(endpoint: str, units: List[BehaviorUnitCard]) -> EndpointSummary:
    """Create endpoint summary from its behavioral units."""
    
    contradiction_count = sum(1 for unit in units 
                            if FindingKind.CONTRADICTION in unit.structural_warnings)
    
    undocumented_count = sum(1 for unit in units 
                           if FindingKind.DOCUMENTATION_ONLY in unit.structural_warnings)
    
    # Find highest risk band
    risk_bands = [unit.risk_band for unit in units if unit.risk_band]
    risk_priority = {RiskBand.CRITICAL: 4, RiskBand.HIGH: 3, RiskBand.MEDIUM: 2, RiskBand.LOW: 1}
    highest_risk_band = max(risk_bands, key=lambda r: risk_priority.get(r, 0)) if risk_bands else None
    
    return EndpointSummary(
        endpoint=endpoint,
        behavior_count=len(units),
        contradiction_count=contradiction_count,
        undocumented_count=undocumented_count,
        highest_risk_band=highest_risk_band,
        behavioral_units=units
    )

def create_risk_driven_view(units: List[BehaviorUnitCard]) -> RiskDrivenView:
    """Group units by risk band for risk-driven view."""
    
    risk_groups = {
        RiskBand.CRITICAL: [],
        RiskBand.HIGH: [],
        RiskBand.MEDIUM: [],
        RiskBand.LOW: []
    }
    
    for unit in units:
        if unit.risk_band:
            risk_groups[unit.risk_band].append(unit)
    
    # Sort within each band by number of contradictions (highest first)
    for risk_band in risk_groups:
        risk_groups[risk_band].sort(
            key=lambda u: len([w for w in u.structural_warnings if w == FindingKind.CONTRADICTION]),
            reverse=True
        )
    
    return RiskDrivenView(
        critical_behaviors=risk_groups[RiskBand.CRITICAL],
        high_risk_behaviors=risk_groups[RiskBand.HIGH],
        medium_risk_behaviors=risk_groups[RiskBand.MEDIUM],
        low_risk_behaviors=risk_groups[RiskBand.LOW]
    )

def create_coverage_view(units: List[BehaviorUnitCard]) -> CoverageView:
    """Group units by coverage gaps."""
    
    no_tests = [u for u in units if not u.source_coverage.test]
    no_spec = [u for u in units if not u.source_coverage.api_spec] 
    no_readme = [u for u in units if not u.source_coverage.readme]
    full_coverage = [u for u in units if u.source_coverage.count() == 3]
    
    return CoverageView(
        no_tests=no_tests,
        no_spec=no_spec,
        no_readme=no_readme,
        full_coverage=full_coverage
    )

def create_display_context(analyses: List[AnalysisObject], evaluations: List[EvaluationObject]) -> DisplayContext:
    """Transform raw analysis results into complete display context."""
    
    # Create evaluation lookup map to handle partial failures gracefully
    eval_map = {e.key(): e for e in evaluations}
    
    # Create behavioral unit cards
    behavioral_units = []
    for analysis in analyses:
        evaluation = eval_map.get(analysis.key())
        if evaluation is not None:
            unit_card = create_behavior_unit_card(analysis, evaluation)
            behavioral_units.append(unit_card)
        # Silently skip analyses without matching evaluations (partial failure handling)
    
    # Group units by endpoint for summaries
    endpoint_groups = defaultdict(list)
    for unit in behavioral_units:
        endpoint_groups[unit.endpoint].append(unit)
    
    # Create aggregated views
    endpoint_summaries = [
        create_endpoint_summary(endpoint, units) 
        for endpoint, units in endpoint_groups.items()
    ]
    
    risk_driven_view = create_risk_driven_view(behavioral_units)
    coverage_view = create_coverage_view(behavioral_units)
    
    return DisplayContext(
        behavioral_units=behavioral_units,
        endpoint_summaries=endpoint_summaries,
        risk_driven_view=risk_driven_view,
        coverage_view=coverage_view
    )