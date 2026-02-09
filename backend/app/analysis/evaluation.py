from claims.claim_model import Claim, ArtifactSource
from analysis.analysis_model import Finding, EvaluationObject, FindingKind
from typing import List, Set
import re

# -------------------------Evaluation Layer (Heuristics & Scoring)-------------------------

def calculate_coverage_score(sources: Set[ArtifactSource]) -> float:
    """Calculate coverage score based on artifact source diversity - heuristic evaluation."""
    total_sources = 3  # README, API_SPEC, TEST
    return len(sources) / total_sources

def calculate_confidence_score(bucket: List[Claim]) -> float:
    """Calculate weighted average confidence score - heuristic evaluation."""
    if not bucket:
        return 0.0
    
    # Weight by source reliability: TEST > API_SPEC > README
    weights = {
        ArtifactSource.TEST: 1.0,
        ArtifactSource.API_SPEC: 0.9,
        ArtifactSource.README: 0.7
    }
    
    total_weight = 0
    weighted_confidence = 0
    
    for claim in bucket:
        weight = weights.get(claim.source, 0.5)
        weighted_confidence += claim.confidence * weight
        total_weight += weight
    
    return weighted_confidence / total_weight if total_weight > 0 else 0.0

def determine_risk_level(findings: List[Finding], confidence_score: float, coverage_score: float) -> str:
    """Determine overall risk level based on findings and scores - heuristic evaluation."""
    # Count findings by semantic significance (not using deprecated severity field)
    contradiction_findings = [f for f in findings if f.kind == FindingKind.CONTRADICTION]
    multiple_variants_findings = [f for f in findings if f.kind == FindingKind.MULTIPLE_SUCCESS_VARIANTS]
    documentation_only_findings = [f for f in findings if f.kind == FindingKind.DOCUMENTATION_ONLY]
    
    # Heuristic risk assessment
    if contradiction_findings or confidence_score < 0.3:
        return "critical"
    elif multiple_variants_findings or documentation_only_findings or confidence_score < 0.5 or coverage_score < 0.5:
        return "high"
    elif confidence_score < 0.7 or coverage_score < 0.7:
        return "medium"
    else:
        return "low"

def evaluate_bucket(bucket: List[Claim], findings: List[Finding]) -> EvaluationObject:
    """Apply heuristic evaluation to analyzed claims bucket."""
    sources = {c.source for c in bucket}
    
    coverage_score = calculate_coverage_score(sources)
    confidence_score = calculate_confidence_score(bucket)
    risk_level = determine_risk_level(findings, confidence_score, coverage_score)
    
    return EvaluationObject(
        endpoint=bucket[0].endpoint,
        category=bucket[0].category,
        condition=bucket[0].condition,
        claims=bucket,
        findings=findings,
        coverage_score=coverage_score,
        confidence_score=confidence_score,
        risk_level=risk_level
    )

# -------------------------Policy Layer (UI/User Decisions)-------------------------

def generate_policy_recommendations(evaluation: EvaluationObject) -> List[str]:
    """Generate policy recommendations based on evaluation - belongs in UI layer."""
    recommendations = []
    
    for finding in evaluation.findings:
        if finding.kind == FindingKind.CONTRADICTION:
            recommendations.extend([
                "Resolve assertion conflicts between artifacts",
                "Ensure consistent API behavior specification"
            ])
        elif finding.kind == FindingKind.MISSING_TESTS:
            recommendations.extend([
                "Add automated tests to verify this behavior",
                "Ensure test coverage for this endpoint"
            ])
        elif finding.kind == FindingKind.MISSING_SPEC:
            recommendations.extend([
                "Add specification in OpenAPI/Swagger documentation",
                "Define expected responses in API contract"
            ])
        elif finding.kind == FindingKind.MISSING_README:
            recommendations.extend([
                "Document this behavior in user-facing documentation",
                "Add usage examples to README"
            ])
        elif finding.kind == FindingKind.IMPLEMENTATION_ONLY:
            recommendations.extend([
                "Document this behavior in API specification",
                "Add user documentation explaining this behavior"
            ])
        elif finding.kind == FindingKind.DOCUMENTATION_ONLY:
            recommendations.extend([
                "Add tests to verify documented behavior",
                "Ensure implementation matches documentation"
            ])
    
    # De-duplicate recommendations
    return list(set(recommendations))

def determine_severity_level(finding: Finding, evaluation: EvaluationObject) -> str:
    """Determine severity level for a finding based on evaluation - policy layer."""
    if finding.kind == FindingKind.CONTRADICTION:
        return "critical"
    elif finding.kind in [FindingKind.MISSING_TESTS, FindingKind.MISSING_SPEC, FindingKind.DOCUMENTATION_ONLY]:
        return "high"
    elif finding.kind in [FindingKind.UNVERIFIED, FindingKind.IMPLEMENTATION_ONLY]:
        return "medium"
    else:
        return "low"