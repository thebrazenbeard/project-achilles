#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

PACKAGE_ID = "BT2_SEVEN_ROLE_TRAINING"
ROLE = "Seven"
CHECKPOINT_SCHEMA = "BT2_SEVEN_TRAINING_CHECKPOINT_V1"
SOURCE_REPOSITORY = "thebrazenbeard/project-achilles"
SOURCE_PATH_PREFIX = "training/roles/seven"
H40 = re.compile(r"^[0-9a-f]{40}$")
H64 = re.compile(r"^[0-9a-f]{64}$")


class TrainingCheckpointError(ValueError):
    pass


def load_json(path: Path):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise TrainingCheckpointError(f"duplicate JSON key in {path}: {k}")
            out[k] = v
        return out

    def bad(v):
        raise TrainingCheckpointError(f"non-finite JSON value in {path}: {v}")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=pairs,
            parse_constant=bad,
        )
    except json.JSONDecodeError as e:
        raise TrainingCheckpointError(f"invalid JSON: {path}: {e}") from e


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def digest_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()


def relpath(s):
    if not isinstance(s, str) or not s:
        raise TrainingCheckpointError("path must be a nonempty string")
    if "\\" in s:
        raise TrainingCheckpointError(f"path must use '/' separators: {s}")
    p = Path(s)
    if p.is_absolute() or ".." in p.parts:
        raise TrainingCheckpointError(f"unsafe path: {s}")
    if p.as_posix() != s:
        raise TrainingCheckpointError(f"path is not canonical: {s}")
    return p


def safe_regular_file(root: Path, rp: Path):
    root = root.resolve()
    current = root
    for part in rp.parts:
        current = current / part
        if current.is_symlink():
            raise TrainingCheckpointError(
                f"symlinked package path is not allowed: {rp.as_posix()}"
            )
    try:
        resolved = current.resolve(strict=True)
    except FileNotFoundError as e:
        raise TrainingCheckpointError(
            f"missing required file: {rp.as_posix()}"
        ) from e
    try:
        resolved.relative_to(root)
    except ValueError as e:
        raise TrainingCheckpointError(
            f"package path escapes root: {rp.as_posix()}"
        ) from e
    if not resolved.is_file():
        raise TrainingCheckpointError(f"not a regular file: {rp.as_posix()}")
    return resolved


def verify_package(root: Path):
    root = root.resolve()
    mp = safe_regular_file(root, Path("TRAINING_MANIFEST.json"))
    m = load_json(mp)
    if m.get("package_id") != PACKAGE_ID:
        raise TrainingCheckpointError("wrong package_id")
    if not isinstance(m.get("role"), dict) or m["role"].get("identity") != ROLE:
        raise TrainingCheckpointError("wrong role identity")
    version = m.get("training_package_version")
    if not isinstance(version, str) or not version:
        raise TrainingCheckpointError("training_package_version missing")
    files = m.get("files")
    if not isinstance(files, dict) or not files:
        raise TrainingCheckpointError("manifest files map missing/empty")

    folded = {}
    count = 0
    for name, meta in files.items():
        rp = relpath(name)
        cf = name.casefold()
        if cf in folded and folded[cf] != name:
            raise TrainingCheckpointError(
                f"case-colliding manifest paths: {folded[cf]} vs {name}"
            )
        folded[cf] = name
        p = safe_regular_file(root, rp)
        st = p.stat()
        if not isinstance(meta, dict):
            raise TrainingCheckpointError(f"invalid metadata: {name}")
        eh, eb = meta.get("sha256"), meta.get("bytes")
        if not isinstance(eh, str) or not H64.fullmatch(eh):
            raise TrainingCheckpointError(f"invalid sha256 metadata: {name}")
        if not isinstance(eb, int) or isinstance(eb, bool) or eb < 0:
            raise TrainingCheckpointError(f"invalid byte metadata: {name}")
        if st.st_size != eb:
            raise TrainingCheckpointError(f"byte mismatch: {name}")
        if digest(p) != eh:
            raise TrainingCheckpointError(f"sha256 mismatch: {name}")
        count += 1

    order = m.get("module_order")
    if not isinstance(order, list) or not order:
        raise TrainingCheckpointError("module_order missing/empty")
    ids = []
    paths = []
    for n, e in enumerate(order, 1):
        if not isinstance(e, dict) or e.get("order") != n:
            raise TrainingCheckpointError("module_order must be contiguous from 1")
        mid, path = e.get("id"), e.get("path")
        if not isinstance(mid, str) or not mid or mid in ids:
            raise TrainingCheckpointError(
                "module ids must be unique nonempty strings"
            )
        relpath(path)
        if path in paths:
            raise TrainingCheckpointError("module paths must be unique")
        if path not in files:
            raise TrainingCheckpointError(
                f"module path is not covered by manifest files: {path}"
            )
        ids.append(mid)
        paths.append(path)

    policy = m.get("evaluation_policy")
    if isinstance(policy, dict) and "qualification_rubric_path" in policy:
        rubric = policy["qualification_rubric_path"]
        relpath(rubric)
        if rubric not in files:
            raise TrainingCheckpointError(
                f"qualification rubric is not covered by manifest files: {rubric}"
            )

    return {
        "package_id": PACKAGE_ID,
        "role": ROLE,
        "version": version,
        "manifest_sha256": digest(mp),
        "verified_file_count": count,
        "module_ids": ids,
        "module_paths": paths,
        "manifest_files": files,
    }


def expected_source_path(version: str):
    return f"{SOURCE_PATH_PREFIX}/v{version}"


def validate_source_metadata(pkg, repo, commit, path):
    if repo != SOURCE_REPOSITORY:
        raise TrainingCheckpointError(
            f"training_source repository must be {SOURCE_REPOSITORY}"
        )
    if not isinstance(commit, str) or not H40.fullmatch(commit):
        raise TrainingCheckpointError(
            "training_source commit must be exact lowercase 40-hex SHA"
        )
    expected = expected_source_path(pkg["version"])
    if path != expected:
        raise TrainingCheckpointError(f"training_source path must be {expected}")


def _git(cwd: Path, *args: str):
    p = subprocess.run(
        ["git", "-C", str(cwd), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", errors="replace").strip()
        raise TrainingCheckpointError(
            f"git {' '.join(args)} failed: {err or f'exit {p.returncode}'}"
        )
    return p.stdout


def _normalize_github_repo(remote: str):
    remote = remote.strip()
    if remote.startswith("git@github.com:"):
        value = remote.split(":", 1)[1]
    else:
        parsed = urlparse(remote)
        if parsed.hostname != "github.com":
            raise TrainingCheckpointError(
                f"origin is not a github.com repository: {remote}"
            )
        value = parsed.path.lstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        raise TrainingCheckpointError(f"cannot normalize GitHub origin: {remote}")
    return "/".join(parts)


def verify_source_binding(root: Path, pkg, repo, commit, path):
    validate_source_metadata(pkg, repo, commit, path)
    root = root.resolve()
    git_root = Path(
        _git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    ).resolve()
    try:
        actual_rel = root.relative_to(git_root).as_posix()
    except ValueError as e:
        raise TrainingCheckpointError(
            "package root is outside its Git repository"
        ) from e
    if actual_rel != path:
        raise TrainingCheckpointError(
            f"package checkout path mismatch: expected {path}, got {actual_rel}"
        )

    origin = _git(git_root, "remote", "get-url", "origin").decode("utf-8").strip()
    if _normalize_github_repo(origin).casefold() != repo.casefold():
        raise TrainingCheckpointError(
            f"origin repository mismatch: expected {repo}, got {origin}"
        )

    _git(git_root, "cat-file", "-e", f"{commit}^{{commit}}")
    manifest_at_commit = _git(
        git_root, "show", f"{commit}:{path}/TRAINING_MANIFEST.json"
    )
    if digest_bytes(manifest_at_commit) != pkg["manifest_sha256"]:
        raise TrainingCheckpointError(
            "TRAINING_MANIFEST.json at source commit does not match verified package"
        )

    for name, meta in pkg["manifest_files"].items():
        data = _git(git_root, "show", f"{commit}:{path}/{name}")
        if len(data) != meta["bytes"]:
            raise TrainingCheckpointError(f"source commit byte mismatch: {name}")
        if digest_bytes(data) != meta["sha256"]:
            raise TrainingCheckpointError(f"source commit sha256 mismatch: {name}")

    return {
        "repository": repo,
        "commit": commit,
        "path": path,
        "binding": "GIT_COMMIT_BYTES_MATCH",
    }


def make_checkpoint(pkg, repo, commit, path):
    validate_source_metadata(pkg, repo, commit, path)
    return {
        "schema": CHECKPOINT_SCHEMA,
        "package": {
            "package_id": pkg["package_id"],
            "training_package_version": pkg["version"],
            "role_identity": ROLE,
            "manifest_sha256": pkg["manifest_sha256"],
        },
        "training_source": {
            "repository": repo,
            "commit": commit,
            "path": path,
        },
        "modules": [
            {"id": x, "status": "PENDING", "evidence_ref": None}
            for x in pkg["module_ids"][:-1]
        ],
        "qualification": {
            "module_id": pkg["module_ids"][-1],
            "response_completed_before_rubric": False,
            "evaluator_outcome": "PENDING",
            "critical_failures": [],
            "evaluation_evidence_ref": None,
        },
        "operational_state_loaded_before_freeze": False,
        "base_status": "NOT_BASE_READY",
        "notes": [],
    }


def verify_checkpoint(root: Path, cp_path: Path):
    pkg = verify_package(root)
    cp = load_json(cp_path)
    if cp.get("schema") != CHECKPOINT_SCHEMA:
        raise TrainingCheckpointError("wrong checkpoint schema")
    p = cp.get("package")
    if not isinstance(p, dict):
        raise TrainingCheckpointError("checkpoint package section missing")
    expected = {
        "package_id": pkg["package_id"],
        "training_package_version": pkg["version"],
        "role_identity": ROLE,
        "manifest_sha256": pkg["manifest_sha256"],
    }
    for k, v in expected.items():
        if p.get(k) != v:
            raise TrainingCheckpointError(f"checkpoint package mismatch: {k}")

    src = cp.get("training_source")
    if not isinstance(src, dict):
        raise TrainingCheckpointError("training_source section missing")
    validate_source_metadata(
        pkg, src.get("repository"), src.get("commit"), src.get("path")
    )
    source_binding = verify_source_binding(
        root, pkg, src["repository"], src["commit"], src["path"]
    )

    expected_ids = pkg["module_ids"][:-1]
    mods = cp.get("modules")
    if not isinstance(mods, list) or len(mods) != len(expected_ids):
        raise TrainingCheckpointError("module checkpoint count mismatch")
    passed = []
    for mid, e in zip(expected_ids, mods):
        if not isinstance(e, dict) or e.get("id") != mid:
            raise TrainingCheckpointError(f"module order/id mismatch: {mid}")
        if e.get("status") != "PASS":
            raise TrainingCheckpointError(f"module not passed: {mid}")
        if not isinstance(e.get("evidence_ref"), str) or not e["evidence_ref"].strip():
            raise TrainingCheckpointError(f"module evidence_ref missing: {mid}")
        passed.append(mid)

    q = cp.get("qualification")
    if not isinstance(q, dict) or q.get("module_id") != pkg["module_ids"][-1]:
        raise TrainingCheckpointError("qualification module mismatch")
    if q.get("response_completed_before_rubric") is not True:
        raise TrainingCheckpointError("qualification response-before-rubric not met")
    if q.get("evaluator_outcome") != "QUALIFICATION_PASS":
        raise TrainingCheckpointError("qualification is not QUALIFICATION_PASS")
    if not isinstance(q.get("critical_failures"), list) or q["critical_failures"]:
        raise TrainingCheckpointError("critical_failures must be empty")
    if (
        not isinstance(q.get("evaluation_evidence_ref"), str)
        or not q["evaluation_evidence_ref"].strip()
    ):
        raise TrainingCheckpointError("evaluation_evidence_ref missing")
    if cp.get("operational_state_loaded_before_freeze") is not False:
        raise TrainingCheckpointError("operational state loaded before freeze")
    if cp.get("base_status") != "BASE_READY":
        raise TrainingCheckpointError("base_status is not BASE_READY")

    return {
        "status": "BASE_READY_MECHANICAL_GATE_PASS",
        "package_id": pkg["package_id"],
        "version": pkg["version"],
        "manifest_sha256": pkg["manifest_sha256"],
        "source_commit": src["commit"],
        "source_binding": source_binding["binding"],
        "modules_passed": passed,
        "qualification": "QUALIFICATION_PASS",
        "semantic_ceiling": (
            "Mechanical integrity/provenance-record gate only; this script cannot "
            "grade semantic competence or turn self-authored claims into authority."
        ),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Seven training package/checkpoint mechanical verifier"
    )
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("verify-package")
    p.add_argument("package_dir")
    p = sp.add_parser("init-checkpoint")
    p.add_argument("package_dir")
    p.add_argument("output")
    p.add_argument("--source-repo", required=True)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--source-path", required=True)
    p = sp.add_parser("verify-checkpoint")
    p.add_argument("package_dir")
    p.add_argument("checkpoint")
    a = ap.parse_args()
    try:
        if a.cmd == "verify-package":
            result = verify_package(Path(a.package_dir))
        elif a.cmd == "init-checkpoint":
            pkg = verify_package(Path(a.package_dir))
            verify_source_binding(
                Path(a.package_dir),
                pkg,
                a.source_repo,
                a.source_commit,
                a.source_path,
            )
            result = make_checkpoint(
                pkg, a.source_repo, a.source_commit, a.source_path
            )
            Path(a.output).write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = {
                "status": "CHECKPOINT_TEMPLATE_CREATED",
                "output": str(Path(a.output)),
                "source_binding": "GIT_COMMIT_BYTES_MATCH",
            }
        else:
            result = verify_checkpoint(Path(a.package_dir), Path(a.checkpoint))
    except (TrainingCheckpointError, OSError) as e:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(e)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
