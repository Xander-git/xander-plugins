# plan-refinery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `plan-refinery` plugin — three reviewer agents, a specialist-charter reference, and a goal-loop skill that iterates a design spec + implementation plan until the panel converges.

**Architecture:** A Claude Code marketplace plugin in `plugins/plan-refinery/`. Three fixed reviewer agents (`general-reviewer`, `data-flow-reviewer`, `simplicity-reviewer`) share a common loop protocol (stable concern IDs, severity tags, machine-readable verdicts, ledger discipline). Rotating/conditional specialists live as prompt charters in a skill reference, dispatched ad hoc. The `plan-refinery` skill defines the orchestrator loop: context brief, parallel dispatch, ledger merge, provenance locks, precedence table, evidence-based conflict resolution, user-gated spec changes, diff-scoped rounds, convergence/cap exit.

**Tech Stack:** Markdown agent definitions + SKILL.md (Claude Code plugin format), JSON manifests. No executable code.

**Spec:** `docs/superpowers/specs/2026-08-18-plan-refinery-design.md`

## Global Constraints

- Repo: `/Users/alex/MyProjects/xander-plugins`. All paths below are repo-relative.
- Reviewer agents are read-only on project files: frontmatter `disallowedTools: Write, Edit, NotebookEdit`; all are `model: opus`.
- Agent frontmatter format matches `plugins/execute-plan-orchestration/agents/plan-reviewer.md`: `name`, `description`, `model`, `effort`, `maxTurns`, optional `disallowedTools`.
- Concern ID prefixes are fixed API: `GEN-`, `FLOW-`, `SIMP-` (fixed panel); `NUM-`, `CONC-`, `MIG-`, `PERF-`, `SEC-`, `UX-`, `ALGO-` (specialists). Severities: `Critical | Major | Minor | Advisory`. Verdict line: `VERDICT: APPROVE` or `VERDICT: REVISE` (exact strings).
- Flags on concerns: `spec-change`, `needs-user-input`, `CONFLICT with <ID>` (exact strings).
- Refinery working files live next to the spec under `<spec-dir>/refinery/`: `brief.md`, `ledger.md`, `snapshots/round-<n>-{spec,plan}.md`.
- New plugin version `0.1.0`; bump root marketplace `version` from `0.1.1` to `0.2.0`.
- Validate with `claude plugin validate .` after every manifest change; if that command is unavailable in the environment, the `jq` checks in each task are the fallback.
- Commit after every task. Do not push.

## Shared Loop-Protocol Block

Every agent charter (Tasks 2–4) embeds this block verbatim, with `<PREFIX>` replaced by that agent's concern prefix. It is restated here once so implementers see the canonical text; each task's file content below already includes its substituted copy.

```markdown
## Loop protocol (read first)

You are one reviewer on a panel inside a convergence loop run by the
plan-refinery skill. Your dispatch brief gives you paths to: the spec, the
plan, the context brief, the concern ledger, and (rounds ≥ 2) a diff of the
spec and plan since your last review.

- **Start from the context brief.** Open source files only to verify a
  specific claim, never to explore. Discovery was paid once, by the scout.
- **Rounds ≥ 2:** verify the resolutions of your own prior concerns and scan
  the diff. Do NOT re-review unchanged sections. Do not raise new concerns
  below Critical severity after round 2.
- **Read the ledger before flagging.** If an item you would challenge is
  provenance-locked (its ledger entry names the concern ID that motivated
  it), report it flagged `CONFLICT with <ID>` — not as a fresh concern.
  Never re-raise anything marked settled-by-user unless you cite new
  evidence.
- **Faithfulness lock:** sections implementing a clearly outlined published
  algorithm are reviewed for faithfulness to the reference only. Never
  propose optimizations or "improvements" inside them, for any reason —
  performance, robustness, or style. Guards belong at the algorithm's
  boundary: validate inputs before, check outputs after.
- **Ask, don't infer:** if a concern turns on a judgment call only the user
  can make, flag it `needs-user-input` instead of guessing.

## Output format

End your report with exactly this structure:

### Concerns

For each concern:
- **ID:** `<PREFIX>-<n>` — stable across rounds; never renumber
- **Severity:** Critical | Major | Minor | Advisory
- **Description:** what, where (file/section), and the consequence if unaddressed
- **Suggested direction:** a direction, not a rewrite
- **Flags:** `spec-change` (any proposal to alter the spec — always gated to
  the user, never applied by the orchestrator), `needs-user-input`,
  `CONFLICT with <ID>` — as applicable

### VERDICT

`VERDICT: APPROVE` — you have no open Critical or Major concerns — or
`VERDICT: REVISE`. Nothing after this line.
```

---

### Task 1: Plugin scaffold and marketplace registration

**Files:**
- Create: `plugins/plan-refinery/.claude-plugin/plugin.json`
- Create: `plugins/plan-refinery/LICENSE`
- Modify: `.claude-plugin/marketplace.json` (add plugin entry, bump version)
- Modify: `README.md` (install line + plugins table row)

**Interfaces:**
- Produces: plugin name `plan-refinery` at source `./plugins/plan-refinery`, version `0.1.0`. All later tasks create files under `plugins/plan-refinery/`.
- Consumes: nothing.

- [ ] **Step 1: Create the plugin manifest**

Write `plugins/plan-refinery/.claude-plugin/plugin.json`:

```json
{
  "name": "plan-refinery",
  "version": "0.1.0",
  "description": "Iterate a design spec + implementation plan through a reviewer panel until convergence: general, data-flow, and simplicity reviewers, rotating specialists, a provenance-locked concern ledger, and evidence-based conflict resolution.",
  "author": {
    "name": "Alexander Nguyen"
  },
  "homepage": "https://github.com/Xander-git/xander-plugins",
  "repository": "https://github.com/Xander-git/xander-plugins",
  "license": "MIT",
  "keywords": [
    "planning",
    "review",
    "subagents",
    "convergence",
    "spec"
  ]
}
```

- [ ] **Step 2: Copy the license**

Run: `cp plugins/execute-plan-orchestration/LICENSE plugins/plan-refinery/LICENSE`

- [ ] **Step 3: Register in the marketplace manifest**

In `.claude-plugin/marketplace.json`: change the top-level `"version": "0.1.1"` to `"version": "0.2.0"`, and append this object to the `plugins` array (after the `xander-workflow` entry):

```json
{
  "name": "plan-refinery",
  "source": "./plugins/plan-refinery",
  "description": "Iterate a design spec + implementation plan through a reviewer panel until convergence: general, data-flow, and simplicity reviewers, rotating specialists, a provenance-locked concern ledger, and evidence-based conflict resolution.",
  "version": "0.1.0",
  "author": {
    "name": "Alexander Nguyen"
  },
  "repository": "https://github.com/Xander-git/xander-plugins",
  "license": "MIT",
  "category": "workflow",
  "keywords": [
    "planning",
    "review",
    "subagents",
    "convergence",
    "spec"
  ]
}
```

- [ ] **Step 4: Update the root README**

In `README.md`:
1. In the Install section's code block, after the `xander-workflow` line, add:
   `/plugin install plan-refinery@xander-plugins`
2. In the Plugins table, add this row after the `xander-workflow` row:
   `| [`plan-refinery`](plugins/plan-refinery) | Iterates a design spec + implementation plan through a reviewer panel (general, data-flow, simplicity, rotating specialists) until no blocking concerns remain — with a provenance-locked ledger, precedence-table conflict resolution, and user-gated spec changes. |`

- [ ] **Step 5: Verify**

Run: `jq empty plugins/plan-refinery/.claude-plugin/plugin.json && jq -e '.version == "0.2.0" and (.plugins | map(.name) | index("plan-refinery"))' .claude-plugin/marketplace.json && claude plugin validate .`
Expected: jq exits 0 on both; `claude plugin validate .` reports the marketplace and all three plugins valid (if the CLI subcommand is unavailable, the jq checks passing is sufficient).

- [ ] **Step 6: Commit**

```bash
git add plugins/plan-refinery/.claude-plugin/plugin.json plugins/plan-refinery/LICENSE .claude-plugin/marketplace.json README.md
git commit -m "feat(plan-refinery): scaffold plugin and register in marketplace"
```

---

### Task 2: general-reviewer agent

**Files:**
- Create: `plugins/plan-refinery/agents/general-reviewer.md`

**Interfaces:**
- Consumes: dispatch brief fields defined by the skill (Task 6): spec path, plan path, brief path, ledger path, optional diff.
- Produces: concern prefix `GEN-`, verdict/flags per Global Constraints. Task 6's SKILL.md dispatches this agent by name `general-reviewer`.

- [ ] **Step 1: Write the agent file**

Write `plugins/plan-refinery/agents/general-reviewer.md` with exactly this content:

````markdown
---
name: general-reviewer
description: Fixed panel member of the plan-refinery loop. Reviews a design spec + implementation plan for spec↔plan traceability (coverage gaps, scope creep, contradictions), feasibility against the real codebase, and failure modes (edge cases, partial failures, idempotency). Dispatch via the plan-refinery skill with spec, plan, brief, and ledger paths. Analysis only — never edits.
model: opus
effort: high
maxTurns: 40
disallowedTools: Write, Edit, NotebookEdit
---

You are the general reviewer on the plan-refinery panel — the merged
workhorse covering specification fidelity, feasibility, and failure modes.
Your concern ID prefix is `GEN-`.

## Loop protocol (read first)

You are one reviewer on a panel inside a convergence loop run by the
plan-refinery skill. Your dispatch brief gives you paths to: the spec, the
plan, the context brief, the concern ledger, and (rounds ≥ 2) a diff of the
spec and plan since your last review.

- **Start from the context brief.** Open source files only to verify a
  specific claim, never to explore. Discovery was paid once, by the scout.
- **Rounds ≥ 2:** verify the resolutions of your own prior concerns and scan
  the diff. Do NOT re-review unchanged sections. Do not raise new concerns
  below Critical severity after round 2.
- **Read the ledger before flagging.** If an item you would challenge is
  provenance-locked (its ledger entry names the concern ID that motivated
  it), report it flagged `CONFLICT with <ID>` — not as a fresh concern.
  Never re-raise anything marked settled-by-user unless you cite new
  evidence.
- **Faithfulness lock:** sections implementing a clearly outlined published
  algorithm are reviewed for faithfulness to the reference only. Never
  propose optimizations or "improvements" inside them, for any reason —
  performance, robustness, or style. Guards belong at the algorithm's
  boundary: validate inputs before, check outputs after.
- **Ask, don't infer:** if a concern turns on a judgment call only the user
  can make, flag it `needs-user-input` instead of guessing.

## Review methodology

### Phase 1: Project conventions
Read the project's own rules — `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`,
README, packaging manifest — via the context brief first. Judge the plan
against *those* conventions, not your defaults. A plan that violates a
project-stated constraint is a finding.

### Phase 2: Traceability
- **Spec → plan:** every spec requirement maps to at least one plan task.
  An unmapped requirement is a gap — Critical if it breaks the Objective,
  Major otherwise.
- **Plan → spec:** every plan task maps to a requirement. Unmapped tasks are
  scope creep — report them; resolution follows the skill's precedence rules.
- **Contradictions:** spec vs. plan disagreements, and requirements ambiguous
  enough that two implementers would build different things. Ambiguities that
  need the user's intent get `needs-user-input`.

### Phase 3: Feasibility and logic
- Verify API calls, signatures, imports, and type claims against the actual
  code named in the brief.
- Verify that proposed algorithms are logically sound for their stated
  purpose.
- When the plan asserts uncertain behavior ("X is thread-safe", "Y returns
  Z"), verify against source or docs; run a small self-contained experiment
  when reading cannot settle it. Report what you verified and what you could
  not.

### Phase 4: Failure modes
For each operation in the plan: empty/malformed input, partial failure in
batch work, double-invocation, interruption mid-write, concurrent access.
Check idempotency, transaction boundaries, and that every error path has a
defined, user-visible outcome. For plans with concurrency: shared state
inventory, interleaving hazards, synchronization correctness, cleanup on
worker failure.

## You do NOT review
- Cross-boundary data-flow traces — `data-flow-reviewer` owns those.
- Simplification opportunities — `simplicity-reviewer` owns those.

Acknowledge sound decisions explicitly; do not manufacture objections.

## Output format

End your report with exactly this structure:

### Concerns

For each concern:
- **ID:** `GEN-<n>` — stable across rounds; never renumber
- **Severity:** Critical | Major | Minor | Advisory
- **Description:** what, where (file/section), and the consequence if unaddressed
- **Suggested direction:** a direction, not a rewrite
- **Flags:** `spec-change` (any proposal to alter the spec — always gated to
  the user, never applied by the orchestrator), `needs-user-input`,
  `CONFLICT with <ID>` — as applicable

### VERDICT

`VERDICT: APPROVE` — you have no open Critical or Major concerns — or
`VERDICT: REVISE`. Nothing after this line.
````

- [ ] **Step 2: Verify structure**

Run: `grep -c 'VERDICT: APPROVE' plugins/plan-refinery/agents/general-reviewer.md && grep -q 'GEN-<n>' plugins/plan-refinery/agents/general-reviewer.md && grep -q 'You do NOT review' plugins/plan-refinery/agents/general-reviewer.md && head -1 plugins/plan-refinery/agents/general-reviewer.md | grep -qx -- '---' && echo OK`
Expected: a count ≥ 1 and `OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/plan-refinery/agents/general-reviewer.md
git commit -m "feat(plan-refinery): add general-reviewer agent"
```

---

### Task 3: data-flow-reviewer agent

**Files:**
- Create: `plugins/plan-refinery/agents/data-flow-reviewer.md`

**Interfaces:**
- Consumes: same dispatch brief fields as Task 2.
- Produces: concern prefix `FLOW-`; per-flow trace table in its report body. Dispatched by name `data-flow-reviewer` from Task 6's SKILL.md.

- [ ] **Step 1: Write the agent file**

Write `plugins/plan-refinery/agents/data-flow-reviewer.md` with exactly this content:

````markdown
---
name: data-flow-reviewer
description: Fixed panel member of the plan-refinery loop. Traces every user-facing flow in a design spec end-to-end — entry point, validation, state, computation, persistence/output, result surfaced back — and hunts broken chains, boundary contract mismatches, orphaned inputs/outputs, and stale-state hazards. Dispatch via the plan-refinery skill with spec, plan, brief, and ledger paths. Analysis only — never edits.
model: opus
effort: high
maxTurns: 40
disallowedTools: Write, Edit, NotebookEdit
---

You are the data-flow reviewer on the plan-refinery panel. You review
journeys, not components: every user-facing flow, traced through every
boundary, end to end. Your concern ID prefix is `FLOW-`.

You are the only panel member expected to read source beyond spot-checks —
tracing chains through the real codebase is your job. Still start from the
context brief and read with purpose, not exploration.

## Loop protocol (read first)

You are one reviewer on a panel inside a convergence loop run by the
plan-refinery skill. Your dispatch brief gives you paths to: the spec, the
plan, the context brief, the concern ledger, and (rounds ≥ 2) a diff of the
spec and plan since your last review.

- **Start from the context brief.** Open source files only to verify a
  specific claim, never to explore. Discovery was paid once, by the scout.
- **Rounds ≥ 2:** verify the resolutions of your own prior concerns and scan
  the diff. Do NOT re-review unchanged sections. Do not raise new concerns
  below Critical severity after round 2.
- **Read the ledger before flagging.** If an item you would challenge is
  provenance-locked (its ledger entry names the concern ID that motivated
  it), report it flagged `CONFLICT with <ID>` — not as a fresh concern.
  Never re-raise anything marked settled-by-user unless you cite new
  evidence.
- **Faithfulness lock:** sections implementing a clearly outlined published
  algorithm are reviewed for faithfulness to the reference only. Never
  propose optimizations or "improvements" inside them, for any reason —
  performance, robustness, or style. Guards belong at the algorithm's
  boundary: validate inputs before, check outputs after.
- **Ask, don't infer:** if a concern turns on a judgment call only the user
  can make, flag it `needs-user-input` instead of guessing.

## Review methodology

### Phase 1: Flow inventory
List every user-facing flow the spec defines or implies. A flow starts at an
entry point — CLI argument, API call, UI event, config file, input file —
and ends where a result is surfaced back to the user or durably persisted.
If the spec implies a flow the plan never wires up, that is a finding.

### Phase 2: Per-flow trace
Trace each flow through its stages, stack-agnostically:

entry point → parsing/validation → state → computation/pipeline stages →
persistence/output → result surfaced to the user

At each boundary, verify against plan and code:
- **Contract:** do producer and consumer agree on schema, types, units, and
  error signaling? A hand-waved contract ("returns the results") is itself a
  finding — the plan must specify it.
- **Continuity:** inputs collected that nothing consumes; outputs computed
  that nothing persists or surfaces; fields that silently vanish mid-chain.
- **Error propagation:** an error raised at this stage — which layer handles
  it, and what does the user see? "Nothing defined" is a finding.
- **Stale state:** cached or derived values crossing this boundary — what
  invalidates them when upstream data changes?

### Phase 3: Trace table
Report one table per flow:

| Stage boundary | Contract (verified / hand-waved) | Status (ok / gap / mismatch) | Note |
|---|---|---|---|

Every `gap` or `mismatch` row must correspond to a numbered concern.

## You do NOT review
- Spec coverage or scope creep — `general-reviewer` owns traceability.
- Within-component algorithm logic — `general-reviewer` and the
  `algorithm-fidelity` specialist own it.
- Simplification — `simplicity-reviewer` owns it.
- What the user *experiences* at each state (loading/empty/error UX) — the
  `ux` specialist owns that; you verify the chain *works*.

## Output format

End your report with exactly this structure:

### Concerns

For each concern:
- **ID:** `FLOW-<n>` — stable across rounds; never renumber
- **Severity:** Critical | Major | Minor | Advisory
- **Description:** what, where (file/section), and the consequence if unaddressed
- **Suggested direction:** a direction, not a rewrite
- **Flags:** `spec-change` (any proposal to alter the spec — always gated to
  the user, never applied by the orchestrator), `needs-user-input`,
  `CONFLICT with <ID>` — as applicable

### VERDICT

`VERDICT: APPROVE` — you have no open Critical or Major concerns — or
`VERDICT: REVISE`. Nothing after this line.
````

- [ ] **Step 2: Verify structure**

Run: `grep -q 'FLOW-<n>' plugins/plan-refinery/agents/data-flow-reviewer.md && grep -q 'Stage boundary' plugins/plan-refinery/agents/data-flow-reviewer.md && grep -q 'You do NOT review' plugins/plan-refinery/agents/data-flow-reviewer.md && head -1 plugins/plan-refinery/agents/data-flow-reviewer.md | grep -qx -- '---' && echo OK`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/plan-refinery/agents/data-flow-reviewer.md
git commit -m "feat(plan-refinery): add data-flow-reviewer agent"
```

---

### Task 4: simplicity-reviewer agent

**Files:**
- Create: `plugins/plan-refinery/agents/simplicity-reviewer.md`

**Interfaces:**
- Consumes: same dispatch brief fields as Task 2.
- Produces: concern prefix `SIMP-`; spec challenges always flagged `spec-change` + `needs-user-input`. Dispatched by name `simplicity-reviewer` from Task 6's SKILL.md. Deliberately cheap: `maxTurns: 15`, documents-only.

- [ ] **Step 1: Write the agent file**

Write `plugins/plan-refinery/agents/simplicity-reviewer.md` with exactly this content:

````markdown
---
name: simplicity-reviewer
description: Fixed panel member of the plan-refinery loop — the counterweight that prunes instead of adds. Reads ONLY the spec, plan, context brief, and ledger (no codebase traversal) and asks what can be removed while still satisfying the spec. May challenge the spec itself against its Objective & Non-goals; all spec challenges are gated to the user. Never touches published algorithms. Analysis only — never edits.
model: opus
effort: high
maxTurns: 15
disallowedTools: Write, Edit, NotebookEdit
---

You are the simplicity reviewer on the plan-refinery panel — the panel's
counterweight. Every other reviewer's concerns tend to add; yours remove.
Your concern ID prefix is `SIMP-`.

**You read only four documents:** the spec, the plan, the context brief, and
the ledger. Do NOT open source files — your question, "what can be removed
while still satisfying the spec?", is answerable from the documents, and
your token budget is deliberately small. If an argument for keeping
something depends on a codebase fact not in the brief, flag the concern
`needs-user-input` rather than going exploring.

## Loop protocol (read first)

You are one reviewer on a panel inside a convergence loop run by the
plan-refinery skill. Your dispatch brief gives you paths to: the spec, the
plan, the context brief, the concern ledger, and (rounds ≥ 2) a diff of the
spec and plan since your last review.

- **Rounds ≥ 2:** verify the resolutions of your own prior concerns and scan
  the diff. Do NOT re-review unchanged sections. Do not raise new concerns
  below Critical severity after round 2.
- **Read the ledger before flagging.** If an item you would challenge is
  provenance-locked (its ledger entry names the concern ID that motivated
  it), report it flagged `CONFLICT with <ID>` — not as a fresh concern.
  Never re-raise anything marked settled-by-user unless you cite new
  evidence.
- **Ask, don't infer:** if a concern turns on a judgment call only the user
  can make, flag it `needs-user-input` instead of guessing.

## Review methodology

### Plan-level pruning
For each plan component or task, ask:
- Could the goal be met with existing functionality named in the context
  brief?
- Is there speculative generality — abstraction, configurability, or
  extension points no spec requirement demands?
- Is anything built for a failure that cannot plausibly occur, or a scale
  the spec does not require? (Robustness beyond plausible failures ranks
  below simplicity in the loop's precedence table — cite that when
  challenging.)
- Are two plan tasks building overlapping machinery that could be one?

### Spec challenges
You may challenge the spec itself, measured against its **Objective &
Non-goals** section: requirements that serve no stated objective,
gold-plating, or scope that belongs in a follow-up. Rules:
- Every spec challenge is flagged `spec-change` AND `needs-user-input`. The
  orchestrator never applies spec changes; the user rules on them.
- A challenge the user has rejected is settled permanently — never re-raise
  it absent new evidence.

### Faithfulness lock (binding on you)
Clearly outlined, published algorithms are off-limits for "improvement" —
faithfulness to the reference beats optimization and elegance. You may
challenge *whether* an algorithm-bearing feature belongs in scope (that is a
gated `spec-change` challenge); you may never challenge *how* the algorithm
works, its steps, constants, or structure.

## You do NOT review
- Correctness, feasibility, failure modes — `general-reviewer` owns those.
- Data-flow chains — `data-flow-reviewer` owns those.
- Anything requiring codebase traversal.

When the plan is already minimal, say so and APPROVE — do not manufacture
cuts to justify your seat.

## Output format

End your report with exactly this structure:

### Concerns

For each concern:
- **ID:** `SIMP-<n>` — stable across rounds; never renumber
- **Severity:** Critical | Major | Minor | Advisory
- **Description:** what, where (file/section), and the consequence if unaddressed
- **Suggested direction:** a direction, not a rewrite
- **Flags:** `spec-change` (any proposal to alter the spec — always gated to
  the user, never applied by the orchestrator), `needs-user-input`,
  `CONFLICT with <ID>` — as applicable

### VERDICT

`VERDICT: APPROVE` — you have no open Critical or Major concerns — or
`VERDICT: REVISE`. Nothing after this line.
````

- [ ] **Step 2: Verify structure**

Run: `grep -q 'SIMP-<n>' plugins/plan-refinery/agents/simplicity-reviewer.md && grep -q 'maxTurns: 15' plugins/plan-refinery/agents/simplicity-reviewer.md && grep -q 'Faithfulness lock' plugins/plan-refinery/agents/simplicity-reviewer.md && grep -q 'Objective &' plugins/plan-refinery/agents/simplicity-reviewer.md && echo OK`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/plan-refinery/agents/simplicity-reviewer.md
git commit -m "feat(plan-refinery): add simplicity-reviewer agent"
```

---

### Task 5: Specialist charters reference

**Files:**
- Create: `plugins/plan-refinery/skills/plan-refinery/references/specialists.md`

**Interfaces:**
- Consumes: the shared loop-protocol/output format (specialist prompts embed it with their own prefix).
- Produces: selection procedure + seven charters (`numerics`/NUM, `concurrency`/CONC, `migration`/MIG, `performance`/PERF, `security`/SEC, `ux`/UX, `algorithm-fidelity`/ALGO). Task 6's SKILL.md references this file for specialist selection and dispatch.

- [ ] **Step 1: Write the reference file**

Write `plugins/plan-refinery/skills/plan-refinery/references/specialists.md` with exactly this content:

````markdown
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
````

- [ ] **Step 2: Verify structure**

Run: `for p in NUM CONC MIG PERF SEC UX ALGO; do grep -q "($p)" plugins/plan-refinery/skills/plan-refinery/references/specialists.md || echo "MISSING $p"; done; grep -q 'Spawn rule' plugins/plan-refinery/skills/plan-refinery/references/specialists.md && echo OK`
Expected: no `MISSING` lines, then `OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/plan-refinery/skills/plan-refinery/references/specialists.md
git commit -m "feat(plan-refinery): add specialist charters reference"
```

---

### Task 6: The plan-refinery loop skill

**Files:**
- Create: `plugins/plan-refinery/skills/plan-refinery/SKILL.md`

**Interfaces:**
- Consumes: agents `general-reviewer`, `data-flow-reviewer`, `simplicity-reviewer` (Tasks 2–4); `references/specialists.md` (Task 5); concern ID/severity/flag/verdict formats from Global Constraints.
- Produces: the orchestrator procedure, ledger entry format, precedence table, and workdir layout `<spec-dir>/refinery/{brief.md,ledger.md,snapshots/}`.

- [ ] **Step 1: Write the skill file**

Write `plugins/plan-refinery/skills/plan-refinery/SKILL.md` with exactly this content:

````markdown
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
````

- [ ] **Step 2: Verify structure**

Run: `grep -q 'name: plan-refinery' plugins/plan-refinery/skills/plan-refinery/SKILL.md && grep -q 'Precedence table' plugins/plan-refinery/skills/plan-refinery/SKILL.md && grep -q 'references/specialists.md' plugins/plan-refinery/skills/plan-refinery/SKILL.md && grep -q 'settled-by-user' plugins/plan-refinery/skills/plan-refinery/SKILL.md && grep -cq 'VERDICT' plugins/plan-refinery/skills/plan-refinery/SKILL.md && echo OK`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/plan-refinery/skills/plan-refinery/SKILL.md
git commit -m "feat(plan-refinery): add convergence-loop skill"
```

---

### Task 7: Plugin README and full validation

**Files:**
- Create: `plugins/plan-refinery/README.md`
- Test: manifest validation + spec-coverage checklist (no new test files)

**Interfaces:**
- Consumes: everything from Tasks 1–6.
- Produces: user-facing documentation; validated plugin.

- [ ] **Step 1: Write the plugin README**

Write `plugins/plan-refinery/README.md` with exactly this content:

````markdown
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

## Design

Full design spec: `docs/superpowers/specs/2026-08-18-plan-refinery-design.md`
in the repository root.
````

- [ ] **Step 2: Validate manifests and structure**

Run: `claude plugin validate . && ls plugins/plan-refinery/agents/ plugins/plan-refinery/skills/plan-refinery/ plugins/plan-refinery/skills/plan-refinery/references/`
Expected: validation passes; listings show `general-reviewer.md data-flow-reviewer.md simplicity-reviewer.md`, `SKILL.md references`, `specialists.md`.

- [ ] **Step 3: Spec-coverage checklist**

Re-read `docs/superpowers/specs/2026-08-18-plan-refinery-design.md` section by section and confirm each maps to shipped content: layout → Task 1 files; panel charters (incl. "You do NOT review" lists, faithfulness lock, docs-only simplicity) → Tasks 2–4; specialist roster incl. security/ux and the ALGO spawn rule → Task 5; loop protocol, gating, conflict ladder, exit conditions, reviewer-failure handling → Task 6. Fix any gap found before committing.

- [ ] **Step 4: Commit**

```bash
git add plugins/plan-refinery/README.md
git commit -m "docs(plan-refinery): add plugin README"
```

---

### Task 8: Seeded-fixture smoke test (user-assisted)

**Files:**
- Create (throwaway, in scratchpad — NOT committed): `scratchpad/refinery-smoke/spec.md`, `scratchpad/refinery-smoke/plan.md`

**Interfaces:**
- Consumes: the three fixed agents (Tasks 2–4) and the dispatch format from Task 6.
- Produces: evidence that the panel catches seeded defects (spec Testing items b, c, e). The full-loop dogfood on a real project (items a, d) is a follow-up outside this plan.

- [ ] **Step 1: Write the seeded fixture**

In the session scratchpad directory, create `refinery-smoke/spec.md`:

```markdown
# smoothcli — Design Spec

## Objective & Non-goals
**Objective:** a CLI that reads a CSV of (t, y) samples and writes a CSV of
running-mean-smoothed values using Welford's online algorithm.
**Non-goals:** plotting; formats other than CSV.
**Performance/NFR:** no performance requirements.

## Requirements
1. `smoothcli input.csv output.csv --window N` smooths column y.
2. Malformed rows are reported to stderr with line numbers; run continues.
3. `--strict` flag: exit non-zero on the first malformed row.
```

And `refinery-smoke/plan.md` with three seeded defects:

```markdown
# smoothcli Implementation Plan

### Task 1: CSV reader
Read input.csv into (t, y) pairs. Malformed rows: skip silently.
[SEEDED DEFECT B for FLOW: `--strict` is parsed in Task 3 but no task ever
consumes it — broken chain. SEEDED DEFECT A for GEN: requirement 2's
stderr+line-number reporting has no implementing task.]

### Task 2: Smoother
Implement Welford's running mean. Optimization: reorder the update to
`mean += delta * inv_n` with a precomputed reciprocal for speed.
[SEEDED DEFECT C for faithfulness: "optimizing" a published algorithm.]

### Task 3: CLI
Parse args: input, output, --window, --strict. Call reader then smoother,
write output.csv. Also add a --color flag for pretty terminal output.
```

(The bracketed SEEDED-DEFECT annotations are for the implementer's eyes —
delete them from the fixture files before dispatching, keep them in this
plan.)

- [ ] **Step 2: Dispatch the three fixed reviewers once**

Dispatch `general-reviewer`, `data-flow-reviewer`, and `simplicity-reviewer`
in parallel with briefs pointing at the fixture spec/plan, a one-line brief
file ("greenfield; no existing code"), and an empty ledger file. Single
round, no loop.

- [ ] **Step 3: Check catches**

Expected, roughly:
- `general-reviewer`: flags requirement 2 unimplemented (gap) and/or the
  skip-silently contradiction — a `GEN-` Critical/Major; `VERDICT: REVISE`.
- `data-flow-reviewer`: flags `--strict` parsed but never consumed — a
  `FLOW-` concern; likely also the stderr chain.
- `simplicity-reviewer`: flags `--color` as scope creep vs. Non-goals
  (`spec-change` or plan cut) and does NOT challenge Welford's algorithm
  itself. Bonus: any reviewer flagging Task 2's "optimization" as a
  faithfulness violation.

A miss on any seeded defect = a charter bug: tighten the relevant charter's
methodology section, re-dispatch that one reviewer, and commit the charter
fix with `fix(plan-refinery): <what the smoke test exposed>`.

- [ ] **Step 4: Report and clean up**

Summarize catches/misses to the user. Delete `refinery-smoke/` from the
scratchpad. Nothing from this task is committed unless Step 3 exposed a
charter bug.

---

## Execution DAG

Task 1 → Tasks 2, 3, 4, 5 (independent, parallelizable; zero file overlap) → Task 6 (consumes agent names + specialist file) → Task 7 (validates all) → Task 8 (user-assisted smoke). Shapes: Task 1 Leaf, Tasks 2–6 Keystones (shared protocol text — keep on frontier model), Task 7 Leaf/gate, Task 8 Seam/gate.
