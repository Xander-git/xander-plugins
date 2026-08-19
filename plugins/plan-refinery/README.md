# plan-refinery

Iterate a design spec + implementation plan through a reviewer panel until
convergence — no reviewer raises a blocking concern, or a round cap is hit.

## What it ships

**Skill** — `plan-refinery`: the orchestrator loop. Context brief once,
panel dispatched in parallel each round, concerns merged into a
provenance-locked ledger, plan fixes applied by the orchestrator, all spec
changes gated to the user, diff-scoped rounds with a severity ratchet,
conflicts resolved by precedence table → evidence → user tie-breaker.

**Agents** — the fixed panel:

| Agent | Mandate | Prefix |
|---|---|---|
| `general-reviewer` | spec↔plan traceability, feasibility, failure modes | `GEN-` |
| `data-flow-reviewer` | end-to-end flow traces, boundary contracts, broken chains | `FLOW-` |
| `simplicity-reviewer` | YAGNI counterweight; may challenge the spec (user-gated); documents-only | `SIMP-` |

**Specialists** (`skills/plan-refinery/references/specialists.md`) — at most
one rotating pick per run: numerics, concurrency, migration, performance,
security, ux. Plus `algorithm-fidelity`, spawned per-round whenever the diff
touches a published-algorithm section (exempt from the cap).

## Usage

With a drafted spec (containing an **Objective & Non-goals** section and an
NFR line) and plan:

> Run the plan through the refinery: spec at docs/specs/foo-design.md, plan
> at docs/plans/foo.md

The loop exits converged (hand off to `execute-plan-orchestration`), at the
round cap (open concerns surfaced with a recommendation), or paused on a
question only you can answer — by design, concerns that need input are
raised for discussion, never inferred over.

## Install

```
/plugin marketplace add Xander-git/xander-plugins
/plugin install plan-refinery@xander-plugins
```

## Design

Full design spec: `docs/superpowers/specs/2026-08-18-plan-refinery-design.md`
in the repository root.
