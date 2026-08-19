# plan-refinery — Design Spec

**Date:** 2026-08-18
**Status:** Approved design, pre-implementation
**Home:** `plugins/plan-refinery/` in the `xander-plugins` marketplace

## Objective & Non-goals

**Objective:** A plugin that runs a design spec + implementation plan through a
panel of reviewer subagents in a convergence loop — dispatch reviewers, collect
severity-tagged concerns, fix the plan, repeat — until no reviewer raises a
blocking concern or a round cap is hit. Optimized for scientific computational
tools, and for token economy: shared discovery, diff-scoped re-review, and
evidence-based conflict resolution instead of reviewer tug-of-wars.

**Non-goals:**
- Implementation execution — that remains `execute-plan-orchestration`'s job.
  plan-refinery ends when the plan is approved; it never dispatches implementers.
- Autonomous spec editing — the spec is a contract with the user; the loop may
  challenge it but never amends it without the user's ruling.
- Code review of finished work (`implementation-test-reviewer` covers that).
- Replacing `superpowers:writing-plans` — plan-refinery consumes a drafted
  spec + plan; it does not draft them.

## Plugin layout

```
plugins/plan-refinery/
├── .claude-plugin/plugin.json     # marketplace manifest (match existing plugins)
├── LICENSE
├── README.md
├── agents/
│   ├── general-reviewer.md        # fidelity + feasibility + failure-mode
│   ├── data-flow-reviewer.md      # end-to-end flow traces
│   └── simplicity-reviewer.md     # YAGNI counterweight
└── skills/plan-refinery/
    ├── SKILL.md                   # the goal-loop protocol (orchestrator-facing)
    └── references/
        └── specialists.md         # rotating + conditional specialist charters
```

Also: register the plugin in the root `.claude-plugin/marketplace.json`.

## Reviewer panel

All reviewers are **read-only on spec and plan** (`disallowedTools: Write, Edit,
NotebookEdit`), model `opus`, and end their report with a machine-readable
verdict (see Loop protocol). Each charter contains an explicit **"You do NOT
review"** list so mandates stay disjoint. Reports are **terse**: the concern
list and verdict ARE the report — a few lines of context at most, no narrative
analysis sections (Opus output is the loop's second-largest cost).

### 1. general-reviewer (fixed; effort: high)

The merged workhorse. Extends the methodology of
`execute-plan-orchestration/agents/plan-reviewer.md` (project-conventions
context step, logic/API validation, doc verification, concurrency analysis,
edge cases) with a **traceability phase**. Deliberate deviation from the
plan-reviewer template: its *necessity challenge* is delegated to the
simplicity-reviewer to keep panel mandates disjoint:

- **Spec → plan:** every spec requirement maps to a plan task; unmapped
  requirements are gaps (Critical or Major).
- **Plan → spec:** every plan task maps to a requirement; unmapped tasks are
  scope creep (reported, resolution deferred to simplicity precedence rules).
- **Contradiction scan:** spec vs. plan disagreements, and requirements
  ambiguous enough that two implementers would build different things.
- **Failure-mode analysis:** for each operation — empty/malformed input,
  partial failure, double-invocation, interruption mid-write, concurrent
  access. Idempotency, transaction boundaries, defined outcome for every
  error path.

Does NOT review: cross-boundary data-flow traces (data-flow-reviewer owns
those), or opportunities to simplify (simplicity-reviewer owns those).

### 2. data-flow-reviewer (fixed; effort: high)

Traces every user-facing flow in the spec end-to-end. Written
**stack-agnostically** for scientific tools: entry point (CLI arg, API call, UI
event, config file) → parsing/validation → state → computation/pipeline stages
→ persistence/output → result surfaced back to the user. Hunts **broken
chains**:

- Inputs collected that nothing consumes; outputs computed that nothing persists
  or surfaces.
- Schema/type/unit mismatches at each boundary (producer and consumer must
  agree; a hand-waved contract — "returns the results" — is itself a finding).
- Errors raised in one layer with no defined handling or user-visible outcome
  in the layers above.
- Stale-state hazards: cached/derived values with no defined invalidation when
  upstream data changes.

Output includes a per-flow trace table with each boundary and its
verified/gap/mismatch status. This reviewer earns the deep codebase reads; it
is the only panel member expected to traverse source beyond spot-checks.

Does NOT review: spec coverage, within-component algorithm logic, or
simplification.

### 3. simplicity-reviewer (fixed; effort: high, low turn cap)

The counterweight that prunes instead of adds. **Deliberately cheap:** reads
only the spec, the plan, the context brief, and the ledger — no codebase
traversal (its question, "what can be removed while still satisfying the
spec?", is answerable from the documents).

- Challenges plan-level complexity: unnecessary abstraction, speculative
  generality, components redundant with existing functionality named in the
  context brief.
- **May challenge the spec itself**, measured against the spec's Objective &
  Non-goals section. Spec challenges are never auto-applied (see Gating).
- **Faithfulness lock:** clearly outlined published algorithms are off-limits
  for "improvement" — faithfulness to the reference beats optimization or
  elegance. It may challenge *whether* an algorithm-bearing feature belongs in
  scope (gated spec challenge), never *how* the algorithm works.
- Must read the ledger before flagging: provenance-locked additions (see
  Conflict resolution) are raised as reviewer conflicts, not fresh concerns;
  user-settled items are never re-raised absent new evidence.

Does NOT review: correctness, feasibility, or data flow.

### Rotating specialists (`references/specialists.md`)

The orchestrator picks **at most one per run** at loop start, based on what the
spec touches — or none. The roster's default emphasis is scientific computing,
but it is not domain-locked — the user also builds UX-facing and data
management systems, and the security and UX charters exist for those runs:

- **numerics** — floating-point stability, tolerance derivation (mechanism-based
  per the user's test-integrity rules), conditioning, accumulation error,
  reproducibility across platforms/BLAS backends.
- **concurrency** — deep version of the general reviewer's concurrency pass for
  plans where parallelism is central.
- **migration** — only for brownfield changes touching live data/file formats:
  compat, versioned formats, rollback.
- **performance** — profiling-informed concerns only; every concern must anchor
  to a spec-stated performance requirement or be tagged advisory (precedence
  tier 8).
- **security** — for specs exposing services, handling credentials/PII, or
  managing multi-user data: authn/authz at each boundary, injection surfaces,
  secrets handling, data-access rules. Owns precedence tier 5.
- **ux** — for specs with substantive user-facing interaction: loading/empty/
  error states for every flow, feedback on long-running operations,
  destructive-action confirmation, consistency of interaction patterns.
  Complements (not duplicates) the data-flow reviewer: data-flow verifies the
  chain works; ux reviews what the user experiences at each state of it.

### algorithm-fidelity specialist (conditional; exempt from the ≤1 cap)

For specs implementing published algorithms or reference implementations.
**Spawn rule:** evaluated **per round** — spawned only when the current round's
spec/plan diff touches an algorithm-bearing section; skipped otherwise (round 1
counts everything as touched).

Charter: follow the `porting-a-reference-algorithm` procedure — fetch the paper
or reference source, diff the plan's transcription against it (steps, update
rules, constants, tolerances, edge conditions) with file:line/equation-level
citations; never verify from memory. Every deviation is either **undeclared**
(a finding, severity by impact) or **declared-but-unjustified** (Major).

## Loop protocol (SKILL.md)

### Round 0 — setup
1. Verify the spec has an **Objective & Non-goals** section and a
   **performance/NFR line** (even "no performance requirements"). Missing →
   stop and ask the user to supply them; they are the anchors for gating and
   precedence.
2. A scout pass produces a **context brief** file (architecture map, key file
   paths, existing contracts, conventions, test setup) saved alongside the
   spec. Every reviewer is instructed: *start from the brief; open source files
   only to verify a specific claim, never to explore.* Discovery is paid once.
3. Orchestrator selects the rotating specialist (≤1 or none) and initializes an
   empty **ledger** file.

### Each round
1. Evaluate the algorithm-fidelity spawn rule against this round's diff.
2. Dispatch the due reviewers **in parallel** — round 1: the full panel;
   rounds ≥2: per the cadence rules (see Round economics) — each briefed with:
   spec path, plan path, brief path, ledger path, and (rounds ≥2) the
   spec/plan diff since their last review.
3. Each reviewer returns a report ending with:
   - `VERDICT: APPROVE | REVISE`
   - Concerns, each with a **stable ID** (`GEN-3`, `FLOW-1`, …), severity
     (`Critical | Major | Minor | Advisory`), description, and suggested
     direction (not a rewrite).
4. Orchestrator merges concerns into the ledger, **dedupes** cross-reviewer
   duplicates (one canonical entry, aliases recorded), and resolves conflicts
   (below).
5. Orchestrator applies **plan** fixes; every applied change gets a ledger
   entry naming the concern ID that motivated it (**provenance lock**).
6. **Spec challenges pause the loop immediately** and go to the user (see
   Gating) before the next round dispatches.

### Rounds ≥2 — diff-scoping and ratchet
- Reviewers verify their prior concerns' resolutions and scan the diff; they do
  **not** re-review unchanged sections.
- Diffs are computed from per-round snapshots of the spec and plan that the
  orchestrator saves alongside the ledger (no reliance on git state).
- **Severity ratchet:** after round 2, new sub-Critical concerns may not be
  raised. The orchestrator may downgrade implausible severities; a downgraded
  late concern becomes Advisory.

### Round economics (rounds ≥2)

Round 1 is discovery and gets the full panel; later rounds are mostly
verification, which is cheaper work. Two mechanisms exploit that asymmetry:

- **Cadence scheduling.** Only reviewers whose lane the round's diff touches
  are dispatched: `general-reviewer` every round (it owns correctness);
  `data-flow-reviewer` when the diff touches a boundary, contract, or flow;
  `simplicity-reviewer` when the diff is net-additive beyond a trivial
  threshold (it audits additions); the rotating specialist when the diff
  touches its domain; algorithm-fidelity per its existing spawn rule. Lane
  assignment is the orchestrator's judgment call from the diff.
- **Resolution verifier.** A mid-tier (Sonnet-class) agent checks every
  `resolved` ledger entry against the diff: was the fix applied, and does it
  address the concern as written. It never reviews new content — that is
  lane work. Anything ambiguous, contested, or suspicious escalates to the
  owning Opus reviewer, re-dispatched narrowly; escalate on any doubt. This
  is mechanical diffing of ledger claims against text, so the
  never-verify-with-a-weaker-model rule is respected via the escalation path.
- **Full-panel sign-off.** Convergence is only declared after a final round
  in which every panel member (verification- and diff-scoped) returns
  APPROVE on the final plan state — the backstop for cadence misjudgments.
  The simplicity reviewer stays Opus regardless: it is the counterweight in
  precedence fights and must not argue from a weaker model.

### Exit conditions
- **Converged:** all reviewers return `APPROVE` (no open Critical/Major) in a
  final full-panel sign-off round on the final plan state (see Round
  economics). Advisory/Minor items are listed in the final summary, not
  loop-extending.
- **Round cap** (default 4): remaining open concerns are surfaced to the user
  with the orchestrator's recommendation, instead of looping further.
- **User-input short-circuit:** any concern flagged `needs-user-input`
  surfaces immediately rather than burning rounds.
- On exit, hand off: converged plans proceed to `execute-plan-orchestration`.

## Spec-change gating

- The orchestrator auto-applies **plan** changes only. **All spec changes** —
  from any reviewer, however peripheral — are gated to the user.
- A spec challenge **pauses the loop immediately**; the user's ruling is
  recorded in the ledger; the next round reviews the (possibly amended) spec.
- User rulings are permanent: a rejected challenge is never re-raised absent
  new evidence, by any reviewer.

## Conflict resolution — no tug-of-wars

Identified conflict axes: robustness vs. simplicity (also security/migration
vs. simplicity), performance vs. algorithm faithfulness, failure-guards vs.
algorithm faithfulness, and re-litigation of user rulings. Resolved by:

### Provenance locks
Every applied plan change is ledger-tagged with its motivating concern ID.
Challenging a provenance-locked item is a **reviewer conflict**, not a normal
concern — the orchestrator resolves it directly instead of applying-then-
reverting across rounds.

### Precedence table
Reviewer conflicts resolve by the highest applicable tier:

1. User's explicit rulings
2. Spec requirements (incl. Objective & Non-goals)
3. Correctness / data integrity
4. Faithfulness to published references
5. Security baseline
6. Simplicity
7. Robustness beyond plausible failures
8. Performance without a spec-stated requirement

### Evidence before escalation
When the table does not decide, the orchestrator settles the conflict
**empirically before asking the user**: a small self-contained experiment
(e.g., does this failure mode actually occur? is this guard load-bearing?) or
a check against authoritative docs/reference source. Most robustness-vs-
simplicity disputes in scientific code are testable claims. Only genuinely
underdetermined conflicts reach the user as a tie-breaker, presented with both
positions and the evidence gathered.

### Faithfulness lock (global)
Published-algorithm sections are locked for **all** reviewers. Any deviation —
for performance, robustness, or style — requires a declared-and-justified
deviation note (per `porting-a-reference-algorithm`) **and** a user gate.
Guards and validation belong at the algorithm's boundary (inputs checked
before, outputs after), never inside the transcription.

### Ask, don't infer (global orchestrator rule)
A concern that needs user input — ambiguous requirement, judgment call the
precedence table and evidence can't settle, anything touching the spec — is
raised for discussion, never inferred over. For scientific tools a wrong
inference silently corrupts results; a question costs a round-trip.

## Error handling of the loop itself
- A reviewer that fails/returns garbage: re-dispatch once; on second failure,
  proceed without it and note the coverage gap in the final summary (never
  silently treat a dead reviewer as APPROVE).
- Ledger and brief are plain markdown files next to the spec — inspectable and
  survivable across sessions.

## Testing
Dogfood: run plan-refinery on a real spec + plan for one of the user's
scientific projects; verify (a) round-2 token spend is materially below
round 1 (diff-scoping works), (b) an injected spec-violating plan task is
caught (fidelity), (c) an injected broken chain is caught (data-flow), (d) a
seeded reviewer conflict resolves via evidence without a user gate, and (e) a
seeded published-algorithm "optimization" is blocked by the faithfulness lock.
