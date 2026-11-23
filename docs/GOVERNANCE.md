# Governance

## Decision authority

| Area | Responsibility |
| --- | --- |
| Organization-wide policy | This repository records the mission, shared principles, and requirements for the organization’s index repositories. |
| Index-specific knowledge | Each index is responsible for its scope, record identities, representations, validation, and releases. Its authority extends to its own published records. |
| Upstream standards and primary sources | Authority depends on the claim. A governing specification is authoritative for its requirements within the relevant edition and scope. An implementation or study can provide primary evidence about what it implemented or observed. |
| Downstream products | Each consuming project owns its integration, interpretation in product context, and engineering decisions. |

## Making and recording decisions

Use issues to discuss proposals and pull requests to make changes. GitHub repository permissions determine who can merge changes. Decisions about shared policy are recorded here. Decisions about an index's domain model or records are recorded in that index.

Research notes, proposals, and review comments retain their provisional status. An accepted decision is recorded in merged policy, decision documentation, or index records, as appropriate. For material decisions, record the rationale, evidence, affected scope, and remaining uncertainty in the relevant repository. Link the decision to its discussion where available.

## Changes across indexes

Discuss a cross-index change in the repository that owns the record or policy and link the discussion from each affected repository. Confirm affected identifiers, versions, and publication dependencies with the affected repositories before treating the proposal as adopted across them. Each repository records its own adoption and releases on its own schedule.

Preserve compatibility where practical. Document breaking changes explicitly, including affected identifiers or data contracts, the versions involved, and any migration path. Preserve access to historical releases and the sources used to produce them. See the [interoperability policy](INDEX_POLICY.md#cross-index-interoperability).
