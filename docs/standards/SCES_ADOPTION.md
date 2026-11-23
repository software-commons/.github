# Adopt and maintain SCES

The [evidence standard](EVIDENCE_STANDARD.md) applies to each Software Commons index. Use the published `sces-v1.0` Git tag to find the policy commit. Inspect `evidence/v1/policy.json` at that commit for the exact bundle digest and file hashes. Pin the full commit SHA in the index workflow and repository agent instructions.

Software Commons research programs can use the same registry and workflow under their own repository names.

## Bootstrap an index

1. Copy [the agent instructions](../../templates/SCES_AGENTS.md) into root `AGENTS.md` and replace the pin tokens with verified values. Copy [the adoption manifest](../../templates/sces-adoption.json) to `sces/adoption.json`, set the real index name, pin the digest, and declare each predicate's scope dimensions and admitted factual categories. Set `targeted_review` for predicates whose consequences are high. This setting adds to the standard's per-claim risk requirement.
2. Set `sces/** -text` in root `.gitattributes` so Git preserves source, receipt, and release bytes. Keep one immutable file per revision in `sces/records/<kind>/<id>--<revision>.json`. Store permitted artifacts under `sces/artifacts/`. Use the [machine contracts](../../evidence/v1/contracts.schema.json) and the [protocol](../protocols/CODEX_RESEARCH_PROTOCOL.md). Record raw JSON as UTF-8 without floats or duplicate keys. Canonical output uses compact JSON with code-point-sorted object keys and a single LF terminator.
3. Copy [the workflow caller](../../templates/sces-ci.yml) to `.github/workflows/sces-ci.yml`. Replace both policy commit tokens with the same full SHA. Enable GitHub Actions and verify a successful `SCES validation` job. Keep this check active on every pull request, merge queue item if used, and default-branch push. Avoid path filtering or conditional job skips.
4. In repository rulesets or branch protection, target the default branch, require pull requests and the observed SCES check from GitHub Actions, block force-push and deletion, and keep bypass access at its operational minimum. Protect changes to the caller, adoption manifest, release path, or source filters through authorized review. GitHub rulesets with centrally required workflows can additionally pin the centrally controlled check on supported plans. A matching status name alone cannot authenticate an attacker-controlled workflow; a trusted review or organization rule must protect changes to the gate. Review changes in an authenticated, permission-limited GitHub context.
5. Restrict publication to an authorized workflow or release decision operating on protected branches and release refs. Require the exact checked bundle, authenticated review evidence, and an approved publication mapping covering all material factual assertions in the shipped output. An index must not use another release path to bypass these checks.

GitHub organization rulesets require eligible plans and owner access. Public repository rulesets can be configured by a repository administrator. With a merge queue, use `merge_group`; otherwise the required result may be missing. An index may remain under development pending these prerequisites, and must withhold canonical publication while its enforcement is unavailable. [Repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository) · [Organization rulesets](https://docs.github.com/en/organizations/managing-organization-settings/creating-rulesets-for-repositories-in-your-organization) · [Reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)

## Record and qualify a release

Use the approved, pinned checkout of this repository. Install `tools/sces/requirements.txt`. Commit the index adoption file, source and claim records, and evidence artifacts as the source snapshot. Record that full Git commit in `sces/publication.json` together with the dataset and schema versions, discovery cutoff, scope, limitations, exclusions, and exact claims. If replacing a release, link the prior report by path and SHA-256. The snapshot precedes the release selection, which avoids a self-referential commit hash.

```sh
python /path/to/pinned-policy/tools/sces/validate.py --repo . --write-build
python /path/to/pinned-policy/tools/sces/validate.py --repo . --base FULL_TRUSTED_BASE_SHA
```

The builder writes only `sces/releases/<release>/claims.json` and `qualification.json`. It reads existing evidence and review records. Commit the selection and both outputs before publication. The report points to the source commit, coverage counts, review executions and record hashes, and the canonical artifact digest. The bundle's claims include exact dependency references. Additional output formats or statements must have an approved claim-to-output binding and verification before dissemination. A GitHub Release should link to the exact checked report and attach only the verified payloads. When a release becomes invalid before a replacement is ready, remove its active selection in the same change that appends `sces/advisories/<release>.json` with its report digest, affected claim revisions, date, and reason. Add a public correction to affected downstream release surfaces.

## Enforcement map

| Requirement | Fail-closed executable check | Required review or operational control |
| --- | --- | --- |
| Sources, citations, uniqueness, applicability | Strict JSON Schema, immutable references, SHA-256 and byte ranges, role matrix, modality equality and declared dimensions. | Directly inspect source authenticity, precision, scope, applicability and entailment. Explain any controlled or locator-only access. |
| Provenance, independence, and derivation | Cycle detection, transitive basis checks, grouped origin and duplicate-byte detection, claim-bound receipts, and separately completed executions. | Verify underlying tool events, independently assess material origin dependencies, seek counterevidence and review inference strength. |
| Negative knowledge and conflicts | Distinct states, explicit absence types, review records, opposing bindings and resolution links. | Confirm that actual evidence proves the scoped absence and that adjudication addresses all known positions. |
| Verified publication and correction | Gate status, freshness dates, exact Git inputs, reproducible payload, report digest, prior report custody and immutable baseline check. | Check new evidence triggers, completeness assertions and coverage, enforce the approved publisher path, and withdraw compromised releases. |
| Source security and access | Offline validator treats artifacts as bytes and trace data and executes no artifact code. | Isolate retrieved content from agent instructions, capture genuine provenance, and respect access, retention, and redistribution terms. |

## Upgrade the policy

Open an organization policy decision for substantive amendments. Record rationale, compatibility, changed gates, affected data and required migrations. Adversarially test the proposed revision and pin its contracts, tools, and workflow in a new manifest and release. Keep earlier manifests and release refs discoverable.

Upgrade an index in a reviewed PR changing `AGENTS.md`, the adoption manifest and caller pins together. Compare old and new results against the same evidence history. Preserve earlier qualification reports. Where a claim needs new evidence or review, append the appropriate revision and leave it out of the new active canonical release until qualified. Record reassessments separately with both release identities and policy revisions. Never reinterpret a previous qualification in place.
