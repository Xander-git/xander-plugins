---
name: plan-refinery
description: Use when a design spec and implementation plan are drafted and should be iterated to convergence before execution — dispatches a reviewer panel (general, data-flow, simplicity, plus specialists) in a loop, merges severity-tagged concerns into a provenance-locked ledger, applies plan fixes, gates all spec changes to the user, and exits when no reviewer raises a blocking concern. Trigger on "refine this plan", "review loop", "run the plan through the refinery", or after writing-plans and before execute-plan-orchestration.
---

# plan-refinery — Reviewer-Panel Convergence Loop

Iterate a spec + plan until the panel stops raising blocking concerns.
You (the orchestrating session) dispatch reviewers, merge their concerns,
fix the plan, and gate spec questions to the user. Reviewers never edit
anything; you never edit the spec.

**Global rule — ask, don't infer:** a concern that needs user input
(ambiguous requirement, judgment call evidence can't settle, anything
touching the spec) is raised for discussion, never inferred over. A wrong
inference silently corrupts results; a question costs a round-trip.

## Working files

Create `<spec-dir>/refinery/` next to the spec:

- `brief.md` — context brief (round 0)
- `ledger.md` — the concern ledger (append-only entries, updated statuses)
- `snapshots/round-<n>-spec.md`, `snapshots/round-<n>-plan.md` — copies
  saved at the END of each round; diffs between snapshots drive diff-scoped
  review (no reliance on git state)

## Round 0 — setup

1. **Check spec anchors.** The spec MUST contain an **Objective & Non-goals**
   section and a **performance/NFR line** (even "no performance
   requirements"). Missing → stop and ask the user to supply them. They
   anchor spec gating and the precedence table.
2. **Scout the codebase** (yourself or one Explore agent) and write
   `brief.md`: architecture map, key file paths, existing contracts and
   conventions, test setup. Reviewers start from the brief and open source
   only to verify specific claims — discovery is paid once, here.
3. **Select the rotating specialist** — at most one, or none — per the
   selection table in [references/specialists.md](references/specialists.md).
4. **Initialize** an empty `ledger.md` and save `snapshots/round-0-*.md`.

## Each round

1. **Evaluate the algorithm-fidelity spawn rule** against this round's diff
   (round 1: everything counts as touched) — see specialists.md.
2. **Dispatch the panel in parallel**: `general-reviewer`,
   `data-flow-reviewer`, `simplicity-reviewer`, plus the selected specialist
   and (if spawned) algorithm-fidelity. Each brief contains: spec path, plan
   path, brief path, ledger path, and for rounds ≥ 2 the diff of spec and
   plan since that reviewer's last round (computed from snapshots).
3. **Collect reports.** Each ends with severity-tagged concerns bearing
   stable IDs and `VERDICT: APPROVE` or `VERDICT: REVISE`.
4. **Merge into the ledger.** Dedupe cross-reviewer duplicates: keep one
   canonical entry, record the others as aliases. Ledger entry format:

   ```markdown
   ### GEN-3 [Critical] [open]
   - Raised: round 1, general-reviewer
   - Aliases: FLOW-2
   - Concern: <one-paragraph description>
   - Resolution: —
   ```

   Statuses: `open` → `resolved (round N: <what changed>)` |
   `settled-by-user (round N: <ruling>)` | `conflict (vs <ID>)` |
   `advisory`. A resolution entry that changed the plan IS the provenance
   lock — it names what was added and why.
5. **Resolve conflicts** (see Conflict resolution) BEFORE editing.
6. **Apply plan fixes.** You edit the plan; reviewers never do. Every
   applied change updates its concern's ledger entry (provenance lock).
   Severity may be downgraded when implausible — a downgraded concern raised
   after round 2 becomes `advisory`.
7. **Gate spec changes.** Any `spec-change` concern PAUSES the loop
   immediately: present it to the user, record the ruling as
   `settled-by-user`, amend the spec only per the ruling. User rulings are
   permanent — no reviewer may re-raise absent new evidence.
8. **Save snapshots** and check exit conditions; otherwise next round.

## Diff-scoping and the severity ratchet (rounds ≥ 2)

- Reviewers verify their prior concerns' resolutions and scan the diff only;
  unchanged sections are not re-reviewed. This is where the loop's token
  cost is controlled — keep diffs honest and snapshots exact.
- After round 2, reviewers may not raise new sub-Critical concerns.

## Conflict resolution — no tug-of-wars

A reviewer flagging `CONFLICT with <ID>` (challenging a provenance-locked
change) triggers this ladder. Never apply-then-revert across rounds.

**1. Precedence table** — highest applicable tier wins:

1. User's explicit rulings
2. Spec requirements (incl. Objective & Non-goals)
3. Correctness / data integrity
4. Faithfulness to published references
5. Security baseline
6. Simplicity
7. Robustness beyond plausible failures
8. Performance without a spec-stated requirement

**2. Evidence** — if the table does not decide, settle empirically BEFORE
asking the user: a small self-contained experiment (does this failure mode
actually occur? is this guard load-bearing?) or a check against
authoritative docs/reference source. Most robustness-vs-simplicity disputes
are testable claims.

**3. User tie-breaker** — only genuinely underdetermined conflicts reach the
user, presented with both positions and the evidence gathered.

**Faithfulness lock (binds every reviewer and you):** published-algorithm
sections change only for faithfulness. Any deviation from the reference —
for performance, robustness, or style — requires a declared-and-justified
deviation note (per `porting-a-reference-algorithm`) AND a user gate.
Guards go at the algorithm's boundary, never inside the transcription.

## Exit conditions

- **Converged:** every reviewer returned `VERDICT: APPROVE` (no open
  Critical/Major). List remaining Minor/Advisory items in the final summary;
  they never extend the loop.
- **Round cap** (default 4): surface remaining open concerns to the user
  with your recommendation instead of looping further.
- **User-input short-circuit:** `needs-user-input` concerns surface
  immediately — do not burn rounds around them.

On exit, hand off: a converged plan proceeds to `execute-plan-orchestration`.

## Reviewer failure

A reviewer that dies or returns an unparseable report: re-dispatch once; on
second failure, proceed without it and record the coverage gap in the final
summary. NEVER treat a dead reviewer as APPROVE.
