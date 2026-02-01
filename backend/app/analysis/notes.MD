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

4. A finding exists iff it can be derived purely from the set of claims (and their sources), without interpretation.

5. The FindingKind Enums signify the following:

- UNVERIFIED
  Only one artifact asserts this behavior. There is no independent corroboration.
- CONTRADICTION
  Multiple artifacts assert incompatible behavior for the same semantic unit.
- MISSING_TESTS
  Test files for asserted behavior are missing
- MISSING_SPEC
  Spec files for asserted behavior are missing
- MISSING_README
  Behavior exists but is not documented
- IMPLEMENTATION_ONLY
  Only tests assert this behavior
- DOCUMENTATION_ONLY
  Behavior is promised but not enforced