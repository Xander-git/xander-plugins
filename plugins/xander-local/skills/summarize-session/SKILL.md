---
name: summarize-session
description: >-
  Generate a shareable, evidence-gated write-up of the CURRENT Claude Code
  session — what was asked, how it was steered, what was built, and what was
  learned. INVOKE ONLY ON EXPLICIT REQUEST — never proactively or automatically.
  Trigger only when the user explicitly asks for it, e.g. "summarize this
  session", "/summarize-session", "write up what we did", "document this
  workflow", "session recap/summary", or "hand-off doc". Do NOT invoke because a
  session merely feels done, long, or worth documenting — wait for the ask.
  Produces a three-tier markdown document (fixed spine + evidence-gated body +
  fixed close), pulls every number from files/command output on disk (never
  prose or memory), runs an internal-consistency check before saving, and gates
  section selection through a one-line approval preview. Self-summary only
  (the current session).
---

# summarize-session

Turn the current session into a document a teammate (or your future self) can
read to understand **what was asked, how it was steered, what was produced, and
what was learned** — without replaying the whole transcript.

**Invocation is request-only.** This skill is never triggered automatically.
Run it only when the user explicitly asks to summarize/write up/document the
session. If you are unsure whether they asked for it, do not run it.

This skill was distilled from a real workflow write-up. Its discipline exists
because each rule below was earned by a failure: numbers that drifted from the
files they came from, a capability claimed as tested when it wasn't, a correction
announced but not fully applied. Follow the rules and the document is
trustworthy.

---

## The output: a three-tier document

**TIER 1 — Spine (always present, always this order):**
1. **Header** — project, purpose, status, date.
2. **Original request** — the first user task, **quoted verbatim**.
3. **Decision & steering log** — a chronological table of the human-in-the-loop
   choices, **each framed by WHY it mattered**, not just what was chosen. This is
   the transferable heart of the doc. If the session was a single pass with no
   course corrections, the section still appears with a one-line note saying so.

**TIER 2 — Conditional body (frozen relative order; include a section only if
its trigger fired; omit empty ones entirely and renumber so there are no gaps):**
4. What was built / done
5. External sources & dependencies
6. Data / code transformations
7. Methodological caveats
8. Validation / testing
9. Corrections / course changes
10. Planned / next steps

**TIER 3 — Close (always present):**
11. **Lessons learned**
12. **Artifact index**

### The catalog is a FLOOR, not a ceiling
The body list covers common cases. It is **not exhaustive.** After gating the
catalog sections, review the session for any *substantial* thread none of them
capture, and **mint a new body section** for it (e.g. "Root cause & fix" for
debugging, "Environment & remote setup" for infra, "Model & hyperparameters" for
modeling, "Sources & synthesis" for a research session, "What didn't work" for a
negative result). A minted section must clear the SAME bar as a catalog one:
evidence-gated (concrete session material behind it) and substantial (more than a
paragraph, and doesn't fit cleanly as a subsection of an existing section). Mint
only into the body — never the spine or close. Place it next to related catalog
sections so the frozen-order feel holds. Flag every minted section in the
approval preview as new.

---

## Workflow

### Step 1 — Gather evidence (from the transcript + the workspace, not memory)
Summarize the CURRENT session only. Two evidence sources:

1. **The conversation transcript** — you already hold it in context. From it,
   pull: the **first user message** (the verbatim original request), the
   **steering turns** (user turns that redirect, choose between options, correct,
   or constrain the work), the **corrections** (places where a prior output was
   revised), and candidate **lessons**.
2. **The workspace** — get the concrete record of what actually changed, so every
   claim is backed by a file or command output rather than recollection. Prefer
   these over memory:

```bash
# What changed this session (in a git repo)
git status --short
git diff --stat
git log --oneline -20            # if you committed during the session

# Not a git repo? enumerate what you created/edited from the session
# and re-read those files before citing anything from them.
```

Re-open (with Read) any file, log, or command output whose numbers, IDs, paths,
or metrics you intend to cite. Do not cite from chat prose or memory.

### Step 2 — Gate the sections
Decide which body sections fire **from the evidence**, not from habit. Then do
the residual pass for minted sections (see FLOOR rule above). The full catalog is
in `kernel.py` (`section_catalog()`); run it if you want the machine-readable
list:

```bash
python3 "$SKILL_DIR/kernel.py" catalog   # $SKILL_DIR = this skill's folder
```

Trigger guide (evidence → include):
- **External sources & dependencies** — any network fetch, API/MCP call, package
  install, or external service was used.
- **Data / code transformations** — input was ingested from a source and reshaped
  (parsed, merged, migrated, refactored, normalized). Document per-source.
- **Methodological caveats** — a non-obvious method, parameter, or design choice
  (a threshold, an algorithm, an architecture decision) was made and matters.
- **Validation / testing** — tests, controls, QC, linters, or sanity checks ran.
- **Corrections / course changes** — a prior output was revised or a claim
  retracted.
- **Planned / next steps** — work was explicitly deferred or left unfinished.

### Step 3 — Auto-extract candidate lessons
Draw lessons in **priority order**: (1) fixes to real errors hit this session (a
fixed error is a gotcha by definition), (2) non-obvious method/design choices,
(3) anything the user explicitly flagged as a preference or rule. Frame each as a
transferable rule, not a narration of what happened.

### Step 4 — Approval preview (proposed-for-approval gate)
Before writing, show the user ONE compact line of what will be included and let
them veto / rename / merge / add. Use the AskUserQuestion tool (or a plain
question if it's simpler). Minted sections are flagged `+[Title]`; omitted catalog
sections show why. Example:

`Sections: OK prompt, decisions, built, sources; SKIP transforms(none), tests(none); +[Root cause & fix] | Lessons: cache-invalidation, retry-backoff, config-precedence — edit/veto/add?`

Write the document only after the user confirms.

### Step 5 — Compose (pull every number from the file, never from prose)
For any figure, count, ID, path, or metric that goes in the doc, **read it from
the file or command output on disk** (via Read, or re-run the command), not from
memory or from earlier chat prose. This is the single most important rule — most
numeric errors come from re-typing a remembered value.

Write file references as relative Markdown links, e.g. `[config.py](src/config.py)`.

### Step 6 — Internal-consistency check (before saving)
Run the scanner on the composed text and resolve every flag. This is what catches
the same quantity stated two different ways in two sections.

```bash
python3 "$SKILL_DIR/kernel.py" scan SESSION_SUMMARY.md
# near_miss MUST be empty or every pair explained;
# eyeball `repeated` so each repeated number/ID agrees everywhere it appears.
```

Any `near_miss` pair is a suspected same-quantity-stated-differently error. Trace
each back to its source file and fix before saving.

### Step 7 — Save
Write the composed document with the Write tool to `SESSION_SUMMARY.md` (or a
path/name the user chose, named for the session/task). Report the saved path and
the one-line section list actually used.

---

## Hard rules (non-negotiable)
0. **Request-only.** Run this skill only when the user explicitly asked for a
   session summary. Never trigger it proactively.
1. **Numeric fidelity.** Every number/ID/metric is read from a file or command
   output at compose time, never from prose or memory.
2. **Internal consistency.** Run the `scan` and resolve every flag; the same
   quantity reads identically everywhere it appears.
3. **Honest provenance.** Mark a capability, dependency, or route "confirmed" only
   if it was actually exercised this session; otherwise "unverified" and say why.
   Never record a claimed status as a tested one.
4. **Verbatim vs reconstruction.** The original prompt is quoted verbatim. The
   decision log is a reconstruction — present it as such; never imply it is a
   transcript. Optionally quote short verbatim steering snippets beside rows.
5. **Empty sections are omitted, not stubbed** — except the tier-1 spine and
   tier-3 close, which always appear (a thin note is fine when content is light).
6. **Decision log is framed by WHY.** Each row says why the choice mattered / what
   it protected against — that is the part another engineer can reuse.

---

## kernel.py helpers
`kernel.py` is a standalone script (no host runtime required). Run it with
`python3`:
- `python3 kernel.py catalog` → prints the three-tier catalog (spine / body /
  close) with each section's title and trigger. The body is a FLOOR — mint
  substantial extras.
- `python3 kernel.py scan <file.md>` → prints `repeated` (every number/ID
  appearing on more than one line, with locations, so repeats can be eyeballed)
  and `near_miss` (close-but-unequal numbers sharing nearby words — the classic
  drifted-figure bug). Resolve every near_miss before saving.

Both are also importable: `from kernel import section_catalog, consistency_scan`.
