from enum import Enum
from pydantic import BaseModel
from typing import Optional
from claims.claim_model import Claim, ClaimCategory

# -------------------------FindingKind Enum-------------------------------------
class FindingKind(str, Enum):
    CONTRADICTION = "contradiction"
    MULTIPLE_SUCCESS_VARIANTS = "multiple_success_variants"
    CONFIDENCE_SPREAD = "confidence_spread"
    UNVERIFIED = "unverified"

    MISSING_TESTS = "missing_tests"
    MISSING_SPEC = "missing_spec"
    MISSING_README = "missing_readme"

    IMPLEMENTATION_ONLY = "implementation_only"
    DOCUMENTATION_ONLY = "documentation_only"
# -------------------------FindingKind Enum-------------------------------------

# -------------------------Finding Model (Pure Analysis Facts)-----------------------------
class Finding(BaseModel):
    kind: FindingKind
    description: str
    related_claims: list[Claim] = []
    details: Optional[dict] = None
# -------------------------Finding Model-------------------------------------

# -------------------------AnalysisObject (Pure Structural Facts)---------------------------
class AnalysisObject(BaseModel):
    endpoint: str
    category: ClaimCategory
    condition: Optional[str]
    claims: list[Claim]
    findings: list[Finding]
    
    def key(self) -> tuple[str, ClaimCategory, Optional[str]]:
        """Key for matching with corresponding EvaluationObject."""
        return (self.endpoint, self.category, self.condition)
# -------------------------AnalysisObject-------------------------------------

# -------------------------Evaluation Layer (Heuristics & Scoring)-------------------------
class EvaluationObject(BaseModel):
    endpoint: str
    category: ClaimCategory
    condition: Optional[str]
    claims: list[Claim]
    findings: list[Finding]
    coverage_score: float  # 0.0-1.0 based on artifact source diversity
    confidence_score: float  # Weighted average confidence
    risk_level: str  # critical, high, medium, low
    
    def key(self) -> tuple[str, ClaimCategory, Optional[str]]:
        """Key for matching with corresponding AnalysisObject."""
        return (self.endpoint, self.category, self.condition)
# -------------------------Evaluation Layer-------------------------------------