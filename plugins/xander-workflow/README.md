# xander-workflow

Five engineering workflow skills that cover the parts of a task that aren't writing
the code: deciding what to build, transcribing an outside algorithm faithfully,
finding what's duplicated, searching structurally, and writing up what happened.

## Skills

| Skill | Use it when |
|---|---|
| `present-solutions` | You're weighing design choices. Lays out candidate approaches with background, tradeoffs (accuracy, cost, complexity, technical debt), failure modes, and a reasoned recommendation — instead of silently picking one. |
| `porting-a-reference-algorithm` | You're transcribing a paper or reference implementation into a codebase. A checkable procedure: assemble references, cite `file:line`, diff rather than eyeball, pin behavior with a golden fixture plus behavioral controls, mutation-test the suite, record every deviation. |
| `dedupe-scanner` | You want a review focused on duplication rather than bugs — repeated literals, magic numbers, config dicts, schemas, logging and I/O patterns, test fixtures. Advisory only; it never edits without per-finding confirmation. |
| `ast-grep` | Text search isn't enough and you need to match code by structure. Guide to writing ast-grep rules, with a full rule reference. |
| `summarize-session` | You want a shareable write-up of a Claude Code session. Evidence-gated — every number comes from a file or command output on disk, never from memory. Explicit invocation only. |

## Install

```
/plugin marketplace add Xander-git/xander-plugins
/plugin install xander-workflow@xander-plugins
```

## Notes

- `ast-grep` documents rule syntax; it assumes the `ast-grep` binary is available
  on your `PATH` when you actually run a search.
- `summarize-session` ships a `kernel.py` helper and summarizes only the current
  session.
- `dedupe-scanner`'s templates are domain-neutral: they use a generic tabular
  pipeline (`dataset_id` / `region` / `value`) as a running example, and every
  Python block parses. Rename to your own domain nouns when drafting a sketch.
