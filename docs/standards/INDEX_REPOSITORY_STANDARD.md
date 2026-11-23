# Software Commons Index Repository Standard

| Document field | Value |
| --- | --- |
| Revision | SCIRS-1.0 |
| Authority | Software Commons |
| Scope | Software Commons knowledge index repositories |
| Evidence baseline | SCES-1.0 at `ab26f278422772f2d9e5d4dd016407d14372a710` |
| Evidence bundle SHA-256 | `14da3f31f697ab828d4a4560f060dbe511861020db54bea7bc531e20ea0855ce` |

Software Commons adopts revisions of this standard through its [governance process](../GOVERNANCE.md). A proposal becomes binding on merge into the organization repository. Pin the adopted revision by full Git commit in each index. MUST, MUST NOT, SHOULD, and MAY carry the meanings in [BCP 14](https://www.rfc-editor.org/info/bcp14) when written in uppercase.

This standard defines the shared repository architecture and how it connects to the [Index Repository Policy](../INDEX_POLICY.md) and the binding [Software Commons Evidence Standard](EVIDENCE_STANDARD.md). The evidence standard governs eligibility and provenance. A repository architecture decision cannot waive an evidence requirement.

## Domain and ownership

Each index MUST define one coherent knowledge domain, name its owning repository, document its inclusion and exclusion criteria, and identify adjacent domains. The organization owns this standard. Each index owns its scoped identities, structural vocabulary, factual predicates, registered evidence, and released datasets. Upstream authorities retain control over their specifications, implementations, and publications.

An index MUST use references to another index's governed entities when those entities have their own owning index. An external reference MUST identify the owning repository, exact target identifier, and immutable release or revision. Document how a consumer resolves the target. A working branch, moving label, or provisional candidate MUST NOT be a published target. An index MAY preserve bounded local context or a provisional lead without assigning it the authority of an external canonical record. Cross-index identity and semantic assertions remain subject to the applicable SCES review.

| Shared requirement | Domain extension |
| --- | --- |
| One scoped identity registry with stable records | Entity kinds, taxonomy, inclusion policy, and governed relationship types |
| Opaque permanent IDs and deterministic sharding | The documented portable identifier representation and shard rule |
| Exact, qualified bindings for factual attributes | Predicate vocabulary, claim categories, scope dimensions, and mappings from claims to consumer fields |
| Reproducible discovery and coverage | Sources, lead-selection and reconciliation methods, domain-specific research dimensions, and exclusions |
| Reproducible versioned releases | Optional consumer formats, search indexes, and additional domain validation |

The architecture MUST support languages, runtimes, platforms, specifications, formats, and protocols without requiring a shared ontology, a central database, a runtime service, or a live lookup of another index.

## Repository layout

| Path | Contract |
| --- | --- |
| `README.md`, `AGENTS.md`, `LICENSE`, `.gitattributes` | Document the index, bind its adopted policies, and specify license and Git byte handling. Document any distinct license or terms for data and upstream evidence. |
| `registry/entities/<shard>/<id>.json` | One independently maintainable identity record per entity. Record the domain kind inside the file. An index may use an additional immutable allocation directory. |
| `registry/candidates/` | Independently maintainable discovery leads, dispositions, exact origins, and links to any approved identities. |
| `registry/coverage/current.json`, `registry/coverage/snapshots/` | Current discovery and depth assessment and retained snapshots with a declared cutoff and method. |
| `sces/` | The adopted SCES layout and machine contracts. Use `sces/adoption.json`, `sces/records/<kind>/<id>--<revision>.json`, and `sces/artifacts/` as specified by SCES. Active publication uses `sces/publication.json` and `sces/releases/<release>/`. |
| `schemas/domain/` | Machine-readable schemas for the domain model, its coverage data, and any exported formats the index defines. |
| `research/` | Discovery, predecessor mappings, methods, and review findings. Use the SCES registry for governed sources, claim revisions, and verifications. |
| `tools/`, `tests/`, `docs/`, `.github/workflows/` | Repeatable maintenance, validation, documented operating procedures, and GitHub checks. |

Git does not require placeholder files for paths with no records. Domain documentation MUST identify each path and the authoritative record types it contains. Generated search data, aggregate exports, crosswalk views, and incoming relationship views MUST be reproducible from the underlying records. Keep these separate from canonical input. An index MAY publish generated assets outside Git when the applicable evidence contract permits it. It MUST retain the SCES files required by its policy revision.

## Identity and lineage

Each candidate and accepted entity MUST have a stable, opaque identity. Canonical entity names, aliases, classifications, versions, and other mutable attributes MUST NOT determine an ID or path. The assigned ID and path persist through display-name changes, reclassification, and retirement. Derive the shard solely from the opaque ID under a documented immutable rule. If an index uses an additional allocation directory, its identifier MUST be fixed at allocation and independent of mutable classification. A lowercase 32-character UUID without punctuation and its first two characters as a shard is one conforming design.

An entity record owns domain structural data such as its identifier, kind, preferred presentation label, and bindings to applicable claims. Externally factual identity or presentation assertions, such as alternate names, classifications, governance boundaries, editions, and lineage, MUST resolve to the exact qualified claim supporting the asserted field or relation. An ID allocation records an index decision. The supporting evidence establishes why the decision covers the objects claimed. Define the minimum qualified identity and profile expected for admission. Rich technical and historical properties belong in SCES claims and derived projections.

Store renames, merges, splits, replacements, and retirement without reusing IDs. A materially changed identity MUST preserve references to its predecessors and successors through explicit, typed lineage, anchored to the decision and its qualified evidence. A prior ID MUST remain resolvable in history and MUST NOT silently become an alias for an ambiguous split. Document fixture assertions or production checks for duplicate IDs, improper relocation, missing targets, and ambiguous or cyclic lineage. Competing records with similar names require investigation. Shared implementations and lexical similarity alone cannot establish identity, equivalence, or direction of lineage.

An index MUST discover records by traversing its documented directories, checking schema, path, and unique identity. An alias belongs to its entity. A relationship has one owning record or exact qualified assertion. Derive reverse lookup rather than maintaining a second authoritative copy. Search and resolve operations SHOULD preserve ambiguity and offer exact identity lookup.

## Research and coverage

Discovery and canonical admission are separate operations. Each discovered lead MUST record its identifier, source or campaign provenance, and disposition with a reason. Keep unresolved, contested, inaccessible, rejected, and duplicate leads inspectable. A candidate confirmed as equivalent to an accepted entity SHOULD resolve to that identity without replacing its source identity. Candidate material and synthetic fixtures MUST be clearly distinguishable from accepted records and qualified releases.

Record a cutoff, included ecosystems and discovery paths, exclusions and inaccessible areas, predecessor revisions, reconciliation choices, and per-disposition counts in the coverage assessment. Measure population investigation and research depth independently. Report which dimensions were examined, verified, inapplicable, unresolved, or outside the release. Counts refer to the declared discovery method and scope. Claims of completeness require their own qualified evidence.

An index MUST preserve the difference between research eligibility, evidence status, and publication selection. Discovery leads, mutable upstream search results, and analytical datasets from another project are admissible leads subject to source inspection and adjudication under SCES. Imported identifiers require a provenance-aware crosswalk. If an upstream artifact is unavailable, document the gap and identify any independent reconstruction separately.

## SCES adoption and release controls

Before substantive canonical research, each index MUST adopt the verified SCES revision and bundle digest. Follow the binding [adoption procedure](SCES_ADOPTION.md), machine contracts, and [Codex Research Protocol](../protocols/CODEX_RESEARCH_PROTOCOL.md). The adoption manifest MUST declare domain predicates and required scopes. Root `AGENTS.md` and the reusable CI caller MUST pin the same full policy commit. Keep the required SCES file paths and their immutable bytes, including the `sces/** -text` Git attributes rule.

Protected default-branch changes MUST require pull requests and the pinned SCES validation check reported by GitHub Actions. Run the check on all pull requests and default-branch pushes, and on merge queue entries when applicable. Apply the adopted ruleset guidance for strict checks, force-push and deletion restrictions, and controlled bypass. Evidence pins, caller workflows, source selection, and publication paths MUST receive authorized review or organization-enforced protection covering changes to those controls. A repository MUST document its protection arrangements, including any administrative gaps, and withhold canonical publication while mandatory controls are unavailable.

Each production release MUST:

1. Freeze the source commit, discovery cutoff, model revision, scope, and exact selected claim revisions. Every domain record used in the release MUST match its bytes at the frozen source commit. Preserve the source-to-claim-to-entity mapping and the release's relationship to its predecessor.
2. Write the selection to `sces/publication.json` and use the pinned validator to build and verify the required release artifacts via the adopted release procedure. The release manifest records the policy version and digest, input and artifact identities, verified coverage, exclusions, limits, and outcomes from all applicable qualification gates.
3. Document, check, and obtain authorization for the claim-to-output mapping for every additional consumer artifact. Gate all material factual output, including attributes encoded as relationships and labels that assert factual identity. Canonical publication MUST use the exact validated bytes after approval. A repository MUST prevent alternate publication paths from conferring canonical status on unchecked output.
4. Supply independent consumers a versioned payload, schema and index identity, qualification report, checksums, and instructions for reproducing the artifacts from the frozen inputs. Independent reproducibility MUST work without a live index service or automatically fetching mutable sources.

Verify authentic, independent execution records and actual source inspection before approval. Structural validation exposes format, integrity, and linkage defects. Semantic authority, applicability, and scientific completeness require the corresponding SCES review. A repository MUST retain corrections, withdrawals, historical releases, and identity supersession under the applicable policy.

## Maintenance guarantees and tests

Index maintainers MUST be able to add a record without editing a global catalog. Acceptance or revision may also add genuinely required sources, claims, verification, candidate dispositions, or coverage records. A change to one identity or evidence record MUST NOT rewrite unrelated canonical records. Normal lookup and validation MUST be read-only. Build output MUST be derived deterministically and written separately from canonical inputs.

Each index's regression suite MUST check the applicable behaviors below:

- Adding or editing an entity updates only its record and required supporting records. An alias update does not require a central alias table.
- Display-name changes preserve the identifier and file path. Registration of a new source preserves existing source bytes and stable revisions.
- Adding a relationship does not require a hand-maintained inverse. Unknown local targets and unpinned external targets fail validation.
- A new cutoff does not rewrite unrelated entity records. Validation and build leave canonical inputs byte-identical.
- Builds from identical inputs produce identical artifact bytes. Unsupported records, bad bindings, and invalidated claims cannot reach a canonical export.

The initial shared architecture qualification MUST exercise synthetic language, runtime, platform, and specification cases. Test permanent identities, distinct domain kinds, exact SCES source and claim revisions, versioned assertions, cross-index references, incremental writes, qualification, and reproducible exports. Fixtures MUST remain separate from production research and publication. See the [initial qualification record](SCIRS_1_0_QUALIFICATION.md).

## Pinning and change control

Document the exact adopted standard revision and organization commit in the index. Protect policy changes through a reviewed pull request. Proposed revisions MUST identify compatibility and migration impacts, demonstrate qualification against independent domain cases where relevant, and preserve old public references and release reproducibility. An index may revise its extension independently while preserving community policy and the exact contracts that governed historical releases.
