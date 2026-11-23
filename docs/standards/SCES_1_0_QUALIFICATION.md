# SCES-1.0 qualification record

SCES-1.0 was developed from the separately supplied SCES proposal. The [policy manifest](../../evidence/v1/policy.json) records its SHA-256 and the exact digests of the adopted bundle. The [architecture decision](../decisions/EVIDENCE_ARCHITECTURE.md) records the external precedents and their limits.

## Adversarial review of the policy

| Finding | Resolution |
| --- | --- |
| A declaration of independent review could become a second copy of the original judgment. | Require sequential, separate execution identities, distinct inspection captures and logs, both bound to exact claim and dependency revisions. Require release approval to verify actual execution provenance. |
| A source could be intact and authentic while failing to support the claim. | Check cited spans and source role mechanically. Require an explicit independently recorded semantic assessment for support and preserve rejected or inconclusive assessments. |
| Exact byte preservation could be impossible for lawful access reasons. | Require the strongest durable locator and a preservation limitation when bytes cannot be retained, with actual firsthand inspections still required. A controlled route is not a substitute for direct access. |
| A generic evidence rank could elevate official documentation, observations, or AI text to normative authority. | Enforce explicit roles and modalities, preserve derivative origins, and limit the secondary-source exception to reviewed historical or descriptive claims when primary material is unavailable. |
| An independent review pass could be confused with resolution, or a missing source with an absence finding. | Keep evidence and verification states separate. Require explicit absence evidence, preserve conflicting positions, and refuse unsupported projections. |
| Historical immutability could prevent prompt correction, or apparent history could introduce an unchecked release. | Compare the trusted predecessor tree, append dispositions and advisories, and independently rebuild newly active bundles from exact input commits. Preserve prior publications and remove compromised active status. |
| A registry-wide snapshot could make unrelated research invalidate published outputs. | Store one file per record revision. Bind publication to its exact input commit and its dependency closure. Recheck current eligibility without regenerating an unrelated artifact. |
| Additional prose and unpublished outputs could elude the structured gate. | Ship the checked factual payload and require a release mapping and authorized review of every material claim in additional formats. Maintain an approved publisher path. |

The proposal's independent-review, exception, and versioning requirements remain binding. The standard specifies how that review is recorded and how a deterministic gate differs from scientific adjudication. It uses explicit claim records in the common contracts, so a domain-level validated binding must still materialize and check each member.

## Validation scope

The [executable suite](../../tests/sces/test_validation.py) uses synthetic Language, Runtime, Platform, and Specification Index scenarios, with distinct predicates and scopes. It checks positive publication, deliberately invalid inputs, rejection after independent-review findings, release integrity, and revision custody. Synthetic receipts are test inputs. This policy review does not constitute a qualified release of index knowledge or a human peer review.

Machine validation cannot authenticate fabricated but internally consistent receipt exports, prove an undeclared source dependency, decide semantic entailment from source prose, discover all counterevidence, or prevent publication through an unrestricted external path. The protocol assigns each of those controls to direct inspection, release authorization, and repository protections.
