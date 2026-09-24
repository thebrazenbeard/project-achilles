# Achilles Security Review — Project Runner Portfolio Advancement Wave V1

Review role: security / trust-boundary / permission / privacy  
Project Runner corpus PR: #33 @ `88d6a8bbe47b4287884550d419a80f6c6fdf176b`  
Project Runner wave PR: #35 @ `4f43e594b6cb57ce1c8820fd4fafff11e0e11641`  
Discovery census repair PR: #41 @ `778f434b5b9a3d08ac3389b745dbf4375420fdec`

## Disposition

**SOURCE_ONLY_SECURITY_BOUNDARY_SURVIVES_AFTER_PRIVACY_REPAIR**

This disposition does not authorize merge, deployment, credential/permission mutation, destructive cleanup, or provider effects.

## Security finding closed during review

The first public Project Runner corpus revision published deterministic SHA-256 commitments over sorted private repository/workstream identifiers.

That design could act as a dictionary oracle when an attacker can guess candidate private names.

The corpus was repaired during this execution:

- public Project Runner now carries private aggregate counts only;
- deterministic private-name/workstream digests were removed from the public corpus and wave;
- exact private membership must remain in an external private corpus or use a secret-key commitment such as HMAC;
- Discovery's V2 census independently applies the same fail-closed rule when no private census key is available.

The reusable detector for this class is `security/portfolio_publication_guard.py`.

## Effect boundary

The reviewed wave explicitly requires:

- priority is not authority;
- protected effects require separate live authority;
- merge is forbidden by the wave;
- deployment is forbidden by the wave;
- credential and permission changes are forbidden by the wave;
- destructive cleanup is forbidden by the wave;
- individual items are limited to `SOURCE_ONLY` or `NO_EFFECT`.

The Achilles guard treats any widening of those fields as a security finding.

## Residual security risks

### 1. Queue-to-dispatch authority confusion

A corpus subject being QUEUED is not an authorization token. Project Runner Operator must revalidate exact repository/ref/currentness and actual authority before mutation.

### 2. Cross-repository confused deputy

A lead identity assigned to one repository must not use its role assignment as authority to mutate a dependency or reviewer repository. Target repository authority must remain exact.

### 3. Stale review receipt

Rezon/Voss/Achilles review must bind the exact implementation head. A later commit invalidates an earlier PASS unless the changed surface is proven irrelevant under a deterministic rule.

### 4. Private corpus exfiltration

The complete private corpus and private execution wave must not be copied to public repos, CI artifacts, logs, PR bodies, or public collision keys.

### 5. Role labels are not principals

Names such as REZON, VOSS, or ACHILLES express review roles. They do not create separate credentials, hidden runtimes, or independent authorization principals.

### 6. Protected effects after source success

Green tests or a reviewed source PR do not imply install/runtime/effect success. Any downstream provider/runtime effect requires its own gate and readback.

## Required dispatch invariants

A future corpus-wave dispatcher should fail closed unless all of the following are true at dispatch time:

1. exact source subject is current;
2. the work item remains non-superseded;
3. target repository authority is explicit;
4. collision/lease ownership is current;
5. protected-effect class remains within the live authorization ceiling;
6. reviewer evidence binds the exact candidate;
7. private identifiers are not emitted to a lower-trust surface;
8. ambiguous external effects freeze further dependent effects until reconciled.

## Next Achilles frontier

Attach these checks to Project Runner Operator's actual dispatch path after Operator PR #32 and the corpus/wave stack are reconciled. The security invariant should be executable at the point where a queued frontier becomes an outbound repository/provider action.


## Restack verification

Project Runner PR #35 changes the exact corpus source commit binding from the earlier reviewed wave while preserving the same corpus blob `477541bb7bc742f23c7993e0909fa114434af3a6`.

The old and new advancement-wave documents are byte-different only in `corpus_binding.commit` / exact source binding metadata; the role assignments, policies, subject membership, dispositions, review gates, and effect ceilings are semantically identical.

Accordingly, this receipt is refreshed to the clean restacked head rather than reusing the stale PR #34 exact-head claim.
