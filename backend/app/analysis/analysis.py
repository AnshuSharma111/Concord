from app.claims.claim_model import Claim, ArtifactSource
from app.analysis.analysis_model import AnalysisObject, Finding, FindingKind, EvaluationObject
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import re

# -------------------------Function to group claims by comparison key----------------------------------------
def group_claims(claims: list[Claim]) -> dict[str, list[Claim]]:
    groups = defaultdict(list)
    for c in claims:
        groups[c.comparison_key()].append(c)
    return groups
# -------------------------Function to group claims by comparison key----------------------------------------

# -------------------------Pure Analysis Functions (Facts Only)-----------------------------
def detect_multiple_success_variants(bucket: List[Claim]) -> List[Finding]:
    """Detect multiple success code variants - structural observation only."""
    findings = []
    
    success_codes = set()
    for claim in bucket:
        assertion = claim.assertion
        if re.match(r'OUT_HTTP_2\d{2}', assertion):
            success_codes.add(assertion)
    
    if len(success_codes) > 1:
        findings.append(Finding(
            kind=FindingKind.MULTIPLE_SUCCESS_VARIANTS,
            description=f"Multiple success code variants present: {', '.join(sorted(success_codes))}",
            related_claims=[c for c in bucket if c.assertion in success_codes],
            details={"variants": list(success_codes)}
        ))
    
    return findings

def detect_confidence_spread(bucket: List[Claim]) -> List[Finding]:
    """Detect confidence spread across claims - factual observation only."""
    findings = []
    
    if len(bucket) < 2:
        return findings
    
    confidences = [c.confidence for c in bucket]
    min_conf = min(confidences)
    max_conf = max(confidences)
    spread = max_conf - min_conf
    
    findings.append(Finding(
        kind=FindingKind.CONFIDENCE_SPREAD,
        description=f"Confidence range: {min_conf:.2f} to {max_conf:.2f} (spread: {spread:.2f})",
        related_claims=bucket,
        details={"min_confidence": min_conf, "max_confidence": max_conf, "spread": spread}
    ))
    
    return findings

# -------------------------Pure Analysis Function (Truth-Preserving)------------------------
def analyse_bucket(bucket: List[Claim]) -> AnalysisObject:
    """Analyze a bucket of claims for structural facts only - no evaluation or policy."""
    findings = []
    sources = {c.source for c in bucket}

    # Factual analysis - what IS, not what SHOULD BE
    findings.extend(detect_multiple_success_variants(bucket))
    findings.extend(detect_confidence_spread(bucket))

    # Source diversity facts
    if len(bucket) == 1:
        findings.append(Finding(
            kind=FindingKind.UNVERIFIED,
            description="Single artifact source for this behavior",
            related_claims=bucket
        ))

    # Assertion contradiction facts
    assertion_map = defaultdict(list)
    for claim in bucket:
        assertion_map[claim.assertion].append(claim)

    if len(assertion_map) > 1:
        conflicting_assertions = list(assertion_map.keys())
        findings.append(Finding(
            kind=FindingKind.CONTRADICTION,
            description=f"Multiple distinct assertions: {', '.join(conflicting_assertions)}",
            related_claims=bucket,
            details={
                "assertion_groups": [
                    {"assertion": a, "sources": [c.source.value for c in cs]}
                    for a, cs in assertion_map.items()
                ]
            }
        ))

    # Artifact presence facts
    if ArtifactSource.TEST not in sources:
        findings.append(Finding(
            kind=FindingKind.MISSING_TESTS,
            description="No test artifacts assert this behavior",
            related_claims=bucket
        ))

    if ArtifactSource.API_SPEC not in sources:
        findings.append(Finding(
            kind=FindingKind.MISSING_SPEC,
            description="No API specification artifacts assert this behavior",
            related_claims=bucket
        ))

    if ArtifactSource.README not in sources:
        findings.append(Finding(
            kind=FindingKind.MISSING_README,
            description="No README documentation asserts this behavior",
            related_claims=bucket
        ))

    # Source pattern facts
    if sources == {ArtifactSource.TEST}:
        findings.append(Finding(
            kind=FindingKind.IMPLEMENTATION_ONLY,
            description="Behavior asserted only in test artifacts",
            related_claims=bucket
        ))

    if ArtifactSource.TEST not in sources and sources & {ArtifactSource.README, ArtifactSource.API_SPEC}:
        findings.append(Finding(
            kind=FindingKind.DOCUMENTATION_ONLY,
            description="Behavior asserted only in documentation artifacts",
            related_claims=bucket
        ))

    return AnalysisObject(
        endpoint=bucket[0].endpoint,
        category=bucket[0].category,
        condition=bucket[0].condition,
        claims=bucket,
        findings=findings
    )
# -------------------------Function to create analysis object from bucket----------------------------------------

# -------------------------Function to analyse claims------------------------------------------------------------
def analyse_claims(claims: List[Claim]) -> List[AnalysisObject]:
    analysis_results = []
    grouped_claims = group_claims(claims)

    for bucket in grouped_claims.values():
        analysis_result = analyse_bucket(bucket)
        analysis_results.append(analysis_result)
    
    return analysis_results
# -------------------------Function to analyse claims------------------------------------------------------------