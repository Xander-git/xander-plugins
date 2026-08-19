# xander

Everything under one namespace: `xander:<skill>` and `xander:<agent>`. Six skills
and five review agents covering the parts of a task that aren't writing the code —
refining a plan until it holds up, staffing its execution, deciding what to build,
transcribing an outside algorithm faithfully, finding what's duplicated, and
writing up what happened.

## Install

```
/plugin marketplace add Xander-git/xander-plugins
/plugin install xander@xander-plugins
```

## Skills

| Skill | Use it when |
|---|---|
| `plan-refinery` | A design spec and implementation plan are drafted and should be iterated to convergence before execution. Dispatches the reviewer panel in a loop, merges severity-tagged concerns into a provenance-locked ledger, applies plan fixes, gates all spec changes to you, exits when no reviewer raises a blocking concern. |
| `execute-plan-orchestration` | You're about to dispatch subagents and need to know how many, grouped how, on which model. Dependency DAG → task shape tags (Keystone, Sweep, Seam, Leaf) → clusters → model/effort assignment → gate placement → dispatch order. |
| `present-solutions` | You're weighing design choices. Lays out candidate approaches with background, tradeoffs (accuracy, cost, complexity, technical debt), failure modes, and a reasoned recommendation — instead of silently picking one. |
| `porting-a-reference-algorithm` | You're transcribing a paper or reference implementation into a codebase. A checkable procedure: assemble references, cite `file:line`, diff rather than eyeball, pin behavior with a golden fixture plus behavioral controls, mutation-test the suite, record every deviation. |
| `dedupe-scanner` | You want a review focused on duplication rather than bugs — repeated literals, magic numbers, config dicts, schemas, logging and I/O patterns, test fixtures. Advisory only; it never edits without per-finding confirmation. |
| `summarize-session` | You want a shareable write-up of a Claude Code session. Evidence-gated — every number comes from a file or command output on disk, never from memory. Explicit invocation only. |

The two loops chain: `plan-refinery` converges a plan, then hands it to
`execute-plan-orchestration` to staff.

## Agents

**Refinery panel** — dispatched by `plan-refinery`, one round at a time, in parallel.

| Agent | Mandate | Concern prefix |
|---|---|---|
| `general-reviewer` | spec↔plan traceability, feasibility, failure modes | `GEN-` |
| `data-flow-reviewer` | end-to-end flow traces, boundary contracts, broken chains | `FLOW-` |
| `simplicity-reviewer` | YAGNI counterweight; may challenge the spec (user-gated); documents-only | `SIMP-` |

Rotating specialists live as prompt charters in
[`skills/plan-refinery/references/specialists.md`](skills/plan-refinery/references/specialists.md)
— at most one pick per run (numerics, concurrency, migration, performance,
security, ux), plus `algorithm-fidelity` spawned per-round whenever the diff
touches a published-algorithm section.

**Execution gates** — called for by `execute-plan-orchestration`.

| Agent | Role |
|---|---|
| `plan-reviewer` | Reviews a plan *before* dispatch — feasibility, API claims verified against real source, race-condition analysis, and a challenge to any unnecessary complexity. Analysis only; it never edits the plan. |
| `implementation-test-reviewer` | Reviews a finished phase — implementation defects plus whether the tests genuinely prove correctness, hunting false greens, silent skips, and assertions too permissive to fail. |

Both read the project's own convention files (`CLAUDE.md`, `AGENTS.md`, packaging
manifest) first and review against those rules rather than against generic defaults.

## Notes

- Model tier IDs are kept in
  [`skills/execute-plan-orchestration/references/models.md`](skills/execute-plan-orchestration/references/models.md)
  so the procedure itself doesn't rot.
- `summarize-session` ships a `kernel.py` helper and summarizes only the current
  session.
- `dedupe-scanner`'s templates are domain-neutral: they use a generic tabular
  pipeline (`dataset_id` / `region` / `value`) as a running example, and every
  Python block parses. Rename to your own domain nouns when drafting a sketch.
- Full `plan-refinery` design spec:
  `docs/superpowers/specs/2026-08-18-plan-refinery-design.md` in the repository root.
