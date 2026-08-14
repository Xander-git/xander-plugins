# Refactor templates

Use these templates when drafting the `refactor_sketch` field of a finding. Each template is syntactically valid and intended to be pasted into the codebase with minimal adaptation.

Pick the template that matches the finding's category and use case. When in doubt, prefer the more conservative template (e.g., `Final[str]` over `StrEnum` when the value is a true singleton).

Templates use a neutral running example — a tabular pipeline over records keyed by `dataset_id` and `region`, with a numeric `value` column. Rename to the target codebase's own domain nouns when drafting a sketch; the shapes are what matter, not the names.

`<pkg>` appears in path comments as a placeholder for the target package. Import statements use a concrete name (`mypkg`) instead, so every block below parses as valid Python.

---

## STR (string literals in closed sets)

### Singleton: `Final[str]` constant

For a single fixed value reused for its meaning (config key, header name, sentinel).

```python
# src/<pkg>/constants.py
from typing import Final

DEFAULT_USER_AGENT: Final[str] = "<pkg>/1.0"
RECORD_LABEL_COL: Final[str] = "record_id"
```

### Closed enumeration: `StrEnum` plus public-facing `Literal`

For dispatch and closed sets that interop with strings (CLI, JSON, file formats). Python 3.11+.

```python
# src/<pkg>/types.py
from enum import StrEnum
from typing import Literal, TypeAlias

class Mode(StrEnum):
    FAST = "fast"
    ACCURATE = "accurate"

ModeInput: TypeAlias = Mode | Literal["fast", "accurate"]
```

```python
# src/<pkg>/process.py
from .types import Mode, ModeInput

def process(data: NDArray, mode: ModeInput = "fast") -> Result:
    mode = Mode(mode)   # boundary normalization; idempotent on Mode
    # internal code uses Mode.FAST / Mode.ACCURATE only
    ...
```

Consistency test (recommended when both `Enum` and `Literal` exist):

```python
# tests/test_types_consistency.py
from typing import get_args
from mypkg.types import Mode, ModeInput

def test_mode_input_matches_enum() -> None:
    literal_args = get_args(get_args(ModeInput)[1])
    assert set(literal_args) == {m.value for m in Mode}
```

### Pure type-check enumeration: `Literal` alias alone

When the set is enforced statically only, with no runtime dispatch.

```python
from typing import Literal, TypeAlias

Channel: TypeAlias = Literal["red", "green", "blue"]
```

---

## NUM (magic numbers)

### Single constant with units in the name

```python
from typing import Final

SMOOTHING_WINDOW_SAMPLES: Final[int] = 32
MIN_SEGMENT_LENGTH_PX: Final[int] = 50
OUTLIER_Z_THRESHOLD: Final[float] = 2.3
```

### Grouped constants via frozen dataclass

When constants are conceptually a unit and tend to change together.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SmoothingParams:
    window_samples: int = 32
    polyorder: int = 3
    edge_mode: str = "reflect"

DEFAULT_SMOOTHING: SmoothingParams = SmoothingParams()
```

---

## CFG (shared configuration dicts)

### Frozen dataclass for typed config

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ParquetReadOptions:
    columns: tuple[str, ...]
    use_pyarrow: bool = True
    low_memory: bool = False
    n_rows: int | None = None

RECORD_READ_OPTIONS: ParquetReadOptions = ParquetReadOptions(
    columns=("dataset_id", "region", "value"),
)
```

### TypedDict when call sites want `**kwargs` style

```python
from typing import TypedDict, NotRequired

class ParquetReadOptions(TypedDict):
    columns: list[str]
    use_pyarrow: NotRequired[bool]
    low_memory: NotRequired[bool]

RECORD_READ_OPTIONS: ParquetReadOptions = {
    "columns": ["dataset_id", "region", "value"],
    "use_pyarrow": True,
}

# call sites:
df = pl.read_parquet(path, **RECORD_READ_OPTIONS)
```

### Pydantic model when config crosses a boundary (CLI, JSON, API)

```python
from pydantic import BaseModel, Field

class SmoothingParams(BaseModel):
    model_config = {"frozen": True}

    window_samples: int = Field(default=32, gt=0)
    polyorder: int = Field(default=3, ge=0)
    outlier_z_threshold: float = Field(default=2.3, ge=0)
```

---

## STY (styling and design tokens)

### Python tokens module

```python
# src/<pkg>/viz/tokens.py
from typing import Final

# Brand palette
BRAND_NAVY: Final[str] = "#0A2540"
BRAND_GOLD: Final[str] = "#C9A961"

# Okabe-Ito categorical palette (colorblind-safe)
OKABE_ITO: Final[tuple[str, ...]] = (
    "#000000", "#E69F00", "#56B4E9", "#009E73",
    "#F0E442", "#0072B2", "#D55E00", "#CC79A7",
)

# Typography
SANS_STACK: Final[str] = "DM Sans, system-ui, sans-serif"
MONO_STACK: Final[str] = "DM Mono, ui-monospace, monospace"
```

### Plotly template

```python
# src/<pkg>/viz/plotly_template.py
import plotly.graph_objects as go
import plotly.io as pio
from .tokens import BRAND_NAVY, OKABE_ITO, SANS_STACK

pio.templates["brand"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family=SANS_STACK, size=12, color=BRAND_NAVY),
        colorway=list(OKABE_ITO),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
)
pio.templates.default = "brand"
```

### TypeScript tokens (cross-language sharing)

```typescript
// src/dashboard/tokens.ts
export const BRAND_NAVY = "#0A2540" as const;
export const BRAND_GOLD = "#C9A961" as const;
export const OKABE_ITO = [
  "#000000", "#E69F00", "#56B4E9", "#009E73",
  "#F0E442", "#0072B2", "#D55E00", "#CC79A7",
] as const;
```

Where Python and TypeScript share tokens, prefer a single source (JSON or YAML) with codegen into both:

```json
// tokens/tokens.json
{
  "brand": { "navy": "#0A2540", "gold": "#C9A961" },
  "categorical": { "okabe_ito": ["#000000", "#E69F00", "..."] }
}
```

---

## IO (I/O access patterns)

### Typed accessor function

```python
# src/<pkg>/io.py
from pathlib import Path
import polars as pl
from typing import Final

_DATA_ROOT: Final[Path] = Path("/data/<pkg>")

def load_partition(dataset_id: int, region: str) -> pl.DataFrame:
    """Load a single partition. Single source of truth for path
    construction, schema, and decoding.

    Args:
        dataset_id: Dataset identifier.
        region: Partition key.

    Returns:
        DataFrame conforming to RECORD_SCHEMA.

    Raises:
        FileNotFoundError: If the partition does not exist.
    """
    path = _DATA_ROOT / f"dataset_{dataset_id:04d}" / f"{region}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    return pl.read_parquet(path, columns=list(RECORD_SCHEMA))
```

### Path builder

```python
from pathlib import Path
from typing import Final

_DATA_ROOT: Final[Path] = Path("/data/<pkg>")

def partition_path(dataset_id: int, region: str, *, suffix: str = ".parquet") -> Path:
    return _DATA_ROOT / f"dataset_{dataset_id:04d}" / f"{region}{suffix}"
```

---

## SCH (schema definitions)

### Polars schema as `Final` mapping

```python
# src/<pkg>/schemas.py
from typing import Final, Mapping
import polars as pl

RECORD_SCHEMA: Final[Mapping[str, pl.DataType]] = {
    "dataset_id": pl.Int32,
    "region": pl.Categorical,
    "channel": pl.Categorical,
    "value": pl.Float32,
    "timestamp": pl.Datetime("us"),
}

RECORD_COLUMNS: Final[tuple[str, ...]] = tuple(RECORD_SCHEMA.keys())
```

### Polars expression factories

```python
# src/<pkg>/expressions.py
import polars as pl

def log_value() -> pl.Expr:
    return pl.col("value").log1p().alias("log_value")

def normalized_value(baseline: float) -> pl.Expr:
    return ((pl.col("value") - baseline) / baseline).alias("norm_value")
```

### Pandera schema for validation at boundaries

```python
import pandera.polars as pa

class RecordSchema(pa.DataFrameModel):
    dataset_id: int = pa.Field(ge=0)
    region: str = pa.Field(str_matches=r"^[a-z]{2}-[a-z]+-\d$")
    value: float = pa.Field(ge=0)

    class Config:
        strict = True
```

---

## PLT (plot and figure construction)

### Composable helpers

```python
# src/<pkg>/viz/helpers.py
import matplotlib.pyplot as plt
from .tokens import BRAND_NAVY, OKABE_ITO

def apply_brand_theme(ax: plt.Axes) -> None:
    """Apply brand styling in-place."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=BRAND_NAVY)
    for label in (ax.xaxis.label, ax.yaxis.label, ax.title):
        label.set_color(BRAND_NAVY)

def format_log_axis(ax: plt.Axes, which: str = "y") -> None:
    """Apply consistent log-axis formatting."""
    if which == "y":
        ax.set_yscale("log")
    else:
        ax.set_xscale("log")
    ax.grid(True, which="both", alpha=0.3)
```

### Matplotlib style file

```ini
; src/<pkg>/viz/brand.mplstyle
axes.spines.top: False
axes.spines.right: False
axes.labelcolor: "#0A2540"
axes.edgecolor: "#0A2540"
font.family: DM Sans
font.size: 11
figure.dpi: 120
```

```python
import matplotlib.pyplot as plt
from importlib.resources import files

plt.style.use(files("<pkg>.viz") / "brand.mplstyle")
```

---

## LOG (logging patterns)

### Module logger factory

```python
# src/<pkg>/logging.py
import logging
from typing import Any

def get_logger(name: str, **bound: Any) -> logging.LoggerAdapter:
    base = logging.getLogger(name)
    return logging.LoggerAdapter(base, bound)
```

```python
# usage
log = get_logger(__name__, dataset_id=dataset_id)
log.info("started processing region %s", region)
# all messages from this logger include dataset_id in extras
```

### structlog binding (preferred for structured logs)

```python
import structlog

def get_logger(**bound: Any) -> structlog.BoundLogger:
    return structlog.get_logger().bind(**bound)

log = get_logger(dataset_id=dataset_id, region=region)
log.info("processing_started")
```

### Format string constant

```python
from typing import Final

PROGRESS_FMT: Final[str] = "processed %d/%d partitions in %.2fs"

log.info(PROGRESS_FMT, done, total, elapsed)
```

---

## TOL (numeric tolerances and epsilons)

### Named tolerance constants

```python
# src/<pkg>/tolerances.py
from typing import Final

RTOL_UNIT_CONVERSION: Final[float] = 1e-3   # round-trip conversion precision
ATOL_CURVE_FIT: Final[float] = 1e-8         # nonlinear fit residual
RTOL_NORMALIZATION: Final[float] = 1e-4     # iterative normalization convergence
EPS_DIVISION_GUARD: Final[float] = 1e-12    # safe denominator floor
```

```python
# usage
from .tolerances import RTOL_UNIT_CONVERSION
if np.allclose(predicted, observed, rtol=RTOL_UNIT_CONVERSION):
    ...
```

Derive each tolerance from a mechanism — accumulated floating-point error over N operations, a documented solver criterion, an instrument's stated precision — and record that reasoning in the trailing comment. A tolerance chosen by guessing is a finding in its own right.

---

## FIX (test fixtures)

### conftest.py shared fixtures

```python
# tests/conftest.py
from collections.abc import Callable
import numpy as np
import polars as pl
import pytest

@pytest.fixture(scope="session")
def synthetic_grid() -> np.ndarray:
    """One 8x12 grid of synthetic values."""
    rng = np.random.default_rng(seed=0)
    return rng.uniform(0, 1, size=(8, 12)).astype(np.float32)

@pytest.fixture
def make_record_df() -> Callable[[int], pl.DataFrame]:
    """Factory fixture for record DataFrames. Each test gets a fresh,
    mutable copy."""
    def _make(n_rows: int = 96) -> pl.DataFrame:
        return pl.DataFrame({
            "dataset_id": [1] * n_rows,
            "region": [f"r{i:03d}" for i in range(n_rows)],
            "value": np.linspace(0, 1, n_rows, dtype=np.float32),
        })
    return _make
```

---

## URL (URL and endpoint construction)

### Typed client class

```python
# src/<pkg>/api.py
import httpx
from typing import Final

_BASE_URL: Final[str] = "https://api.example.com/v1"

class DatasetClient:
    def __init__(self, *, token: str, base_url: str = _BASE_URL) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    def get_dataset(self, dataset_id: int) -> dict:
        r = self._client.get(f"/datasets/{dataset_id}")
        r.raise_for_status()
        return r.json()

    def list_regions(self, dataset_id: int, *, channel: str | None = None) -> list[dict]:
        params = {"channel": channel} if channel else {}
        r = self._client.get(f"/datasets/{dataset_id}/regions", params=params)
        r.raise_for_status()
        return r.json()
```

### Path-builder function (when a client is overkill)

```python
from typing import Final
from urllib.parse import urlencode

_BASE_URL: Final[str] = "https://api.example.com/v1"

def dataset_url(dataset_id: int, **query: str) -> str:
    base = f"{_BASE_URL}/datasets/{dataset_id}"
    return f"{base}?{urlencode(query)}" if query else base
```

---

## RES (resource lifecycle pairs)

### contextmanager decorator

```python
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any

@contextmanager
def job_session(job_spec: dict[str, Any]) -> Iterator[str]:
    """Submit a batch job and ensure cleanup on exit."""
    job_id = submit_job(job_spec)
    try:
        yield job_id
    finally:
        cleanup_job(job_id)
```

### Class-based context manager

```python
from types import TracebackType

class DatabaseSession:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn = None

    def __enter__(self) -> "DatabaseSession":
        self._conn = connect(self._dsn)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
```

### Async variant

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def http_session(base_url: str) -> AsyncIterator[httpx.AsyncClient]:
    client = httpx.AsyncClient(base_url=base_url)
    try:
        yield client
    finally:
        await client.aclose()
```
