## Claims

1. A Claim is an artifact-scoped assertion of intent or contract, derived from evidence, expressed in a canonical semantic form. 

2. Concord never mutates or revises claims; all reasoning is performed by comparing immutable claims.

3. A Claim is made up of 7 members:

```python
    category: ClaimCategory
    endpoint: str
    condition: Optional[str] = None
    assertion: str
    source: ArtifactSource
    confidence: float = Field(ge=0.0, le=1.0)
```

4. Each claim has a comparison key, which is a 3-tuple (endpoint, category, condition). This is what allows the claim analysis engine to determine whether 2 claims are about the same canonical artifact.

5. In the future, make sure assertion string is bounded by a template