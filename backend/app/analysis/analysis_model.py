from enum import Enum
from pydantic import BaseModel
from typing import Optional
from backend.app.claims.claim_model import Claim, ClaimCategory

# -------------------------FindingKind Enum-------------------------------------
class FindingKind(str, Enum):
    CONTRADICTION = "contradiction"
    UNVERIFIED = "unverified"

    MISSING_TESTS = "missing_tests"
    MISSING_SPEC = "missing_spec"
    MISSING_README = "missing_readme"

    IMPLEMENTATION_ONLY = "implementation_only"
    DOCUMENTATION_ONLY = "documentation_only"
# -------------------------FindingKind Enum-------------------------------------

# -------------------------Finding Model-------------------------------------
class Finding(BaseModel):
    kind: FindingKind
    description: str
    related_claims: list[Claim] = []
    details: Optional[dict] = None
# -------------------------Finding Model-------------------------------------

# -------------------------AnalysisResult Model-------------------------------------
class AnalysisObject(BaseModel):
    endpoint: str
    category: ClaimCategory
    condition: Optional[str]
    claims: list[Claim]
    findings: list[Finding]
# -------------------------AnalysisResult Model-------------------------------------