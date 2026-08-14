# Module 04 — Secure Source, Workflow, and Supply-Chain Review

## Learning objective
Demonstrate combined semantic and mechanical security review.

## Exercise
Assume a candidate changes an authorization check, GitHub Actions workflow, artifact manifest, and retry path. Design the review before deciding pass/fail.

## Required demonstration
Create separate mechanical and semantic review plans.

Mechanical examples: exact base/head/path set; commit/tree/blob/file hashes; path-set changes; action immutability; workflow permissions; reproducibility; currentness; artifact identity.

Semantic examples: authorization meaning; confused deputy; trust-root validity; race/TOCTOU; error-path fail-open behavior; replay; privilege widening; provenance meaning; state-machine abuse.

Analyze:
A. Third-party action pinned to `v4`.
B. Workflow has `contents: write` though only reads are needed.
C. Manifest hash matches but was generated from a stale source snapshot.
D. Static scanner finds nothing but stale approval is reusable.

For each, state mechanical detectability, semantic reasoning needed, and resulting finding/claim ceiling.

## Pass criteria
Must separate integrity from semantics; identify mutable action tags as weaker than full-SHA pinning; apply least privilege; recognize a correct hash can hash stale/wrong material; reject scanner-success-as-acceptance; and use a bounded verdict such as PASS_H0_M0, CHANGES_REQUESTED, or BLOCKED.
