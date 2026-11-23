# Index repository policy

## Naming and scope

Use `<singular-domain>-index` for a repository that publishes a knowledge index. Candidate names include `language-index`, `platform-index`, `runtime-index`, `specification-index`, `format-index`, and `protocol-index`. These names illustrate possible future domains. Organization metadata, tooling, schemas, and other supporting repositories may use names that describe their purpose.

## Requirements for each index

1. Address one independently coherent knowledge domain with a clear reason to publish it separately.
2. Define the scope, coverage, and exclusions, including boundaries with neighboring domains.
3. Own the domain-specific identities and normalized representations it publishes. Document identifier assignment and lifecycle.
4. Identify authoritative upstream sources by claim type and explain the basis for their authority.
5. Preserve provenance and distinctions that affect interpretation, comparison, or use.
6. Distinguish established claims, interpretations, empirical observations, and uncertainty.
7. Publish independently consumable, versioned, machine-readable releases with documentation sufficient for consumers to select and interpret a release.
8. Reference records owned by other indexes through documented identifiers and versions. Preserve the owning index as the canonical reference.
9. Maintain validation and reproducibility mechanisms appropriate to the domain, such as integrity checks, pinned inputs, and documented verification steps.
10. Document material limitations, coverage gaps, and unresolved conflicts.

Each index must document the licensing of its published material, any upstream terms relevant to its reuse, and which source content can be redistributed. The organization repository's license applies to that repository.

Each index must [adopt SCES](standards/SCES_ADOPTION.md) before substantive research and apply the pinned qualification gates before publishing a canonical knowledge release.

## Cross-index interoperability

A reference must identify the owning index and record unambiguously. Include the target release or another documented immutable revision when the reference is used in a published artifact. Document how a consumer can resolve the reference and interpret the referenced representation at that revision. Distinguish index release versions from the revisions of underlying sources, and identify source revisions through editions, versioned locators, immutable identifiers, or comparable evidence.

Indexes choose their own representations and release mechanisms. Their releases should remain usable independently, with external references documented as part of the data when relevant. A universal schema, centralized database, global ontology, or mandatory runtime dependency would require separate research and an accepted decision under the [governance policy](GOVERNANCE.md).
