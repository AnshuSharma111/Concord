from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import uuid4
from enum import Enum

'''
Conditions for valid claims:

1) endpoint must be present
If Gemini cannot identify one, the claim is discarded.

2) assertion must describe observable behavior
No implementation details allowed.

3) confidence reflects clarity of extraction, not truth.

4) Claims are additive, not authoritative
Multiple claims about the same endpoint are allowed.
'''

#-------------------------ArtifactSource Enum-------------------------------------
class ArtifactSource(str, Enum):
    README = "readme"
    API_SPEC = "api_spec"
    TEST = "test"
    CODE = "code"
#-------------------------ArtifactSource Enum-------------------------------------

#-------------------------ClaimCategory Enum-------------------------------------
class ClaimCategory(str, Enum):
    ENDPOINT_EXISTS = "endpoint_exists"
    INPUT_PRECONDITION = "input_precondition"
    OUTPUT_GUARANTEE = "output_guarantee"
    ERROR_SEMANTICS = "error_semantics"
    IDEMPOTENCY = "idempotency"
#-------------------------ClaimCategory Enum-------------------------------------

#-------------------------Claim Model-------------------------------------
class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Class members
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: ClaimCategory
    endpoint: str
    """
    Canonical endpoint identifier, e.g.:
    'GET /users/{id}'
    """
    condition: Optional[str] = None
    """
    Preconditions or context, e.g.:
    'user exists'
    'authenticated'
    """
    assertion: str
    """
    Falsifiable behavioral statement, e.g.:
    'returns HTTP 404'
    """
    source: ArtifactSource
    confidence: float = Field(ge=0.0, le=1.0)

    # To check equivalence of claims
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Claim):
            return NotImplemented

        return (
            self.category == other.category
            and self.endpoint == other.endpoint
            and self.condition == other.condition
            and self.assertion == other.assertion
            and self.source == other.source
        )

    # Hash function to allow usage in sets and as dict keys
    def __hash__(self) -> int:
        return hash((
            self.category,
            self.endpoint,
            self.condition,
            self.assertion,
            self.source
        ))
#-------------------------Claim Model-------------------------------------