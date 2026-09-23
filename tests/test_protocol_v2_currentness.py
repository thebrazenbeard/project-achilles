import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProtocolV2CurrentnessTests(unittest.TestCase):
    def test_current_protocol_explicitly_supersedes_frozen_lease_folklore(self):
        text = (ROOT / "PROTOCOL_V2_CURRENT.md").read_text(encoding="utf-8")
        self.assertIn("Frozen training boundary", text)
        self.assertIn("superseded for current execution", text)
        self.assertIn(
            "Writer leases are concurrency controls, not permission generators.",
            text,
        )
        self.assertIn("repository-local steward", text)
        self.assertIn("Class 1 assigned isolated/reversible work: proceed", text)

    def test_frozen_training_history_is_preserved_not_rewritten(self):
        bootstrap = (
            ROOT / "training" / "roles" / "seven" / "v1.0.0" / "BOOTSTRAP.md"
        ).read_text(encoding="utf-8")
        authority = (
            ROOT
            / "training"
            / "roles"
            / "seven"
            / "v1.0.0"
            / "modules"
            / "06-authority-escalation.md"
        ).read_text(encoding="utf-8")
        self.assertIn("This package does not grant a writer lease", bootstrap)
        self.assertIn("GitHub effects route through Five's lease boundary", authority)

    def test_readme_routes_current_execution_to_v2(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Read `PROTOCOL_V2_CURRENT.md`", text)
        self.assertIn("older permission/lease exercises do not override", text)


if __name__ == "__main__":
    unittest.main()
