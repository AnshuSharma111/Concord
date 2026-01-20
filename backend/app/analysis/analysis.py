from backend.app.claims.claim_model import Claim
from backend.app.analysis.analysis_model import AnalysisObject, Finding, FindingKind
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

    if len(bucket) == 1:
        findings.append(Finding(
            kind=FindingKind.UNVERIFIED,
            description="Only one claim exists for this behavior",
            details={"assertion": bucket[0].assertion, "claims": [bucket[0]]}
        ))

    assertion_map = defaultdict(list)
    for claim in bucket:
        assertion_map[claim.assertion].append(claim)

    if len(assertion_map) > 1:
        findings.append(Finding(
            kind=FindingKind.CONTRADICTION,
            description="Conflicting assertions detected for this behavior",
            details={
                "conflicting_assertions": [
                    {
                        "assertion": assertion,
                        "claims": claims
                    }
                    for assertion, claims in assertion_map.items()
                ]
            }
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