## Claims

1. Claims are immutable observations extracted from a static repository snapshot. Concord never mutates or revises claims; all reasoning is performed by comparing immutable claims.

2. A Claim is made up of 7 members:

```python
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: ClaimCategory
    endpoint: str
    condition: Optional[str] = None
    assertion: str
    source: ArtifactSource
    confidence: float = Field(ge=0.0, le=1.0)
```