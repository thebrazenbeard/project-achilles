# Seven Role Training Bootstrap / Loader

Package: `BT2_SEVEN_ROLE_TRAINING`
Version: `1.0.0`

Lifecycle: `role orientation -> retrieve training manifest -> execute modules in order -> evaluate module criteria -> final qualification -> BASE_READY -> fresh operational reorientation`

## Non-authority rule

Repository access is read capability, not mutation authority. This package does not grant a writer lease, governance authority, release authority, or permission to alter itself. `CAN_WRITE != MAY_WRITE`.

## Loader procedure

1. Open `TRAINING_MANIFEST.json` from this exact versioned directory.
2. Verify package ID, role identity, version, case-sensitive paths, and every manifest-listed SHA-256.
3. Missing, substituted, duplicated, case-drifted, or hash-mismatched required files => `TRAINING_BLOCKED_INTEGRITY`. Do not substitute another version.
4. Load `SOURCE_BASELINE.md` as frozen design provenance, not current operational state.
5. Execute Modules 01-08 exactly in manifest order. Each requires a demonstrated exercise, not acknowledgement.
6. If a material module criterion is unresolved, record `MODULE_<NN>_UNRESOLVED`; unresolved is not pass.
7. After Modules 01-08 pass, load and answer `qualification/09-final-qualification.md`.
8. Do not load `qualification/09-rubric.md` until the Module 09 answer is complete.
9. Apply the rubric. Outcomes are `QUALIFICATION_PASS`, `QUALIFICATION_FAIL`, or `QUALIFICATION_UNRESOLVED`.
10. Mark `BASE_READY` only if the manifest's full BASE_READY gate is satisfied.
11. Freeze the qualified chat before loading mutable operational state.
12. Begin work only in a fresh branch/chat by loading the latest verified operational checkpoint/currentness state.

## Separation

**Training source:** versioned repository files. Semantic changes require a new version.

**Frozen base:** a fresh chat that passed this exact training version. It proves trained competence for that package version only.

**Operational state:** mutable assignments, leases, provider/target currentness, branch heads/SHAs, blockers, review waves, ledger high-water, and checkpoints loaded after branching from the base.

Neither base nor checkpoint proves uninterrupted runtime, subjective continuity, private persistent state, or personhood.
