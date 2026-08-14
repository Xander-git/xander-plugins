# execute-plan-orchestration

Right-size subagent work by task *shape*, not count.

Two failure modes bracket subagent orchestration: one-agent-per-micro-task (dispatch
overhead, repeated context loads, inconsistent seams) and one-mega-agent
(unreviewable diffs, bisect-hostile, silently incomplete sweeps). This skill is the
middle path — cluster the cohesive interdependent work, isolate the broad mechanical
sweeps and the risky wiring points.

## What it gives you

- A **procedure**: dependency DAG → task shape tags → clusters → model/effort
  assignment → gates → dispatch order.
- Four **task shapes** (Keystone, Sweep, Seam, Leaf) with a rule for each.
- A **cluster rule** that says exactly when to split.
- **Model + reasoning-effort** selection per cluster, with current tier IDs kept in
  [`references/models.md`](skills/execute-plan-orchestration/references/models.md)
  so the procedure itself doesn't rot.
- **Gate placement** — before dispatch, per cluster, per phase, and one end-of-work
  simplify pass.

## Agents

The skill's gates call for review agents; this plugin ships the two that staff them.

| Agent | Role |
|---|---|
| `plan-reviewer` | Reviews a plan *before* dispatch — feasibility, API claims verified against real source, race-condition analysis, and a challenge to any unnecessary complexity. Analysis only; it never edits the plan. |
| `implementation-test-reviewer` | Reviews a finished phase — implementation defects plus whether the tests genuinely prove correctness, hunting false greens, silent skips, and assertions too permissive to fail. |

Both read the project's own convention files (`CLAUDE.md`, `AGENTS.md`, packaging
manifest) first and review against those rules rather than against generic defaults.

## When it triggers

After writing a plan and before dispatching subagents, or any time the question is
"how do I parallelize / batch / staff this?".

## Install

```
/plugin marketplace add Xander-git/xander-plugins
/plugin install execute-plan-orchestration@xander-plugins
```
