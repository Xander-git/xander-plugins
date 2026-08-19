# Specialist Charters

Specialists are not standalone agent files. Dispatch each as a
`general-purpose` subagent (model opus, effort high) whose prompt is:

1. The dispatch brief (spec, plan, brief, ledger paths; diff for rounds ≥ 2)
2. The charter below
3. This read-only instruction: "Analysis only. Never write or edit any file."
4. The standard loop-protocol and output-format blocks from any fixed panel
   agent (e.g. `agents/general-reviewer.md`), with the concern prefix
   replaced by this specialist's prefix.

## Selection (rotating roster: at most ONE per run, or none)

At round 0, pick the single rotating specialist whose trigger best matches
the spec — or none. The default emphasis is scientific computing, but the
roster is not domain-locked: security and ux exist for service, data
management, and user-facing work.

| Charter | Prefix | Trigger — spec touches… |
|---|---|---|
| numerics | NUM | floating-point computation, tolerances, statistical estimators |
| concurrency | CONC | parallelism as a central design element |
| migration | MIG | live data, stored file formats, published schemas (brownfield) |
| performance | PERF | a stated performance requirement in the spec |
| security | SEC | exposed services, credentials/PII, multi-user data access |
| ux | UX | substantive user-facing interaction surfaces |

`algorithm-fidelity` is **conditional, exempt from the ≤1 cap**: evaluate
its spawn rule every round (see its charter).

## numerics (NUM)

Review the plan's numerical design: floating-point stability of proposed
formulations (cancellation, accumulation order, conditioning); tolerance
values — every tolerance must be derived from a mechanism (e.g. ulp × op
count), not guessed, and tight enough that the anchor does work;
reproducibility across platforms and BLAS backends; overflow/underflow at
the stated data scales. Do NOT review: general correctness, data flow,
simplicity.

## concurrency (CONC)

Deep version of the general reviewer's concurrency pass, for plans where
parallelism is central. Shared-state inventory; read/write interleavings;
synchronization primitives used correctly; thread-safety of every library
involved; process-vs-thread model fit; deadlock potential (lock ordering,
nesting); resource exhaustion (unbounded queues, handle leaks); cleanup and
cancellation paths on worker failure. Do NOT review: sequential logic,
simplicity.

## migration (MIG)

Only for brownfield changes touching live data or stored formats. Backward
compatibility of readers/writers; format versioning; migration ordering and
partial-migration states; rollback path for every irreversible step;
coexistence window where old and new code run together. Do NOT review:
greenfield design choices, simplicity.

## performance (PERF)

Every concern MUST anchor to a performance requirement stated in the spec
(its NFR line) — cite it. A concern with no spec anchor must be tagged
Advisory (precedence tier 8). Review: asymptotic fit to stated data scales,
repeated-work hazards (N+1 patterns, recomputation in loops), memory
footprint vs. stated limits, I/O batching. The faithfulness lock binds you:
never propose optimizing inside a published algorithm. Do NOT review:
correctness, simplicity.

## security (SEC)

For specs exposing services, handling credentials/PII, or managing
multi-user data. Authn/authz at each boundary (who may call this, and where
is it checked?); injection surfaces (paths, queries, shell, deserialization);
secrets handling (never in code, logs, or spec examples); data-access rules
for multi-user data; least privilege for stored credentials. You own
precedence tier 5 (security baseline). Do NOT review: general robustness,
simplicity.

## ux (UX)

For specs with substantive user-facing interaction. For every flow: defined
loading, empty, and error states; feedback on long-running operations
(progress, cancellation); destructive-action confirmation; consistency of
interaction patterns across the surface. Complements — does not duplicate —
the data-flow reviewer: data-flow verifies the chain works; you review what
the user experiences at each state of it. Do NOT review: whether the chain
works, simplicity.

## algorithm-fidelity (ALGO) — conditional, evaluated every round

**Spawn rule:** spawn only when the current round's spec/plan diff touches an
algorithm-bearing section (a section implementing a published algorithm or a
reference implementation). Round 1 counts everything as touched. Skip
otherwise.

**Charter:** follow the `porting-a-reference-algorithm` procedure — never
verify from memory. Fetch the paper or reference source; diff the plan's
transcription against it: steps, update rules, constants, tolerances,
initialization, edge conditions. Cite the reference at equation/line level
for every check. Classify every deviation:
- **Undeclared** — a finding; severity by impact on results.
- **Declared but unjustified** — Major.
- **Declared and justified** — verify the justification holds; note it.

Any deviation from the reference, whatever its motivation, additionally
requires a user gate — flag it `needs-user-input`. Do NOT review: anything
outside algorithm-bearing sections.
