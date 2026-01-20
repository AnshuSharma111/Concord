## Evidence

1. An Evidence is a one-to-one with something that actually exists in the input artifacts, and it always carries a source mapping.

2. An Evidence is made up of 7 members:

```python
    type: EvidenceType
    endpoint: str
    observation: str
    source_file: str
    source_location: str
    raw_snippet: Optional[str]
```
3. An Evidence is atomic. It carries a singular observation within it. Example:

> type: readme_statement
> endpoint: /api/user/home
> observation: returns 404 if no user
> source_file: README.md
> source_location: README.md:44
> raw_snippet: "..."