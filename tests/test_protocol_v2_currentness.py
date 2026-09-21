from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_protocol_explicitly_supersedes_frozen_lease_folklore():
    text = (ROOT / "PROTOCOL_V2_CURRENT.md").read_text(encoding="utf-8")
    assert "Frozen training boundary" in text
    assert "superseded for current execution" in text
    assert "Writer leases are concurrency controls, not permission generators." in text
    assert "repository-local steward" in text
    assert "Class 1 assigned isolated/reversible work: proceed" in text


def test_frozen_training_history_is_preserved_not_rewritten():
    bootstrap = (
        ROOT / "training" / "roles" / "seven" / "v1.0.0" / "BOOTSTRAP.md"
    ).read_text(encoding="utf-8")
    authority = (
        ROOT / "training" / "roles" / "seven" / "v1.0.0" /
        "modules" / "06-authority-escalation.md"
    ).read_text(encoding="utf-8")
    assert "This package does not grant a writer lease" in bootstrap
    assert "GitHub effects route through Five's lease boundary" in authority


def test_readme_routes_current_execution_to_v2():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Read `PROTOCOL_V2_CURRENT.md`" in text
    assert "older permission/lease exercises do not override" in text
