from pydantic import BaseModel
from typing import List, Dict, Optional, Set
from enum import Enum
from app.claims.claim_model import Claim, ArtifactSource, ClaimCategory
from app.analysis.analysis_model import Finding, FindingKind

# -------------------------Display Tier Enums-------------------------------------
class DisplayTier(str, Enum):
    REQUIRED_TRUTH = "required_truth"      # Tier 1: Must see
    STRUCTURAL_WARNINGS = "structural_warnings"  # Tier 2: Should see  
    HEURISTIC_CONTEXT = "heuristic_context"      # Tier 3: Nice but optional

class RiskBand(str, Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

# -------------------------Assertion State Models-------------------------------------
class AssertionInfo(BaseModel):
    """Single assertion with its sources and agreement status."""
    assertion: str
    sources: Set[ArtifactSource]
    is_conflicted: bool  # True if this assertion conflicts with others in same bucket

class AssertionState(BaseModel):
    """Complete assertion state for a behavioral unit."""
    assertions: List[AssertionInfo]
    has_conflicts: bool
    
    def get_canonical_assertion(self) -> Optional[str]:
        """Get the most authoritative assertion if no conflicts."""
        if self.has_conflicts:
            return None
        return self.assertions[0].assertion if self.assertions else None

# -------------------------Source Coverage Model-------------------------------------
class SourceCoverage(BaseModel):
    """Which artifact sources assert this behavior."""
    test: bool = False
    api_spec: bool = False 
    readme: bool = False
    
    def count(self) -> int:
        return sum([self.test, self.api_spec, self.readme])
    
    def missing_sources(self) -> List[str]:
        missing = []
        if not self.test: missing.append("TEST")
        if not self.api_spec: missing.append("API_SPEC") 
        if not self.readme: missing.append("README")
        return missing

# -------------------------Behavioral Unit Card (Tier 1 + 2)-------------------------------------
class BehaviorUnitCard(BaseModel):
    """Canonical unit card - the atomic unit of display."""
    
    # Tier 1: Required Truth (Must See)
    endpoint: str
    condition: Optional[str] 
    category: ClaimCategory
    assertion_state: AssertionState
    source_coverage: SourceCoverage
    
    # Tier 2: Structural Warnings (Should See - only when present)  
    structural_warnings: List[FindingKind] = []
    
    # Tier 3: Heuristic Context (Nice but Optional)
    coverage_score: Optional[float] = None
    confidence_score: Optional[float] = None  
    risk_band: Optional[RiskBand] = None
    
    # Semantic Description (Human-readable explanation of conflicts)
    semantic_description: Optional[str] = None
    
    # Internal data for drill-down
    claims: List[Claim] = []
    findings: List[Finding] = []

# -------------------------Aggregation Models-------------------------------------
class EndpointSummary(BaseModel):
    """Summary view for a single endpoint."""
    endpoint: str
    behavior_count: int
    contradiction_count: int
    undocumented_count: int
    highest_risk_band: Optional[RiskBand]
    behavioral_units: List[BehaviorUnitCard]

class RiskDrivenView(BaseModel):
    """Risk-prioritized view across all behaviors."""
    critical_behaviors: List[BehaviorUnitCard] = []
    high_risk_behaviors: List[BehaviorUnitCard] = []
    medium_risk_behaviors: List[BehaviorUnitCard] = []
    low_risk_behaviors: List[BehaviorUnitCard] = []

class CoverageView(BaseModel):
    """Coverage gap analysis view."""
    no_tests: List[BehaviorUnitCard] = []
    no_spec: List[BehaviorUnitCard] = []  
    no_readme: List[BehaviorUnitCard] = []
    full_coverage: List[BehaviorUnitCard] = []

# -------------------------Display Context-------------------------------------
class DisplayContext(BaseModel):
    """Complete display data ready for UI consumption."""
    behavioral_units: List[BehaviorUnitCard]
    endpoint_summaries: List[EndpointSummary]
    risk_driven_view: RiskDrivenView
    coverage_view: CoverageView
    
    def total_behaviors(self) -> int:
        return len(self.behavioral_units)
    
    def total_contradictions(self) -> int:
        return sum(1 for unit in self.behavioral_units 
                  if FindingKind.CONTRADICTION in unit.structural_warnings)