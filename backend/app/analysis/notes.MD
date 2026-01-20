## Analysis

1. An AnalysisResult object holds the result of analysis of one bucket of claims. It does not have any drawn conclusions, only the findings of the analysis search.

2. An AnalysisResult is made up of 5 members:

```python
    endpoint: str
    category: ClaimCategory
    condition: Optional[str]
    claims: list[Claim]
    findings: list[Finding]
```

3. A Finding Object stores the pairwise result of analysis for each pair in the bucket. For example:

> kind : Contradiction
> description : Claim index 0 and Claim index 3 contradict
> related_claims: [Claim0, Claim3]