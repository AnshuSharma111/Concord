from backend.app.claims.claim_model import Claim
from backend.app.analysis.analysis_model import AnalysisObject, Finding, FindingKind
from backend.app.claims.claim_model import ArtifactSource
from collections import defaultdict

# -------------------------Function to group claims by comparison key----------------------------------------
def group_claims(claims: list[Claim]) -> dict[str, list[Claim]]:
    groups = defaultdict(list)
    for c in claims:
        groups[c.comparison_key()].append(c)
    return groups
# -------------------------Function to group claims by comparison key----------------------------------------

# -------------------------Function to create analysis object from bucket------------------------------------
def analyse_bucket(bucket: list[Claim]) -> AnalysisObject:
    findings = []

    sources = {c.source for c in bucket}

    # UNVERIFIED
    if len(bucket) == 1:
        findings.append(Finding(
            kind=FindingKind.UNVERIFIED,
            description="Only one artifact asserts this behavior",
            related_claims=bucket
        ))

    # CONTRADICTION
    assertion_map = defaultdict(list)
    for claim in bucket:
        assertion_map[claim.assertion].append(claim)

    if len(assertion_map) > 1:
        findings.append(Finding(
            kind=FindingKind.CONTRADICTION,
            description="Conflicting assertions detected for this behavior",
            details={
                "conflicting_assertions": [
                    {"assertion": a, "claims": cs}
                    for a, cs in assertion_map.items()
                ]
            }
        ))

    # Missing artifact types
    if ArtifactSource.TEST not in sources:
        findings.append(Finding(
            kind=FindingKind.MISSING_TESTS,
            description="No tests enforce this behavior",
            related_claims=bucket
        ))

    if ArtifactSource.API_SPEC not in sources:
        findings.append(Finding(
            kind=FindingKind.MISSING_SPEC,
            description="Behavior is not specified in the API contract",
            related_claims=bucket
        ))

    if ArtifactSource.README not in sources:
        findings.append(Finding(
            kind=FindingKind.MISSING_README,
            description="Behavior is undocumented in README",
            related_claims=bucket
        ))

    # Derived patterns
    if sources == {ArtifactSource.TEST}:
        findings.append(Finding(
            kind=FindingKind.IMPLEMENTATION_ONLY,
            description="Behavior is enforced but never documented",
            related_claims=bucket
        ))

    if ArtifactSource.TEST not in sources and sources & {ArtifactSource.README, ArtifactSource.API_SPEC}:
        findings.append(Finding(
            kind=FindingKind.DOCUMENTATION_ONLY,
            description="Behavior is documented but not enforced",
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
def analyse_claims(claims: list[Claim]) -> list[AnalysisObject]:
    analysis_results = []
    grouped_claims = group_claims(claims)

    for bucket in grouped_claims.values():
        analysis_result = analyse_bucket(bucket)
        analysis_results.append(analysis_result)
    
    return analysis_results
# -------------------------Function to analyse claims------------------------------------------------------------