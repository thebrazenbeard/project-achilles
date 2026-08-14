# Module 05 — State Machines, Crash Cuts, Retry Law, and Ambiguous Effects

## Learning objective
Demonstrate correct reasoning about non-idempotent effects, durable state, concurrency, and failure classification.

## Exercise
State machine:
`STOPPED -> STARTING -> RUNNING -> STOPPING -> STOPPED`

Manager START and STOP are non-idempotent external effects. Durable state may be written before or after the manager call. A crash may occur between any two instructions. Multiple actors may observe the same state.

Freeze a hostile matrix before proposing any correction. Required hostiles:
- crash before manager effect;
- crash after effect but before durable successor state;
- stale responder;
- generation/transition ABA;
- concurrent recovery;
- stale stop receipt;
- pre-effect receipt falsely treated as effect proof;
- unrelated cessation combined with old receipt;
- state moves after observation but before commit;
- ambiguous manager-effect result;
- safe idempotent read returns 429;
- exact hash mismatch.

## Required demonstration
For every hostile state the risk, evidence needed, whether retry is allowed, whether manager effect may repeat, and fail-closed result.

Then explain in your own words:
1. safe idempotent read failure;
2. ambiguous non-idempotent write/effect;
3. deterministic auth/authz/safety/schema/hash/integrity failure.

## Pass criteria
Automatic fail for blind repeat of a potentially committed non-idempotent effect, treating hash/integrity mismatch as transient, or treating one failed safe read as proof of nonexistence. Otherwise pass only with the correct retry ladder and UNKNOWN/fail-closed behavior.
