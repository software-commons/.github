"""Offline registry and publication checks for SCES-1.0."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker


POLICY = "SCES-1.0"
POLICY_ROOT = Path(__file__).resolve().parents[2]
RECORD_KINDS = {"source", "claim", "dependency", "verification", "disposition", "conflict"}
SUPPORT = {"support", "corroboration", "premise"}
MUTABLE = {"latest", "current", "head", "main", "master", "any", "unknown", "unspecified"}
ROLES = {
    "normative": {"governing"},
    "documented": {"official-documentation"},
    "implemented": {"implementation"},
    "historical": {"primary-history", "secondary"},
    "descriptive": {"governing", "official-documentation", "implementation", "primary-history",
                    "primary-study", "observation", "secondary"},
    "reported": {"primary-study"},
    "observed": {"observation"},
    "derived": set(),
}


class Invalid(ValueError):
    """A required contract or qualification check failed."""


def require(condition, code, detail):
    if not condition:
        raise Invalid(f"{code}: {detail}")


def digest(data):
    return sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def unique_pairs(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "duplicate-key", name)
        result[name] = value
    return result


def invalid_number(token):
    raise Invalid(f"non-integer-number: {token}")


def decode(data, path):
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs,
                           parse_float=invalid_number, parse_constant=invalid_number)
        canonical(value)
        return value
    except (UnicodeError, ValueError, RecursionError) as error:
        raise Invalid(f"json {path}: {error}") from error


def key(record):
    return record["kind"], record["id"], record["revision"]


def instant(stamp):
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def checked_path(root, relative):
    path = root / relative
    require(path.is_relative_to(root) and path.resolve() == path and
            all(part not in (".", "..") for part in Path(relative).parts),
            "unsafe-path", relative)
    return path


def read_file(root, relative):
    path = checked_path(root, relative)
    require(path.is_file(), "missing-file", relative)
    return path.read_bytes()


def git(root, *args):
    completed = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    require(completed.returncode == 0, "git", " ".join(args))
    return completed.stdout


def policy_bundle(root=POLICY_ROOT):
    manifest = decode(read_file(root, "evidence/v1/policy.json"), "policy manifest")
    require(manifest["policy"] == POLICY, "policy", "unexpected version")
    files = manifest["files"]
    require(digest(canonical(files)) == manifest["sha256"], "policy", "manifest digest")
    for path, expected in files.items():
        require(digest(read_file(root, path)) == expected, "policy", path)
    return manifest["sha256"]


def acyclic(graph, code):
    # Iterative DFS also handles chains deeper than Python's recursion limit.
    done = set()
    for start in graph:
        if start in done:
            continue
        active = {start}
        stack = [(start, iter(graph.get(start, ())))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                active.remove(node)
                done.add(node)
            else:
                require(child not in active, code, str(child))
                if child not in done:
                    active.add(child)
                    stack.append((child, iter(graph.get(child, ()))))


class Registry:
    def __init__(self, root, policy_sha, now, *, synthetic=False, repository=None):
        self.root = root.resolve()
        self.now = now
        schema_data = read_file(POLICY_ROOT, "evidence/v1/contracts.schema.json")
        self.schema = decode(schema_data, "contracts")
        Draft202012Validator.check_schema(self.schema)
        self.validators = {}
        self.files = {}
        self.record_paths = {}
        self.records = {}
        self.entries = defaultdict(list)
        self.edges = defaultdict(list)
        self.dispositions = {}
        self.conflicts = defaultdict(list)
        self.verifications = defaultdict(list)
        self.active_reviews = {}
        self.graph = defaultdict(set)
        self.runs = {}
        self.trace_records = {}
        self.adoption = self.json_file("sces/adoption.json", "adoption")
        require(self.adoption["policy_sha256"] == policy_sha, "policy", "adoption pin mismatch")
        require((self.adoption["mode"] == "synthetic") == synthetic,
                "synthetic-mode", "fixture and production modes must be selected explicitly")
        require(repository is None or repository.lower() == self.adoption["repository"],
                "repository", "adoption name differs from the caller")
        self.load_records()
        self.validate_records()

    def schema_check(self, name, value, label):
        if name not in self.validators:
            schema = {"$defs": self.schema["$defs"], "$ref": f"#/$defs/{name}"}
            self.validators[name] = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = list(self.validators[name].iter_errors(value))
        if errors:
            error = errors[0]
            field = "/".join(map(str, error.absolute_path))
            raise Invalid(f"schema: {label} {field}: {error.validator} failed")

    def file(self, relative):
        if relative not in self.files:
            self.files[relative] = read_file(self.root, relative)
        return self.files[relative]

    def json_file(self, relative, name):
        value = decode(self.file(relative), relative)
        self.schema_check(name, value, relative)
        return value

    def artifact(self, descriptor, prefix="sces/artifacts/"):
        relative = descriptor["path"]
        require(relative.startswith(prefix), "artifact-path", relative)
        data = self.file(relative)
        require(digest(data) == descriptor["sha256"], "artifact-digest", relative)
        return data

    def scan(self, relative):
        directory = checked_path(self.root, relative)
        if not directory.exists():
            return []
        require(directory.is_dir(), "unsafe-directory", relative)
        paths = []
        for child in sorted(directory.iterdir()):
            name = child.relative_to(self.root).as_posix()
            checked_path(self.root, name)
            if child.is_dir():
                paths.extend(self.scan(name))
            else:
                require(child.is_file(), "unsafe-file", name)
                paths.append(name)
        return paths

    def load_records(self):
        revisions = defaultdict(set)
        for path in self.scan("sces/records"):
            parts = path.split("/")
            require(len(parts) == 4 and parts[2] in RECORD_KINDS, "record-path", path)
            row = self.json_file(path, parts[2])
            identity = key(row)
            require(identity not in self.records, "duplicate-id", str(identity))
            require(parts[3] == f"{row['id']}--{row['revision']}.json", "record-path", path)
            self.records[identity] = row
            self.record_paths[identity] = path
            self.entries[row["kind"]].append(row)
            revisions[identity[:2]].add(identity[2])
        for identity, values in revisions.items():
            require(min(values) == 1 and max(values) == len(values), "revision-gap", str(identity))

    def resolve(self, reference, *kinds):
        target = key(reference)
        require(not kinds or target[0] in kinds, "reference-kind", str(target))
        require(target in self.records, "unresolved-reference", str(target))
        return self.records[target]

    def record_digest(self, identity):
        return digest(self.file(self.record_paths[identity]))

    def validate_records(self):
        distinct_claims = {}
        distinct_sources = {}
        for source in self.entries["source"]:
            self.check_source(source)
            identity = (source["publisher"], source["title"], source["release"], source["locator"])
            require(distinct_sources.setdefault(identity, source["id"]) == source["id"],
                    "duplicate-source", source["id"])
        for claim in self.entries["claim"]:
            self.check_claim(claim)
            identity = canonical([claim[field] for field in ("subject", "predicate", "value",
                                 "category", "modality", "polarity", "scope", "conditions")])
            require(distinct_claims.setdefault(identity, claim["id"]) == claim["id"],
                    "duplicate-claim", claim["id"])
        for edge in self.entries["dependency"]:
            self.check_dependency(edge)
        acyclic(self.graph, "provenance-cycle")
        for review in self.entries["verification"]:
            self.check_verification(review)
        self.check_dispositions()
        self.check_conflicts()

    def check_scope(self, scope, label):
        require(not any(value.lower() in MUTABLE for value in scope.values()),
                "mutable-scope", label)

    def check_source(self, source):
        self.check_scope(source["scope"], source["id"])
        instant(source["revalidation"]["due"])
        require(source["release"].lower() not in MUTABLE, "mutable-source", source["id"])
        locator = urlsplit(source["locator"])
        require((locator.scheme == "https" and locator.hostname and not locator.username and not locator.password)
                or (locator.scheme == "urn" and ":" in locator.path and not locator.netloc),
                "source-locator", source["id"])
        require("artifact" in source or "preservation_limit" in source,
                "preservation", source["id"])
        if "artifact" in source:
            self.artifact(source["artifact"])
            require(source.get("captured_sha256", source["artifact"]["sha256"]) == source["artifact"]["sha256"],
                    "source-digest", source["id"])
        for parent in source["upstream"]:
            self.resolve(parent, "source", "claim")
            self.graph[key(source)].add(key(parent))

    def check_claim(self, claim):
        self.check_scope(claim["scope"], claim["id"])
        instant(claim["revalidation"]["due"])
        predicate = self.adoption["predicates"].get(claim["predicate"])
        require(predicate is not None and claim["category"] in predicate["categories"] and
                set(predicate["scope_dimensions"]) <= claim["scope"].keys(),
                "claim-scope", claim["id"])
        require((claim["category"] == "normative") == (claim["modality"] != "descriptive"),
                "claim-modality", claim["id"])
        require(claim["modality"] != "conditional" or claim["conditions"],
                "claim-conditions", claim["id"])
        if claim["polarity"] == "documented-absence":
            require(claim["category"] == "documented" or
                    (claim["category"] == "normative" and claim["modality"] == "prohibited"),
                    "negative-basis", claim["id"])
        if claim["polarity"] == "observed-absence":
            require(claim["category"] == "observed", "negative-basis", claim["id"])
        if claim["category"] in {"observed", "derived"}:
            require("method" in claim, "method-required", claim["id"])
        require((claim["category"] == "derived") == ("derivation" in claim),
                "derivation", claim["id"])
        if "method" in claim:
            self.artifact(claim["method"])

    def check_dependency(self, edge):
        claim = self.resolve(edge["claim"], "claim")
        basis = self.resolve(edge["basis"], "source", "claim")
        self.edges[key(claim)].append(edge)
        self.graph[key(claim)].add(key(basis))
        if basis["kind"] == "claim":
            require(edge["relation"] in {"premise", "context", "counterevidence"} and
                    "citation" not in edge, "claim-dependency", edge["id"])
            return
        require(edge["relation"] != "premise" and "citation" in edge, "citation", edge["id"])
        citation = edge["citation"]
        span = {"start", "end", "sha256"} & citation.keys()
        if "artifact" in basis:
            require(len(span) == 3, "citation-range", edge["id"])
            content = self.artifact(basis["artifact"])
            start, end = citation["start"], citation["end"]
            require(start < end <= len(content) and digest(content[start:end]) == citation["sha256"],
                    "citation-digest", edge["id"])
        else:
            require(not span, "citation-range", edge["id"])

    def check_verification(self, record):
        claim = self.resolve(record["claim"], "claim")
        claim_id = key(claim)
        self.verifications[claim_id, record["phase"]].append(record)
        require(record["claim_sha256"] == self.record_digest(claim_id), "review-revision", record["id"])
        run = record["run"]
        if self.adoption["mode"] == "index":
            require(not any(run[field].lower().startswith("synthetic") for field in ("execution", "harness", "model")),
                    "synthetic-execution", record["id"])
        require(instant(run["started"]) <= instant(run["completed"]) <= self.now,
                "review-time", record["id"])
        require(self.runs.setdefault(run["execution"], run) == run, "run-identity", record["id"])
        trace_path = run["trace"]["path"]
        trace = self.artifact(run["trace"])
        if trace_path not in self.trace_records:
            captures = {}
            for line in trace.splitlines():
                entry = decode(line, trace_path)
                require(isinstance(entry, dict) and isinstance(entry.get("capture"), str)
                        and entry["capture"] not in captures, "trace-receipt", trace_path)
                captures[entry["capture"]] = entry
            self.trace_records[trace_path] = captures
        captures = self.trace_records[trace_path]
        assessments = {}
        for assessment in record["assessments"]:
            edge = self.resolve(assessment["dependency"], "dependency")
            edge_id = key(edge)
            require(key(edge["claim"]) == claim_id and edge_id not in assessments,
                    "review-edge", record["id"])
            assessments[edge_id] = assessment
        acquired = set()
        for receipt in record["acquisitions"]:
            edge = self.resolve(receipt["dependency"], "dependency")
            source = self.resolve(receipt["source"], "source")
            edge_id = key(edge)
            require(edge_id in assessments and edge_id not in acquired and
                    key(edge["basis"]) == key(source) and receipt["locator"] == source["locator"],
                    "review-acquisition", record["id"])
            require(instant(run["started"]) <= instant(receipt["retrieved_at"]) <= instant(run["completed"]),
                    "acquisition-time", record["id"])
            require("artifact" not in source or receipt.get("sha256") == source["artifact"]["sha256"],
                    "acquisition-digest", record["id"])
            require("captured_sha256" not in source or receipt.get("sha256") == source["captured_sha256"],
                    "acquisition-digest", record["id"])
            entry = {field: value for field, value in receipt.items() if field != "dependency"}
            entry.update(execution=run["execution"], event="direct-inspection")
            require(captures.get(receipt["capture"]) == entry, "trace-receipt", record["id"])
            acquired.add(edge_id)
        for edge_id, assessment in assessments.items():
            edge = self.records[edge_id]
            decisive = assessment["outcome"] in {"supports", "opposes"} or +                (edge["relation"] == "counterevidence" and assessment["outcome"] != "unverifiable")
            if decisive and edge["basis"]["kind"] == "source":
                require(edge_id in acquired, "direct-inspection", record["id"])
            if assessment["outcome"] == "supports":
                require(all(value == "pass" for value in assessment["checks"].values()),
                        "source-verification", record["id"])
        if "reproduction" in record:
            self.artifact(record["reproduction"]["artifact"])
        if record["phase"] == "independent-review":
            require("challenge" in record, "review-challenge", record["id"])

    def check_dispositions(self):
        events = defaultdict(list)
        supersession = defaultdict(set)
        for row in self.entries["disposition"]:
            target = self.resolve(row["target"], "source", "claim")
            events[key(target)].append(row)
            require(instant(row["recorded"]) <= self.now, "disposition-time", row["id"])
            if row["evidence"] == "superseded":
                require("successor" in row, "supersession", row["id"])
                successor = self.resolve(row["successor"], target["kind"])
                require(key(successor) != key(target) and
                        (successor["id"] != target["id"] or successor["revision"] > target["revision"]),
                        "supersession", row["id"])
                supersession[key(target)].add(key(successor))
            else:
                require("successor" not in row, "supersession", row["id"])
            for field, phase in (("research", "research"), ("review", "independent-review")):
                if field in row:
                    review = self.resolve(row[field], "verification")
                    require(key(review["claim"]) == key(target) and review["phase"] == phase and
                            instant(review["run"]["completed"]) <= instant(row["recorded"]),
                            "disposition-review", row["id"])
            if row["verification"] == "source-verified" and target["kind"] == "claim":
                require("research" in row, "disposition-review", row["id"])
            if row["verification"] == "independently-reviewed":
                require("research" in row and "review" in row, "disposition-review", row["id"])
            if row["evidence"] == "supported":
                require(row["finding"] in {"none", "unsupported"}, "evidence-state", row["id"])
                if row["finding"] == "unsupported":
                    require(target["kind"] == "claim" and target["polarity"] != "affirmative",
                            "negative-basis", row["id"])
            elif row["finding"] == "unsupported":
                raise Invalid(f"negative-basis: {row['id']}")
            if row["evidence"] == "conflicting":
                require(row["finding"] == "contradictory", "evidence-state", row["id"])
            if row["evidence"] == "refuted":
                require(row["finding"] == "disproven", "evidence-state", row["id"])
        for target, history in events.items():
            prior = None
            for row in sorted(history, key=lambda item: item["revision"]):
                if prior is None:
                    require(row["revision"] == 1 and "replaces" not in row, "disposition-chain", row["id"])
                else:
                    require("replaces" in row and key(row["replaces"]) == key(prior) and
                            row["id"] == prior["id"] and row["revision"] == prior["revision"] + 1 and
                            instant(row["recorded"]) >= instant(prior["recorded"]) and
                            prior["evidence"] != "superseded" and
                            (prior["verification"] != "invalidated" or row["evidence"] == "superseded"),
                            "disposition-chain", row["id"])
                prior = row
            self.dispositions[target] = prior
        acyclic(supersession, "supersession-cycle")

    def check_conflicts(self):
        latest = {}
        for row in sorted(self.entries["conflict"], key=key):
            claim_id = key(self.resolve(row["claim"], "claim"))
            previous = latest.get(row["id"])
            if previous:
                require("previous" in row and key(row["previous"]) == key(previous) and
                        key(previous["claim"]) == claim_id and
                        all(pos in row["positions"] for pos in previous["positions"]),
                        "conflict-history", row["id"])
            else:
                require("previous" not in row and row["status"] == "open", "conflict-history", row["id"])
            latest[row["id"]] = row
            positions = {}
            for position in row["positions"]:
                dependency = self.resolve(position["dependency"], "dependency")
                edge_id = key(dependency)
                require(key(dependency["claim"]) == claim_id and edge_id not in positions,
                        "conflict-scope", row["id"])
                positions[edge_id] = dependency["relation"]
            require("counterevidence" in positions.values() and set(positions.values()) & SUPPORT,
                    "conflict-positions", row["id"])
            if row["status"] == "resolved":
                require("review" in row and "decisive" in row, "conflict-review", row["id"])
                review = self.resolve(row["review"], "verification")
                require(review["phase"] == "independent-review" and key(review["claim"]) == claim_id and
                        all(positions.get(key(ref)) in SUPPORT for ref in row["decisive"]),
                        "conflict-review", row["id"])
            else:
                require("review" not in row and "decisive" not in row, "conflict-review", row["id"])
        for row in latest.values():
            self.conflicts[key(row["claim"])].append(row)

    def admissible(self, claim, edge, basis):
        require(all(claim["scope"].get(name) == value for name, value in basis["scope"].items()),
                "inapplicable-scope", edge["id"])
        if basis["kind"] == "claim":
            require(claim["category"] == "derived", "premise-category", edge["id"])
            return
        require(basis["role"] in ROLES[claim["category"]], "inadmissible-role", edge["id"])
        if basis["role"] == "secondary":
            require("primary_unavailable" in claim and claim["limitations"],
                    "secondary-exception", edge["id"])
        require(edge["citation"]["modality"] == claim["modality"], "modality-mismatch", edge["id"])

    def latest_verification(self, claim_id, phase):
        rows = self.verifications[claim_id, phase]
        require(rows, "missing-review", str(claim_id))
        latest = max(row["run"]["completed"] for row in rows)
        at_latest = [row for row in rows if row["run"]["completed"] == latest]
        require(len(at_latest) == 1, "ambiguous-review", str(claim_id))
        return at_latest[0]

    def check_eligibility(self, claim_id, assessed_at):
        if claim_id in self.active_reviews:
            return
        claim = self.records[claim_id]
        disposition = self.dispositions.get(claim_id)
        require(disposition and disposition["evidence"] == "supported" and
                disposition["verification"] == "independently-reviewed",
                "unqualified-claim", str(claim_id))
        require(instant(disposition["recorded"]) <= assessed_at, "qualification-time", claim["id"])
        require(instant(claim["revalidation"]["due"]) >= self.now, "stale-claim", claim["id"])
        research = self.latest_verification(claim_id, "research")
        review = self.latest_verification(claim_id, "independent-review")
        require(key(research) == key(disposition["research"]) and key(review) == key(disposition["review"]),
                "stale-review", claim["id"])
        require(research["conclusion"] == review["conclusion"] == "supported",
                "review-conclusion", claim["id"])
        first, second = research["run"], review["run"]
        require(first["execution"] != second["execution"] and
                first["trace"]["sha256"] != second["trace"]["sha256"] and
                first["trace"]["path"] != second["trace"]["path"] and
                instant(first["completed"]) <= instant(second["started"]) and
                not ({row["capture"] for row in research["acquisitions"]} &
                     {row["capture"] for row in review["acquisitions"]}),
                "review-independence", claim["id"])
        predicate = self.adoption["predicates"][claim["predicate"]]
        if claim["risks"] or claim["category"] == "normative" or predicate["targeted_review"]:
            require(review["challenge"]["targeted"], "targeted-review", claim["id"])
        if "method" in claim:
            require("reproduction" in review and review["reproduction"]["result"] in {"reproduced", "infeasible"},
                    "reproduction", claim["id"])
        edges = self.edges[claim_id]
        edge_ids = {key(edge) for edge in edges}
        support = [edge for edge in edges if edge["relation"] in SUPPORT]
        require(support, "unsupported-claim", claim["id"])
        for run in (research, review):
            assessments = {key(value["dependency"]): value["outcome"] for value in run["assessments"]}
            require(assessments.keys() == edge_ids and
                    all(assessments[key(edge)] == "supports" for edge in support) and
                    all(assessments[key(edge)] != "unverifiable" for edge in edges
                        if edge["relation"] == "counterevidence"),
                    "review-coverage", claim["id"])
        contrary = {key(edge) for edge in edges if edge["relation"] == "counterevidence"}
        contrary.update(key(value["dependency"]) for run in (research, review)
                        for value in run["assessments"] if value["outcome"] == "opposes")
        documented = set()
        for conflict in self.conflicts[claim_id]:
            require(conflict["status"] == "resolved" and key(conflict["review"]) == key(review),
                    "unresolved-conflict", conflict["id"])
            documented.update(key(value["dependency"]) for value in conflict["positions"])
        require(contrary <= documented, "unrecorded-conflict", claim["id"])
        independent = []
        corroboration = []
        for edge in support:
            basis = self.records[key(edge["basis"])]
            self.admissible(claim, edge, basis)
            origins = self.lineage(key(basis), claim, assessed_at)
            (corroboration if edge["relation"] == "corroboration" else independent).append(origins)
        for index, origins in enumerate(corroboration):
            require(origins and any(other and origins.isdisjoint(other) for other in independent) and
                    all(origins.isdisjoint(other) for other in corroboration[index + 1:]),
                    "corroboration-independence", claim["id"])
        if claim["corroboration_required"] and not corroboration:
            require(any(left and right and left.isdisjoint(right)
                        for index, left in enumerate(independent) for right in independent[index + 1:]),
                    "corroboration-independence", claim["id"])
        self.active_reviews[claim_id] = (research, review)

    def lineage(self, start, claim, assessed_at):
        seen = set()
        origins = set()
        pending = [start]
        while pending:
            identity = pending.pop()
            if identity in seen:
                continue
            seen.add(identity)
            record = self.records[identity]
            state = self.dispositions.get(identity)
            require(not state or (state["evidence"] not in {"superseded", "refuted", "conflicting", "insufficient"}
                                  and state["verification"] not in {"invalidated", "review-failed"}),
                    "inactive-evidence", record["id"])
            require(instant(record["revalidation"]["due"]) >= self.now,
                    "stale-evidence", record["id"])
            if record["kind"] == "claim":
                self.check_eligibility(identity, assessed_at)
                pending.extend(key(edge["basis"]) for edge in self.edges[identity] if edge["relation"] in SUPPORT)
            else:
                require(record["role"] != "ai-generated" and
                        (claim["category"] != "normative" or record["role"] == "governing"),
                        "inadmissible-lineage", record["id"])
                origins.add(("origin", record["origin"]))
                fingerprint = record.get("captured_sha256", record.get("artifact", {}).get("sha256"))
                if fingerprint:
                    origins.add(("bytes", fingerprint))
                pending.extend(key(parent) for parent in record["upstream"])
        return origins

    def check_history(self, base):
        if not base:
            current = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--verify", "HEAD"],
                                     capture_output=True)
            if current.returncode:
                return None, set()
            base = current.stdout.decode().strip()
        known_releases = set()
        require(re.fullmatch(r"[0-9a-f]{40}", base), "base-commit", str(base))
        prefixes = ("sces/records", "sces/artifacts", "sces/releases", "sces/advisories")
        paths = git(self.root, "ls-tree", "-r", "-z", "--name-only", base, "--", *prefixes)
        for path in paths.decode().rstrip("\0").split("\0"):
            if path:
                require(self.file(path) == git(self.root, "show", f"{base}:{path}"),
                        "history-rewrite", path)
                if path.startswith("sces/releases/"):
                    known_releases.add(path.split("/")[2])
        old = git(self.root, "ls-tree", "--name-only", base, "--", "sces/publication.json")
        previous = None
        if old:
            previous = decode(git(self.root, "show", f"{base}:sces/publication.json"), "previous selection")
        return previous, known_releases

    def check_releases(self):
        reports = {}
        by_release = defaultdict(set)
        for path in self.scan("sces/releases"):
            parts = path.split("/")
            require(len(parts) == 4 and parts[-1] in {"claims.json", "qualification.json"},
                    "release-file", path)
            by_release[parts[-2]].add(parts[-1])
        for release, names in by_release.items():
            require(names == {"claims.json", "qualification.json"}, "incomplete-release", release)
            path = f"sces/releases/{release}/qualification.json"
            report = self.json_file(path, "qualification")
            require(report["release"] == release and report["repository"] == self.adoption["repository"] and
                    report["synthetic"] == (self.adoption["mode"] == "synthetic") and
                    self.file(path) == canonical(report), "release-report", release)
            require([item["path"] for item in report["artifacts"]] ==
                    [f"sces/releases/{release}/claims.json"], "release-artifacts", release)
            for artifact in report["artifacts"]:
                self.artifact(artifact, "sces/releases/")
            reports[release] = report
        return reports

    def check_advisories(self, reports):
        withdrawn = set()
        for path in self.scan("sces/advisories"):
            advisory = self.json_file(path, "withdrawal")
            report_path = advisory["report"]["path"]
            self.artifact(advisory["report"], "sces/releases/")
            release = report_path.split("/")[-2]
            require(release in reports and report_path.endswith("/qualification.json") and
                    path == f"sces/advisories/{release}.json" and instant(advisory["recorded"]) <= self.now,
                    "withdrawal-report", path)
            for reference in advisory["affected"]:
                self.resolve(reference, "claim")
                require(reference in reports[release]["claims"], "withdrawal-claim", path)
            withdrawn.add(release)
        return withdrawn

    def pinned_inputs(self, selection):
        source_commit = selection["source_commit"]
        git(self.root, "merge-base", "--is-ancestor", source_commit, "HEAD")
        source_paths = set(git(self.root, "ls-tree", "-r", "-z", "--name-only", source_commit, "--",
                               "sces/adoption.json", "sces/records", "sces/artifacts")
                           .decode().rstrip("\0").split("\0"))
        used = {"sces/adoption.json"}
        visited = set()
        pending = [key(ref) for ref in selection["claims"]]
        while pending:
            identity = pending.pop()
            if identity in visited:
                continue
            visited.add(identity)
            record = self.records[identity]
            used.add(self.record_paths[identity])
            if identity in self.dispositions and (identity[0] != "claim" or identity in self.active_reviews):
                pending.append(key(self.dispositions[identity]))
            if identity[0] == "claim" and identity in self.active_reviews:
                pending.extend(key(edge) for edge in self.edges[identity])
                pending.extend(key(row) for row in self.active_reviews[identity])
                pending.extend(key(row) for row in self.conflicts[identity])
            if identity[0] == "dependency":
                pending.append(key(record["basis"]))
            if identity[0] == "source":
                pending.extend(key(ref) for ref in record["upstream"])
            for descriptor in (record.get("artifact"), record.get("method"),
                               record.get("run", {}).get("trace"), record.get("reproduction", {}).get("artifact")):
                if descriptor:
                    used.add(descriptor["path"])
            for name in ("replaces", "previous"):
                if name in record:
                    pending.append(key(record[name]))
        identities = {}
        for path in sorted(used):
            data = self.file(path)
            require(path in source_paths and data == git(self.root, "show", f"{source_commit}:{path}"),
                    "unpinned-input", path)
            identities[path] = digest(data)
        return digest(canonical(identities)), len([p for p in source_paths if p.startswith("sces/records/claim/")])

    def build(self, selection, selection_bytes):
        assessed_at = instant(selection["evaluated_at"])
        require(instant(selection["research_cutoff"]) <= assessed_at <= self.now,
                "qualification-time", selection["release"])
        identities = []
        for reference in selection["claims"]:
            claim = self.resolve(reference, "claim")
            identity = key(claim)
            identities.append(identity)
            self.check_eligibility(identity, assessed_at)
        require(len(set((kind, name) for kind, name, _ in identities)) == len(identities),
                "release-duplicate-claim", selection["release"])
        inputs, registered = self.pinned_inputs(selection)
        claim_data = []
        verification_summary = []
        for identity in sorted(self.active_reviews):
            for review in self.active_reviews[identity]:
                verification_summary.append({
                    "record": {name: review[name] for name in ("kind", "id", "revision")},
                    "phase": review["phase"], "execution": review["run"]["execution"],
                    "result": review["conclusion"], "record_sha256": self.record_digest(key(review)),
                })
        for identity in sorted(identities):
            claim_data.append({"claim": self.records[identity],
                               "dependencies": sorted(self.edges[identity], key=key)})
        properties = ("release", "dataset", "dataset_version", "schema_version", "source_commit", "scope",
                      "research_cutoff", "evaluated_at", "limitations", "exclusions")
        report = {name: selection[name] for name in properties}
        stem = f"sces/releases/{selection['release']}"
        claims_path = f"{stem}/claims.json"
        claims = canonical(claim_data)
        report.update(
            policy=POLICY, policy_sha256=self.adoption["policy_sha256"],
            repository=self.adoption["repository"], synthetic=self.adoption["mode"] == "synthetic",
            review_kind="separate-codex-executions", outcome="structure-and-recorded-review-qualified",
            selection_sha256=digest(selection_bytes), inputs_sha256=inputs,
            artifacts=[{"path": claims_path, "sha256": digest(claims)}],
            claims=sorted(selection["claims"], key=key), verifications=verification_summary,
            coverage={"selected": len(identities), "registered": registered,
                      "dependencies": sum(len(self.edges[identity]) for identity in self.active_reviews)},
            gates={"A": "structural-pass", "B": "admissibility-pass", "C": "recorded-review-pass",
                   "D": "recorded-scientific-controls-pass", "E": "artifact-integrity-pass"},
        )
        if "previous_report" in selection:
            report["previous_report"] = selection["previous_report"]
        self.schema_check("qualification", report, "generated report")
        return {claims_path: claims, f"{stem}/qualification.json": canonical(report)}

    def validate_publication(self, *, write=False, base=None):
        previous, known_releases = self.check_history(base)
        reports = self.check_releases()
        withdrawn = self.check_advisories(reports)
        selection_path = "sces/publication.json"
        if not checked_path(self.root, selection_path).exists():
            require(not write, "missing-selection", selection_path)
            require(set(reports) <= known_releases, "unqualified-history", selection_path)
            require(not previous or previous["release"] in withdrawn, "unadvised-withdrawal", selection_path)
            require(set(reports) <= withdrawn, "unadvised-withdrawal", selection_path)
            return "valid registry; no active publication"
        selection = self.json_file(selection_path, "selection")
        require(set(reports) <= known_releases | {selection["release"]},
                "unqualified-history", selection["release"])
        require(selection["release"] not in withdrawn, "withdrawn-release", selection["release"])
        if previous:
            if selection["release"] == previous["release"]:
                require(selection == previous, "release-rewrite", selection["release"])
            else:
                pointer = selection.get("previous_report", {})
                require(pointer.get("path") == f"sces/releases/{previous['release']}/qualification.json",
                        "release-predecessor", selection["release"])
        if "previous_report" in selection:
            target = selection["previous_report"]
            self.artifact(target, "sces/releases/")
            require(target["path"] in {f"sces/releases/{name}/qualification.json" for name in reports
                                       if name != selection["release"]},
                    "release-predecessor", selection["release"])
        artifacts = self.build(selection, self.file(selection_path))
        require(artifacts == self.build(selection, self.file(selection_path)),
                "nondeterministic-build", selection["release"])
        for path, data in artifacts.items():
            target = checked_path(self.root, path)
            if not write or target.exists():
                require(self.file(path) == data, "publication-digest", path)
        if write and selection["release"] not in reports:
            directory = checked_path(self.root, f"sces/releases/{selection['release']}")
            directory.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=directory.parent, prefix=".build-") as temporary:
                staged = Path(temporary) / "bundle"
                staged.mkdir()
                for path, data in artifacts.items():
                    (staged / Path(path).name).write_bytes(data)
                staged.rename(directory)
        return f"qualified {selection['release']} ({len(selection['claims'])} selected claims)"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--repository", help="actual owner/repository asserted by the CI caller")
    parser.add_argument("--base", help="full Git commit of the trusted pre-change tree")
    parser.add_argument("--write-build", action="store_true", help="write a new clean publication bundle")
    parser.add_argument("--policy-only", action="store_true", help="verify the pinned policy bundle")
    args = parser.parse_args(argv)
    try:
        policy_sha = policy_bundle()
        if args.policy_only:
            print(f"{POLICY} {policy_sha}")
        else:
            registry = Registry(args.repo, policy_sha, datetime.now(timezone.utc), repository=args.repository)
            print(registry.validate_publication(write=args.write_build, base=args.base))
        return 0
    except (Invalid, OSError, ValueError, RecursionError) as error:
        print(f"SCES rejected: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
