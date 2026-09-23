import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "training" / "roles" / "seven" / "tools" / "training_checkpoint.py"
SPEC = importlib.util.spec_from_file_location("training_checkpoint", TOOL_PATH)
tc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tc)


def sha256(data: bytes):
    return hashlib.sha256(data).hexdigest()


def write_package(root: Path, module_path="module.md"):
    root.mkdir(parents=True, exist_ok=True)
    module = b"module\n"
    rubric = b"rubric\n"
    (root / "module.md").write_bytes(module)
    (root / "rubric.md").write_bytes(rubric)
    manifest = {
        "package_id": tc.PACKAGE_ID,
        "role": {"identity": tc.ROLE},
        "training_package_version": "1.0.0",
        "files": {
            "module.md": {"sha256": sha256(module), "bytes": len(module)},
            "rubric.md": {"sha256": sha256(rubric), "bytes": len(rubric)},
        },
        "module_order": [{"id": "M01", "order": 1, "path": module_path}],
        "evaluation_policy": {"qualification_rubric_path": "rubric.md"},
    }
    (root / "TRAINING_MANIFEST.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


class HardeningTests(unittest.TestCase):
    def test_module_order_must_be_covered_by_hashed_file_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "pkg"
            write_package(root, module_path="unhashed.md")
            with self.assertRaisesRegex(tc.TrainingCheckpointError, "not covered"):
                tc.verify_package(root)

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink support unavailable")
    def test_symlinked_parent_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            root = td / "pkg"
            outside = td / "outside"
            root.mkdir()
            outside.mkdir()
            payload = b"outside\n"
            rubric = b"rubric\n"
            (outside / "module.md").write_bytes(payload)
            (root / "rubric.md").write_bytes(rubric)
            try:
                (root / "linked").symlink_to(outside, target_is_directory=True)
            except OSError as e:
                self.skipTest(f"cannot create symlink: {e}")
            manifest = {
                "package_id": tc.PACKAGE_ID,
                "role": {"identity": tc.ROLE},
                "training_package_version": "1.0.0",
                "files": {
                    "linked/module.md": {
                        "sha256": sha256(payload),
                        "bytes": len(payload),
                    },
                    "rubric.md": {"sha256": sha256(rubric), "bytes": len(rubric)},
                },
                "module_order": [
                    {"id": "M01", "order": 1, "path": "linked/module.md"}
                ],
                "evaluation_policy": {"qualification_rubric_path": "rubric.md"},
            }
            (root / "TRAINING_MANIFEST.json").write_text(
                json.dumps(manifest) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(tc.TrainingCheckpointError, "symlinked"):
                tc.verify_package(root)

    def test_source_metadata_is_canonical(self):
        pkg = {"version": "1.0.0"}
        with self.assertRaisesRegex(tc.TrainingCheckpointError, "repository must be"):
            tc.validate_source_metadata(
                pkg, "someone/else", "a" * 40, "training/roles/seven/v1.0.0"
            )
        with self.assertRaisesRegex(tc.TrainingCheckpointError, "path must be"):
            tc.validate_source_metadata(
                pkg, tc.SOURCE_REPOSITORY, "a" * 40, "elsewhere/v1.0.0"
            )

    def test_source_binding_proves_exact_git_commit_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            pkg_root = repo / "training" / "roles" / "seven" / "v1.0.0"
            write_package(pkg_root)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Achilles Test"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "https://github.com/thebrazenbeard/project-achilles.git",
                ],
                check=True,
            )
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-q", "-m", "fixture"],
                check=True,
            )
            commit = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()
            pkg = tc.verify_package(pkg_root)
            result = tc.verify_source_binding(
                pkg_root,
                pkg,
                tc.SOURCE_REPOSITORY,
                commit,
                "training/roles/seven/v1.0.0",
            )
            self.assertEqual("GIT_COMMIT_BYTES_MATCH", result["binding"])

            changed = b"changed\n"
            (pkg_root / "module.md").write_bytes(changed)
            manifest = json.loads((pkg_root / "TRAINING_MANIFEST.json").read_text())
            manifest["files"]["module.md"] = {
                "sha256": sha256(changed),
                "bytes": len(changed),
            }
            (pkg_root / "TRAINING_MANIFEST.json").write_text(
                json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
            )
            changed_pkg = tc.verify_package(pkg_root)
            with self.assertRaisesRegex(tc.TrainingCheckpointError, "source commit"):
                tc.verify_source_binding(
                    pkg_root,
                    changed_pkg,
                    tc.SOURCE_REPOSITORY,
                    commit,
                    "training/roles/seven/v1.0.0",
                )


if __name__ == "__main__":
    unittest.main()
