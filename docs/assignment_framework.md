# Illustrative Synthetic Assignment Framework

This logic is fictional and exists only to demonstrate analytical controls. It does not reproduce, approximate, or claim knowledge of any real CareCredit or Synchrony assignment process.

## Flow

1. Approximately 50% of digital applications arrive with provisional provider and rep attribution; the remaining 50% enter an unallocated pool with customer geography and application facts.
2. A fictional rules process evaluates intake attribution and other evidence such as an exact synthetic match, provider session, or geographic and temporal candidate.
3. Sufficient evidence creates an `assigned` event with a provider, method, confidence, and actor.
4. Ambiguous evidence enters `manual_review` without confirmed provider attribution.
5. Insufficient evidence remains `unallocated`.
6. Provider master relationships supply authoritative territory and rep only after provider assignment is confirmed. Provisional intake attribution is never treated as confirmed merely because it was present at submission.

Confidence bands are HIGH at 0.90 or above, MEDIUM from 0.70 through 0.899, and LOW below 0.70. Low-confidence cases are not silently promoted to confirmed attribution.

The generated story holds assignment near 96% to 98% from January through June, about 93% in July, and about 89% in August. Separately, selected Southeast territories experience declining activation and application productivity. That separation lets later models distinguish measurement deterioration from a genuine commercial issue.

## Controls

Assignment events must reference a known application. Assigned provider identifiers must exist in the same monthly provider snapshot. Confidence must be in `[0, 1]`, status must be accepted, and assignment date cannot precede application date. The controlled bad-data fixture violates the provider relationship for exactly 17 records and must halt the load.
