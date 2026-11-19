"""File I/O for :class:`~dfcli.table.Table`.

CSV is handled with the standard library so the core tool works on a bare
Python install. Pandas remains available as an optional export/plot path.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .table import Row, Table


def read_csv(path: str | Path) -> Table:
    source = Path(path).expanduser()
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return Table(columns=(), rows=(), name=source.stem)
        rows = [_coerce_row(header, record) for record in reader if record]
    return Table(columns=tuple(header), rows=tuple(rows), name=source.stem)


def write_csv(table: Table, path: str | Path) -> Path:
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(table.columns)
        for row in table.rows:
            writer.writerow(["" if row[column] is None else row[column] for column in table.columns])
    return destination


def to_dataframe(table: Table):
    """Convert to a pandas DataFrame (imports pandas only when called)."""
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("pandas is required for 'to_dataframe'; pip install pandas") from exc
    return pd.DataFrame(table.to_dicts(), columns=list(table.columns))


def _coerce_row(header: list[str], values: list[str]) -> Row:
    row: Row = {}
    for index, column in enumerate(header):
        raw = values[index] if index < len(values) else ""
        row[column] = _infer(raw)
    return row


def _infer(raw: str) -> object:
    text = raw.strip()
    if text == "":
        return None
    lowered = text.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return raw
