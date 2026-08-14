---
name: execute-plan-orchestration
description: Use when planning subagent execution of a multi-task implementation plan — deciding how many subagents to dispatch, how to group tasks, which model each gets, and where review gates go. Turns a task list + dependency DAG into clusters sized for one agent each. Trigger after writing-plans, before dispatching subagents, or whenever asked how to parallelize, batch, or staff agent work.
---

# Cluster-and-Isolate Subagent Orchestration

Right-size subagent work by task *shape*, not count. Avoid two failure modes:
one-agent-per-micro-task (dispatch overhead, repeated context loads, inconsistent
seams) and one-mega-agent (unreviewable diffs, bisect-hostile, silently incomplete
sweeps). The middle path: cluster the cohesive interdependent work, isolate the
broad mechanical sweeps and the risky wiring points.

## Procedure

1. **Build the dependency DAG** from the plan's per-task `Files`/`Interfaces`
   blocks (→ = must-finish-before; record shared files). Record it in the plan's
   execution section — it's a derived, version-controlled view, not a separate tool.
2. **Tag each task** Keystone / Sweep / Seam / Leaf (see Shapes).
3. **Form clusters:** merge adjacent Keystones + their Leaves that share files or
   intent; keep each Sweep alone (sub-batch by subsystem if > one reviewable diff);
   keep each Seam alone.
4. **Validate each cluster** against the cluster rule (below). Split when it breaks.
5. **Assign model + reasoning effort** per cluster (see Model selection).
6. **Place gates** (see Gates).
7. **Mark zero-file-overlap clusters** as parallel-worktree candidates; everything
   else runs sequentially.
8. **Dispatch one agent per cluster;** clear the gate before the next.

## Shapes

- **Keystone** — novel, interdependent core logic over shared files/state → cluster together.
- **Sweep** — broad, shallow, mechanical across many files → isolate; sub-batch by subsystem if large.
- **Seam** — one risky integration/wiring point → isolate for a focused gate, even if small.
- **Leaf** — tiny, independent → fold into the nearest cluster.

## Cluster rule

A cluster is the **largest** task set that (1) shares context/intent, (2) is one
reviewable diff, and (3) one agent can finish AND self-verify in a single pass
without risking incomplete coverage. Split the moment (2) or (3) breaks.

## Model selection

Match model tier AND reasoning effort to whether the task needs *judgment* or
*careful application*:

- Keystone, Seam, and every review/verify/simplify gate → frontier model
  (Opus-tier), high effort.
- Sweep, Leaf → mid-tier model (Sonnet-tier), medium effort. Keep
  consistency-critical sweeps on the frontier model, or add a frontier verify pass.
- Default to the session model; deviate deliberately.
- **Never review or verify with a weaker model than implemented.**

See [references/models.md](references/models.md) for current tier IDs.

## Gates

- **Before dispatch:** run `plan-reviewer` over the plan itself — feasibility,
  API claims, race conditions, unnecessary complexity. Resolve its critical
  issues before clustering work you may have to throw away.
- **Per cluster (light):** review the diff + run tests/lint before the next cluster. Pause and surface any design conflicting open questions from the review that needs user input before proceeding to the next phase.
- **Per multi-task phase (deep):** dispatch a fresh code-review agent over the
  phase's combined diff (frontier model); triage and fix high-signal findings
  before proceeding. `implementation-test-reviewer` is the one to use when the
  phase added tests — it checks that they can actually fail, not just that they pass.
- **End (simplify):** one simplify pass (dedupe, reduce, clarify — quality only, no
  behavior change), apply fixes, then run the regression suite for affected areas.

## Heuristics

- Risk ≠ size: isolate risky seams even when tiny.
- Breadth needs a *bounded* agent, not a bigger one.
- Overlap kills parallelism — check shared files before fanning out.
- Breaking rename → decouple-then-flip (route through indirection first; flip the
  definition last, so each step stays green).

## Anti-patterns

- One agent per checkbox (overhead, drift).
- One agent for a whole phase (incomplete sweeps, unreviewable).
- Parallelizing clusters that touch the same files.
- Reviewing with a model weaker than the implementer.
