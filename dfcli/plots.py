"""Optional plotting support (pandas + matplotlib imported only when used)."""

from __future__ import annotations

from pathlib import Path

from .io import to_dataframe
from .table import Table


def render_plot(table: Table, kind: str, x: str | None, y: str | None, out: str) -> Path:
    if kind not in {"bar", "line", "scatter", "hist", "area", "box"}:
        raise ValueError(f"unsupported plot type {kind!r}")

    frame = to_dataframe(table)
    x_column = x or (frame.columns[0] if len(frame.columns) else None)
    y_column = y or (frame.columns[1] if len(frame.columns) > 1 else None)

    if x_column is not None and x_column not in frame.columns:
        raise KeyError(f"unknown column {x_column!r}")
    if y_column is not None and y_column not in frame.columns:
        raise KeyError(f"unknown column {y_column!r}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("plotting requires matplotlib; pip install matplotlib") from exc

    axes = frame.plot(kind=kind, x=x_column, y=y_column)
    axes.set_title(f"{kind.title()} plot - {table.name}")
    figure = axes.get_figure()
    destination = Path(out).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=140, bbox_inches="tight")
    plt.close(figure)
    return destination
