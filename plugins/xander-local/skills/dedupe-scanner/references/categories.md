# Detection rules per category

Each category has four parts: **detect** (what to look for), **extract to** (the refactor target), **do not flag if** (the falsifier that prevents coincidental matches), and **severity defaults** (the typical severity floor).

Apply the falsifier strictly. Coincidental duplication is more harmful to flag than to miss because it causes false coupling.

---

## Category 1 (STR): String literals in closed sets

**Detect.** Repeated string literals used as dispatch keys, mode flags, column names, or dict keys.
- Threshold: ≥2 occurrences across non-test files, or ≥3 within one file.
- Stronger signal: the literal appears in `if x == "...":`, `match x: case "...":`, `dict[..., "..."]`, or as the value of a parameter annotated as `str` whose docstring lists a closed set of options.

**Extract to.** Choose based on use:
- `StrEnum` (Python 3.11+) when the set must serialize as strings or interop with JSON, CLI, file formats.
- `Literal[...]` alias alone when the set is purely a type-check concern with no runtime dispatch or iteration.
- `Final[str]` module constant for a single fixed value reused for its meaning (config key, header name, sentinel).

Public APIs accepting these values should be typed as `EnumType | Literal["a", "b", ...]` and normalize on entry with `value = EnumType(value)`. Internal code uses enum members exclusively.

**Do not flag if.**
- The literal is a log message, exception message, or docstring fragment.
- The literal is part of a regex pattern, version tag, or other textual identity.
- The literal appears in a one-off test fixture not shared across tests.
- The strings happen to match characters but are used in unrelated contexts (one is a dict key, another is a CLI flag).

**Severity defaults.** High when used in dispatch (silent no-op risk on typo). Medium when used as a dict key or column name. Low when used in a single dict literal.

---

## Category 2 (NUM): Magic numbers

**Detect.** Numeric literals other than `0, 1, -1, 2` appearing ≥2 times, OR any numeric literal in a domain-meaningful position regardless of recurrence (thresholds, tolerances, kernel sizes, percentiles, color values, RGB triples, sigma values).

**Extract to.** `Final` module constant. The name must encode units and intent:
- Good: `SMOOTHING_WINDOW_SAMPLES: Final[int] = 32`, `MIN_SEGMENT_LENGTH_PX: Final[int] = 50`, `OUTLIER_Z_THRESHOLD: Final[float] = 2.3`.
- Bad: `WINDOW = 32`, `THRESHOLD = 50`.

For groups of related constants, use a frozen dataclass or named tuple to keep them associated.

**Do not flag if.**
- The number is an array index, loop bound derived from data shape, or a mathematical constant used once in a formula whose meaning is local (`return x * 0.5 + y * 0.5`).
- The number is a documented requirement from a referenced algorithm (e.g., `4` in a Sobel kernel definition).

**Severity defaults.** High when the same numeric tolerance is duplicated across modules (drift risk; overlaps with Category 9). Medium for kernel sizes, thresholds. Low for single-file scoped constants.

---

## Category 3 (CFG): Shared configuration dicts

**Detect.** Dict or kwargs literals with ≥3 keys recurring with identical or near-identical values across functions or modules. Common in:
- Algorithm parameter dicts passed to multiple functions.
- `pl.read_parquet(..., columns=[...], dtypes={...})` recurring options.
- Plotly `layout` fragments.
- Batch-scheduler resource request dicts.
- HTTP client default options.

**Extract to.** A frozen dataclass, `TypedDict`, or Pydantic model in a `config/` or `params/` module. When the config crosses a boundary — parsed from a CLI, loaded from JSON/YAML, or produced by one system and consumed by another — use a Pydantic model so validation, serialization, and CLI binding are uniform.

**Do not flag if.**
- The dicts overlap by accident (e.g., two unrelated functions both happen to use `{"name": ..., "id": ...}`).
- The dicts share keys but values differ semantically at each site (these are call-site overrides, not a shared config).
- The dict is the natural shape of an external library's API (e.g., a `matplotlib.rcParams`-style update); leave inline unless ≥3 sites share the same update.

**Severity defaults.** Medium. Promote to high if config drift between sites has caused or could cause inconsistent behavior on the same input.

---

## Category 4 (STY): Styling and design tokens

**Detect.** Repeated:
- Color hex codes (`#1A2B3C`), named colors (`navy`, `gold`), or RGB/RGBA tuples.
- Font names, font stacks, font sizes.
- Spacing values that look like a design system (e.g., `8`, `16`, `24`, `32` repeated across components).
- Plotly `layout` fragments setting fonts, paper/plot background, gridlines.
- matplotlib `rcParams` assignments.
- Tailwind class clusters appearing in ≥3 sites with the same combination.

**Extract to.**
- A design tokens module (`tokens.py`, `tokens.ts`, or shared JSON consumed by both). Expose semantic names: `BRAND_NAVY`, `OKABE_ITO[0]`, `MONO_FONT_STACK`, `SPACING_LG`.
- Plotly layouts become a `template` registered via `pio.templates`. Reference by name (`fig.update_layout(template="brand")`).
- matplotlib styling becomes a `.mplstyle` file.
- Recurring Tailwind clusters become a component class, a `@apply` rule in a CSS file, or a typed React component.

**Do not flag if.**
- The color is a one-off accent in a single illustrative chart.
- The value looks like a color but is not (`"#define"` in a C-style comment, `#0` in a CSS selector).
- The Tailwind classes happen to overlap but encode different semantic intents (e.g., `flex items-center` is too generic to extract).

**Severity defaults.** Medium for token duplication that crosses files. Low for within-file duplication. High when the same brand color appears with different hex values across sites (drift).

---

## Category 5 (IO): I/O access patterns

**Detect.**
- Multiple call sites opening the same path with the same parser, especially with identical column lists or schemas (`pl.read_parquet(p, columns=["a", "b"])` repeated).
- Repeated path construction (`Path(BASE) / "datasets" / dataset_id / f"{region}.parquet"`).
- Multiple writers to the same logical artifact without a single owner.
- Repeated glob patterns (`"*.parquet"`, `"dataset_*/region_*/values.parquet"`).
- Repeated `open(...)` followed by the same parsing logic.

**Extract to.** A typed accessor function or class that centralizes schema, caching, error handling, and path conventions:

```python
def load_partition(dataset_id: int, region: str) -> pl.DataFrame:
    """Load a single partition. Centralizes path construction, schema,
    and decoding. All readers go through here."""
    ...
```

Where a raw format needs decoding, give it one entry point (`read_raw(path, *, decode, validate)`) and route every caller through the accessor rather than through the underlying library directly.

**Do not flag if.**
- The site is an ad-hoc inspection script or notebook cell that intentionally bypasses the canonical loader.
- The site is a test that exercises the parser directly.
- The paths share a prefix but resolve to different logical artifacts.

**Severity defaults.** High when writers disagree on schema or path convention (data integrity risk). Medium when readers diverge. Low for single-module repetition.

---

## Category 6 (SCH): Schema definitions

**Detect.** Column lists, dtype maps, or Polars/Pandas/Pandera schemas re-declared in multiple readers, writers, or tests. Polars-specific patterns to watch:
- `pl.read_parquet(..., schema={...})` with the same schema at multiple sites.
- `pl.DataFrame({...}).cast({...})` with the same cast map.
- Repeated `.select([...])` with identical column lists.
- Repeated `.with_columns([...])` building the same derived columns.

**Extract to.** A single schema module (`schemas.py`) exporting `Final` schema objects:

```python
RECORD_SCHEMA: Final[Mapping[str, pl.DataType]] = {
    "dataset_id": pl.Int32,
    "region": pl.Categorical,
    "value": pl.Float32,
}
```

Reference by name in all readers and writers. For derived columns, expose a `pl.Expr` factory:

```python
def log_value() -> pl.Expr:
    return pl.col("value").log1p().alias("log_value")
```

**Do not flag if.**
- The schemas are deliberately divergent (a wide vs. long representation of the same data).
- One is a subset of another and the subset is documented as such.

**Severity defaults.** High. Schema drift between reader and writer is one of the most damaging silent bugs in data pipelines.

---

## Category 7 (PLT): Plot and figure construction

**Detect.** Repeated:
- Axis setup (`ax.set_xlabel(...)`, `ax.set_ylabel(...)`, `ax.tick_params(...)`).
- Legend configuration (position, font, frame).
- Font assignments (`fontsize=`, `family=`).
- Colorbar formatting (location, label, tick density).
- Plotly `update_layout(...)` blocks with overlapping kwargs.
- `update_xaxes` / `update_yaxes` blocks repeated across figures.

**Extract to.**
- A Plotly template registered via `pio.templates["brand"] = go.layout.Template(...)`, then `pio.templates.default = "brand"`.
- A matplotlib `.mplstyle` file referenced via `plt.style.use(...)`.
- Small composable helpers: `apply_brand_theme(fig)`, `add_categorical_legend(ax)`, `format_log_axis(ax, which="y")`.

**Do not flag if.**
- The figure is a one-off illustration in a notebook with intentionally bespoke styling.
- The repeated calls operate on different conceptual axes (e.g., a colorbar for an image vs. for a heatmap, with semantically different formatting).

**Severity defaults.** Medium. Promote to high when the same brand element (logo placement, brand color in titles) is duplicated with drift across publication-quality figures.

---

## Category 8 (LOG): Logging patterns

**Detect.**
- Same format strings used in `logger.info(f"...")` or `logger.info("...", extra={...})` calls at ≥2 sites.
- Same context dicts (`extra={"dataset_id": ..., "region": ...}`) attached to log records across functions.
- Repeated `logger = logging.getLogger(__name__)` followed by the same setup (handlers, formatters) at multiple module entry points.

**Extract to.**
- A `LoggerAdapter` or `structlog` binding that pre-fills the recurring context.
- A module-level logger factory: `get_logger(name, **bound)` returning a configured logger.
- The format string itself becomes a `Final[str]` if templated and reused.

**Do not flag if.**
- The format strings differ in any non-cosmetic way.
- The log calls are at different levels (info vs. debug) with deliberately different messaging.
- The context is a one-off debug trace.

**Severity defaults.** Low. Logging duplication is mostly cosmetic; promote to medium only when it indicates a missing observability abstraction (e.g., every function in a pipeline manually attaches the same `dataset_id` to every log line).

---

## Category 9 (TOL): Numeric tolerances and epsilons

**Detect.** Bare `1e-6`, `1e-8`, `1e-3`, etc. used as:
- `atol=` or `rtol=` in `np.isclose`, `np.allclose`, `pytest.approx`, `math.isclose`.
- Convergence criteria in iterative solvers.
- Threshold comparisons (`if abs(x - y) < 1e-6:`).
- Division-by-zero guards (`x / (y + 1e-9)`).

**Extract to.** Named domain constants in a `tolerances.py` or `constants.py` module:

```python
RTOL_UNIT_CONVERSION: Final[float] = 1e-3  # round-trip conversion precision
ATOL_CURVE_FIT: Final[float] = 1e-8        # nonlinear fit residual
EPS_DIVISION_GUARD: Final[float] = 1e-12   # default safe denominator floor
```

The naming convention should reveal which physical or numerical quantity the tolerance bounds.

**Do not flag if.**
- The tolerance is documented inline as required by a specific algorithm (e.g., LAPACK's `gesdd` recommended threshold).
- The value is used once in a self-contained function and the function's docstring states the tolerance.

**Severity defaults.** High. Tolerance drift between sites is a classic source of silent inconsistency in numerical pipelines and should always be auditable from a single location.

---

## Category 10 (FIX): Test fixtures

**Detect.** Setup code repeated across `test_*.py` files:
- Synthesizing the same test arrays or DataFrames.
- Creating the same temp directory structure.
- Mocking the same external services with the same canned responses.
- Loading the same fixture file with the same parser.

**Extract to.** `conftest.py` pytest fixtures, scoped appropriately:
- `scope="session"` for expensive setup (loading a large reference dataset).
- `scope="module"` for moderately expensive setup shared within a file.
- `scope="function"` (default) for mutable fixtures.

For DataFrame fixtures, prefer factory fixtures (a fixture returning a function that builds the DataFrame on demand) over module-level constants. This lets each test mutate freely.

**Do not flag if.**
- The setups are deliberately divergent and exercise different edge cases.
- The duplication is in a single test file and is more readable inline than under a fixture name.

**Severity defaults.** Low (test code; relaxed). Promote to medium when the same mock specification drifts across files (e.g., one test mocks the API to return `{"status": "ok"}`, another mocks it to return `{"status": "OK"}`).

---

## Category 11 (URL): URL and endpoint construction

**Detect.**
- Repeated base URL plus path joining (`f"{BASE_URL}/v1/datasets/{dataset_id}"` repeated at multiple sites).
- Repeated query parameter construction with the same keys.
- Hardcoded URLs that share a base but no constant exists.

**Extract to.**
- A typed client class with the base URL configured once and methods per endpoint.
- A path-building function (`dataset_url(dataset_id: int, region: str) -> str`).
- For HTTP requests, a session object (e.g., `requests.Session` or `httpx.Client`) with `base_url` set once.

**Do not flag if.**
- The URLs are different external services that happen to share a prefix.
- The site is a one-off curl-equivalent in a debugging script.

**Severity defaults.** Medium. Promote to high when URL construction is duplicated across services AND has caused authentication or routing inconsistencies.

---

## Category 12 (RES): Resource lifecycle pairs

**Detect.** Matched open/close, connect/disconnect, acquire/release, begin/commit outside `with` blocks:
- `f = open(...); ...; f.close()` instead of `with open(...) as f:`.
- `conn = create_connection(); ...; conn.close()`.
- `lock.acquire(); ...; lock.release()`.
- `client.start(); ...; client.stop()`.
- Repeated try/finally blocks doing manual cleanup of the same resource type.

**Extract to.** A context manager via `contextlib.contextmanager` or by implementing `__enter__` / `__exit__`:

```python
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

@contextmanager
def job_session(job_spec: dict[str, Any]) -> Iterator[str]:
    handle = submit_job(job_spec)
    try:
        yield handle
    finally:
        cleanup_job(handle)
```

For async resources, use `contextlib.asynccontextmanager` and `async with`.

**Do not flag if.**
- The resource lifecycle spans process boundaries (e.g., a long-lived scheduler job handle that outlives the calling Python process).
- The cleanup intentionally runs only on success or only on failure (not both).
- The open and close calls are on different objects (separate sessions, not lifecycle pairs).

**Severity defaults.** High when the missing context manager could leak resources (open files, network connections, locks). Medium for lighter resources (counters, temporary state).

---

## Cross-cutting application notes

- **Run AST detection before regex.** For all categories except 4 (textual colors and fonts), AST-based matching dramatically reduces false positives.
- **Resolve names before declaring a match.** Two `pl.read_parquet` calls are only the same I/O pattern if the path expression resolves to the same logical artifact. Use `pyright --outputjson` or `jedi` for cross-scope name resolution.
- **Test files**: apply all detectors but cap severity at low unless the finding is structural (Category 10 itself).
- **Cross-language duplication**: scan Python and TypeScript separately, then surface tokens (Category 4), schemas (Category 6), and URLs (Category 11) that appear in both. The fix is usually a single shared source (JSON, YAML, or codegen), not parallel deduplication in each language.
- **Pragma comments**: `# dedupe: ignore`, `# dedupe: ignore-next-line`, `# dedupe: ignore-category=NUM`, file-level `# dedupe: ignore-all`. TypeScript uses `//` form.
