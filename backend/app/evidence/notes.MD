## Evidence

1. An Evidence is a one-to-one with something that actually exists in the input artifacts, and it always carries a source mapping.

2. An Evidence is made up of 7 members:

```python
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EvidenceType
    endpoint: str
    observation: str
    source_file: str
    source_location: str
    raw_snippet: Optional[str]
```