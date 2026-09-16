# Illustrative Synthetic Assignment Framework

This logic is fictional and exists only to demonstrate analytical controls. It does not reproduce, approximate, or claim knowledge of any real CareCredit or Synchrony assignment process.

## Allocation waterfall

1. **Validated intake attribution.** Approximately 50% of applications arrive with provisional provider and rep values. The first pass validates those relationships. Records without intake attribution or with failed validation remain unresolved.
2. **Provider-session match.** Unresolved records are evaluated against a fictional provider-session token. This produces high-confidence assignments when a single session match exists.
3. **Geographic + specialty + activity match.** Remaining applications are compared with synthetic provider candidates. Only one-candidate results above the confidence threshold are assigned; ambiguous or weak matches continue.
4. **Manual review or unallocated.** Ambiguous cases enter manual review. Cases without sufficient evidence remain unallocated.

Every pass operates only on applications unresolved by the prior pass. Every attempt is retained in `application_assignment_events`, while `is_current = true` marks exactly one authoritative current state per application. Provider master relationships supply authoritative territory and rep only after assignment is confirmed. Provisional intake attribution is never treated as confirmed merely because it was present at submission.

Confidence bands are HIGH at 0.90 or above, MEDIUM from 0.70 through 0.899, and LOW below 0.70. Low-confidence cases are not silently promoted to confirmed attribution.

The generated story holds assignment near 96% to 98% from January through June, about 93% in July, and about 89% in August. Separately, selected Southeast territories experience declining activation and application productivity. That separation lets later models distinguish measurement deterioration from a genuine commercial issue.

The provider-session step deliberately weakens in July and August. This makes the waterfall diagnostic: leadership can see not only that allocation declined, but which pass stopped resolving the same share of applications.

## Controls

Assignment events must reference a known application. Event identifiers are unique, attempt numbers are sequential, and each application has exactly one current state. Assigned provider identifiers must exist in the same monthly provider snapshot. Confidence must be in `[0, 1]`, status must be accepted, and assignment date cannot precede application date. The controlled bad-data fixture violates the provider relationship for exactly 17 records and must halt the load.
