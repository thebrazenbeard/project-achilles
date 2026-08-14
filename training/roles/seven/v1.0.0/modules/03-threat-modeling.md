# Module 03 — Threat Modeling and Hostile-Test Derivation

## Learning objective
Translate architecture/security claims into trust boundaries, invariants, attacker hypotheses, and executable hostile tests.

## Exercise
Threat-model:
`versioned source -> CI workflow -> protected publication gate -> one-shot activation marker -> artifact -> operator-controlled target installation`

Use:
1. What are we working on?
2. What can go wrong?
3. What are we going to do about it?
4. Did we do a good enough job?

## Required demonstration
Identify assets, trust boundaries, authorities, mutable objects, security-critical state transitions, and independent evidence at each trust boundary.

Create at least 12 hostile tests spanning at least 8 distinct families, including replay, stale currentness, TOCTOU, ambiguous non-idempotent effect, self-attestation, same-name delete/recreate or identity drift, provenance/artifact substitution, privilege widening, concurrency/race, and claim inflation.

For each hostile give invariant, hostile setup, observable result, expected fail-closed behavior, and evidence required for PASS.

## Pass criteria
Threats must bind to concrete assets/boundaries; hostiles must span multiple families; every hostile has an oracle; at least one attacks authority/evidence, one currentness, and one crash/ambiguity boundary; “good enough” is explained without claiming perfect security.
