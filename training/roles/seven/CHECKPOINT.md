# Seven Training Checkpoint Support

This role-level support tooling is intentionally separate from immutable versioned training packages.

## Purpose

`tools/training_checkpoint.py` provides **mechanical** checks for:
- package file integrity against a package manifest;
- module ordering/identity;
- creation of a training-checkpoint skeleton;
- structural verification that a recorded training run satisfied the package's BASE_READY gate.

It does **not** execute ChatGPT training, grade semantic answers, create write authority, or prove subjective/runtime continuity.

## Commands

```bash
python training/roles/seven/tools/training_checkpoint.py verify-package   training/roles/seven/v1.0.0
```

```bash
python training/roles/seven/tools/training_checkpoint.py init-checkpoint   training/roles/seven/v1.0.0   /tmp/seven-training-checkpoint.json   --source-repo thebrazenbeard/project-achilles   --source-commit <EXACT_40_HEX_COMMIT>   --source-path training/roles/seven/v1.0.0
```

After modules are actually evaluated, populate PASS evidence references, the independent qualification outcome, and set `base_status` only if the package's BASE_READY requirements are satisfied.

```bash
python training/roles/seven/tools/training_checkpoint.py verify-checkpoint   training/roles/seven/v1.0.0   /tmp/seven-training-checkpoint.json
```

A successful result is `BASE_READY_MECHANICAL_GATE_PASS`, not an independent semantic qualification. The evaluator's qualification evidence remains necessary.

## Fail-closed rules

The tool rejects duplicate/non-finite JSON, unsafe paths, missing or hash-mismatched required files, case-colliding manifest paths, reordered/missing modules, absent evidence references, qualification other than `QUALIFICATION_PASS`, any critical failure, mutable operational state loaded before freeze, or an inexact source commit identity.

## Authority boundary

Repository access and this script are nonauthorizing. `CAN_WRITE != MAY_WRITE`. Operational external writes still require current authority applicable to that service unless a present direct-user instruction explicitly authorizes the exact effect.
