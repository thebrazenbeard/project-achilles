# Seven Training Checkpoint Support

This role-level support tooling is intentionally separate from immutable versioned training packages.

## Purpose

`tools/training_checkpoint.py` provides **mechanical** checks for:
- package file integrity against a package manifest;
- module ordering/identity and coverage by the hashed manifest file set;
- rejection of symlink/path escapes from the package root;
- creation of a training-checkpoint skeleton;
- exact binding of the claimed training repository, package path, Git commit, manifest, and manifest-listed bytes;
- structural verification that a recorded training run satisfied the package's BASE_READY gate.

It does **not** execute ChatGPT training, grade semantic answers, create write authority, or prove subjective/runtime continuity.

## Commands

```bash
python training/roles/seven/tools/training_checkpoint.py verify-package training/roles/seven/v1.0.0
```

```bash
python training/roles/seven/tools/training_checkpoint.py init-checkpoint \
  training/roles/seven/v1.0.0 \
  /tmp/seven-training-checkpoint.json \
  --source-repo thebrazenbeard/project-achilles \
  --source-commit <EXACT_40_HEX_COMMIT> \
  --source-path training/roles/seven/v1.0.0
```

`init-checkpoint` now verifies that the supplied commit exists in the local Git repository, the checkout origin resolves to `thebrazenbeard/project-achilles`, the package is at the canonical versioned path, and every manifest-listed byte at that commit matches the locally verified package.

After modules are actually evaluated, populate PASS evidence references, the independent qualification outcome, and set `base_status` only if the package's BASE_READY requirements are satisfied.

```bash
python training/roles/seven/tools/training_checkpoint.py verify-checkpoint \
  training/roles/seven/v1.0.0 \
  /tmp/seven-training-checkpoint.json
```

A successful result is `BASE_READY_MECHANICAL_GATE_PASS`, not an independent semantic qualification. The evaluator's qualification evidence remains necessary.

## Local validation

Run the repository's dependency-free regression suite with:

```bash
python -m compileall -q training tests
python -m unittest discover -s tests -p 'test_*.py' -v
python training/roles/seven/tools/training_checkpoint.py verify-package training/roles/seven/v1.0.0
(
  cd training/roles/seven/v1.0.0
  sha256sum -c SHA256SUMS.txt
)
```

GitHub Actions execution is intentionally not made part of this repository change while the account's private-repository Actions jobs are failing before step execution. That infrastructure condition is external to this verifier and should not be confused with a verifier test failure.

## Fail-closed rules

The tool rejects duplicate/non-finite JSON, noncanonical or escaping paths, symlinked package paths, missing or hash-mismatched required files, case-colliding manifest paths, module or rubric paths outside the hashed manifest set, reordered/missing modules, false repository/path provenance, source commits whose package bytes do not match the verified manifest, absent evidence references, qualification other than `QUALIFICATION_PASS`, any critical failure, mutable operational state loaded before freeze, or an inexact source commit identity.

## Authority boundary

Repository access and this script are nonauthorizing. `CAN_WRITE != MAY_WRITE`. Operational external writes still require current authority applicable to that service unless a present direct-user instruction explicitly authorizes the exact effect.
