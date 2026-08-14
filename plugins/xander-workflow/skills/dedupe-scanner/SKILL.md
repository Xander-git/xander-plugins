---
name: dedupe-scanner
description: Audit a codebase for extractable duplication and propose targeted refactors. Use this whenever the user asks for a code review focused on duplication, DRY violations, repetition, magic values, code smells, cleanup, or extraction opportunities. Also use proactively when the user shares multiple modules and asks what should be consolidated, mentions "stringly-typed" code, asks about shared configuration or design tokens, or wants a pre-PR/pre-commit audit pass focused on consolidation rather than bugs or performance. Covers string literals, magic numbers, config dicts, design tokens, I/O patterns, schemas, plotting setup, logging patterns, tolerances, test fixtures, URL construction, and resource lifecycle pairs. Advisory only; never auto-modify code without explicit per-finding confirmation.
---

# dedupe-scanner

Find duplication worth extracting. Distinguish semantic duplication (same meaning, consolidate) from coincidental duplication (same characters, leave alone). Output a structured report of candidates with file/line locations, severity, confidence, and concrete refactor sketches.

## Core principle

A single rule like "extract duplicates" conflates three orthogonal axes:

1. **Cause**: semantic duplication (same meaning) vs. coincidental duplication (same characters, unrelated meanings).
2. **Role**: identifier, discriminator, sentinel, display text, format template, configuration.
3. **Cardinality**: singleton, closed enumeration, open set.

Only semantic duplication is a candidate for extraction. Extracting coincidental matches couples unrelated code and causes false change-amplification when one site needs to evolve.

## Workflow

Run as a discrete audit pass, not interleaved with feature work:

1. **Scope**. Confirm with the user what to scan (a package, a directory, changed files in a PR). Default to the active package excluding `tests/`, vendored dependencies, generated code, and anything in `.dedupeignore` if present.
2. **Scan**. For each category, apply the detection rules in `references/categories.md`. Use AST-based detection (Python: `ast` or `libcst`; TypeScript: `ts-morph` or tree-sitter) wherever structure matters. Regex is acceptable only for textual categories (color hex, font names, URLs).
3. **Filter**. Drop coincidental matches using the per-category falsifiers. Apply the cost-benefit filter: skip findings where extraction would produce a name longer than the literal, or where the value is used once.
4. **Report**. Emit findings in the format below, grouped by severity then by category. Include a summary header with counts.
5. **Wait for confirmation**. Do not apply any refactor without the user's explicit per-finding or per-category approval. The skill's job ends at the report.

## Categories scanned

This skill scans for the following twelve categories. Detection rules, falsifiers, and refactor targets for each are in `references/categories.md`. Read that file before scanning.

1. **String literals in closed sets**: repeated strings used as dispatch keys, mode flags, column names. Extract to `StrEnum`, `Literal[...]` alias, or `Final[str]`.
2. **Magic numbers**: non-trivial numeric literals reused or carrying domain meaning. Extract to named `Final` constants with units in the name.
3. **Shared configuration dicts**: recurring kwargs blocks across functions or modules. Extract to a frozen dataclass, `TypedDict`, or Pydantic model.
4. **Styling and design tokens**: repeated color hex codes, fonts, spacing values, Plotly layout fragments, Tailwind class clusters. Extract to a tokens module or Plotly template.
5. **I/O access patterns**: repeated reads, writes, path construction, or glob patterns against the same logical artifact. Extract to a typed accessor function.
6. **Schema definitions**: column lists, dtype maps, or Polars/Pandas schemas declared at multiple sites. Extract to a single schemas module.
7. **Plot and figure construction**: repeated axis setup, legend, font, colorbar formatting. Extract to a Plotly template or matplotlib style file plus small composable helpers.
8. **Logging patterns**: recurring format strings or context dicts on log records. Extract to a `LoggerAdapter`, `structlog` binding, or module logger factory.
9. **Numeric tolerances and epsilons**: bare `1e-6` / `1e-8` etc. used as `atol`/`rtol`. Extract to named domain constants.
10. **Test fixtures**: repeated setup across `test_*.py` files. Extract to `conftest.py` pytest fixtures with appropriate scope.
11. **URL and endpoint construction**: repeated base URL plus path joining or query parameter construction. Extract to a typed client or path-builder.
12. **Resource lifecycle pairs**: matched open/close, connect/disconnect, acquire/release outside `with` blocks. Extract to a context manager.

(Numbers above are the skill's category IDs; they are renumbered from the broader taxonomy to reflect only what this skill covers. Categories on dispatch tables, data clumps, error handling, pure expressions, CLI argument groups, and validation logic are out of scope.)

## Output format

Emit findings as a YAML report. One block per finding:

```yaml
- id: STR-001                          # CAT-NNN where CAT is a 3-letter category code
  category: string_literals_closed_set
  severity: medium                     # low | medium | high
  confidence: 0.85                     # 0.0 to 1.0
  locations:
    - path: src/<pkg>/transform.py
      lines: [42, 87, 134]
    - path: src/<pkg>/report.py
      lines: [12]
  evidence: |
    Literal "fast" used as a mode discriminator in 4 locations across
    2 modules, paired with "accurate" in if/elif dispatch in transform.py:40.
  proposal: |
    Define Mode(StrEnum) in src/<pkg>/types.py with members
    FAST = "fast", ACCURATE = "accurate". Public functions accept
    Mode | Literal["fast", "accurate"] and normalize on entry.
  refactor_sketch: |
    # src/<pkg>/types.py
    from enum import StrEnum
    class Mode(StrEnum):
        FAST = "fast"
        ACCURATE = "accurate"
  risk: low                            # likelihood of breakage if applied naively
  blast_radius: 2 modules, ~6 call sites
```

Category codes: `STR` (1), `NUM` (2), `CFG` (3), `STY` (4), `IO` (5), `SCH` (6), `PLT` (7), `LOG` (8), `TOL` (9), `FIX` (10), `URL` (11), `RES` (12).

Refactor sketches must be syntactically valid in the target language. If a sketch requires imports, include them. If the proposal touches a public API, note that in the `risk` field.

Group the final report by severity (high first), then by category. Lead with a summary:

```
Summary
-------
Scanned: 47 Python files, 12 TypeScript files
Findings: 23 (4 high, 11 medium, 8 low)
By category: STR=6, NUM=3, CFG=2, STY=4, IO=2, SCH=1, PLT=2, LOG=1, TOL=1, FIX=1, URL=0, RES=0
```

## Severity rubric

- **High**: duplication that has caused or will likely cause silent bugs. Examples: stringly-typed dispatch where a typo creates a silent no-op branch; tolerance values that drift between sites and produce inconsistent thresholds; schemas that disagree across reader and writer; paths constructed differently for the same logical artifact.
- **Medium**: maintenance burden. Examples: config dicts repeated across functions; styling tokens scattered across modules; recurring kwargs to `pl.read_parquet`.
- **Low**: cosmetic, isolated to one module, low blast radius. Examples: a magic number used twice in the same file; a fixture pattern in two adjacent test files.

## Confidence rubric

Confidence is the detector's belief that the finding is a real semantic duplicate (not a coincidence):

- **≥0.9**: AST or structural match plus semantic role match. Both sites pass the value to the same function parameter, or both define the same schema column with the same dtype.
- **0.7 to 0.9**: structural match without confirmed semantic role match.
- **<0.7**: textual or fuzzy match only. Surface with a "verify manually" tag in the evidence field.

## Hard rules

- **Do not auto-modify code.** Output is advisory. Refactors require explicit confirmation per finding or per category.
- **Do not flag coincidental duplication.** If two sites share characters but not meaning, leave them alone. Apply each category's falsifier.
- **Do not propose extractions that worsen readability.** Skip findings where the extracted name would be longer than the literal, or where the literal is more readable in place than under an alias.
- **Do not merge duplication across stability boundaries** (public API surface plus internal helper) without explicit approval. Surface as a finding, but mark `risk: high`.
- **Do not touch generated code, vendored dependencies, or paths in `.dedupeignore`.**
- **Do not flag duplication required by a framework's contract** (e.g., repeated decorator stacks on FastAPI endpoints, identical Pydantic field declarations across siblings).
- **Honor pragma comments**: `# dedupe: ignore`, `# dedupe: ignore-next-line`, `# dedupe: ignore-category=<code>`, and file-level `# dedupe: ignore-all`. For TypeScript: `// dedupe: ignore` etc.

## Cross-cutting heuristics

- **Test files** get all detectors but at relaxed severity (default to low unless the finding is structural, e.g., fixture extraction).
- **Cross-language duplication** (Python and TypeScript) is a distinct sub-finding. Design tokens, schemas, and URL bases defined in both languages should converge on a single source of truth (JSON, YAML, or a build-time codegen step) rather than be deduplicated within each language separately.
- **Rule of three**: prefer 3+ occurrences before flagging, except for high-stakes categories (tolerances, schemas, dispatch discriminators) where 2 occurrences is enough because drift between two sites is already a real risk.

## What this skill does not do

- Fix bugs, optimize performance, or eliminate dead code. Those are separate review passes.
- Cross-repository deduplication.
- Choose the final destination module for extracted constants beyond a heuristic suggestion (`config/`, `types/`, `schemas/`, `tokens/`). Final placement is the user's call.
- Detect duplication in dispatch tables, data clumps, error handling blocks, repeated pure expressions, CLI argument groups, or validation logic. Those categories are deliberately out of scope; refer the user to a follow-up skill if they ask.

## Suggested implementation stack

When the user asks the skill to actually run (not just describe what it would find), use:

- **Python AST**: `libcst` for round-trip preservation (needed for refactor sketches), `ast` as a faster fallback for hashing and analysis where formatting is irrelevant.
- **Type resolution**: `pyright --outputjson` invoked as a subprocess, cached by file hash. `jedi` as a lighter alternative.
- **Polars expression equality**: `pl.Expr.meta.eq()` and `pl.Expr.meta.serialize()` for hashing (relevant to Category 5 and 6 when scanning Polars-heavy codebases).
- **Cross-language**: `tree-sitter` with the Python and TypeScript grammars, normalized to a common intermediate representation for categories 1, 3, 4, 6.
- **Storage**: SQLite for the candidate database, supporting incremental scans and queries by category, severity, file.

For one-off scans on small codebases, a single Python script using `ast` plus `pathlib.Path.rglob` is sufficient. Reach for the heavier stack only when the codebase is large or the scan needs to be incremental.

## Refactor templates

For each refactor target, use the templates in `references/refactor-templates.md`. Read that file before drafting the `refactor_sketch` field of any finding.

## Workflow summary

1. Confirm scope with the user.
2. Read `references/categories.md` for per-category detection rules and falsifiers.
3. Read `references/refactor-templates.md` for refactor sketch templates.
4. Scan. Build candidate findings.
5. Apply falsifiers. Drop coincidental matches.
6. Score severity and confidence.
7. Emit the YAML report grouped by severity then category, with a summary header.
8. Stop. Wait for the user to approve refactors before changing any code.
