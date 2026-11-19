"""Backend-neutral table representation.

A :class:`Table` is intentionally tiny: column names plus a tuple of row
mappings. Every operation returns a *new* Table, which is what makes undo and
script replay possible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


Row = dict[str, Any]


@dataclass(frozen=True)
class Table:
    columns: tuple[str, ...]
    rows: tuple[Row, ...] = field(default_factory=tuple)
    name: str = "<unnamed>"

    # -- constructors -------------------------------------------------
    @classmethod
    def from_records(
        cls,
        rows: Iterable[Mapping[str, Any]],
        columns: Iterable[str] | None = None,
        *,
        name: str = "<unnamed>",
    ) -> "Table":
        records = [dict(row) for row in rows]
        if columns is None:
            seen: list[str] = []
            for record in records:
                for key in record:
                    if key not in seen:
                        seen.append(key)
            cols = tuple(seen)
        else:
            cols = tuple(columns)
        normalised = tuple({col: record.get(col) for col in cols} for record in records)
        return cls(columns=cols, rows=normalised, name=name)

    # -- introspection ------------------------------------------------
    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.rows), len(self.columns))

    def has(self, column: str) -> bool:
        return column in self.columns

    def require(self, *columns: str) -> None:
        missing = [column for column in columns if column not in self.columns]
        if missing:
            raise KeyError(f"unknown column(s): {', '.join(missing)}")

    # -- rendering ----------------------------------------------------
    def to_text(self, limit: int | None = 20) -> str:
        """Render an aligned plain-text table (no third-party dependency)."""
        if not self.columns:
            return "(no columns)"

        shown = self.rows if limit is None else self.rows[:limit]
        header = [str(column) for column in self.columns]
        body = [[_fmt(row.get(column)) for column in self.columns] for row in shown]

        widths = [len(text) for text in header]
        for record in body:
            for index, text in enumerate(record):
                widths[index] = max(widths[index], len(text))

        def line(values: list[str]) -> str:
            return "  ".join(text.ljust(widths[i]) for i, text in enumerate(values)).rstrip()

        parts = [line(header), line(["-" * width for width in widths])]
        parts.extend(line(record) for record in body)
        if limit is not None and len(self.rows) > limit:
            parts.append(f"... {len(self.rows) - limit} more row(s)")
        parts.append(f"[{len(self.rows)} rows x {len(self.columns)} columns]")
        return "\n".join(parts)

    def to_dicts(self) -> list[Row]:
        return [dict(row) for row in self.rows]

    def replace(
        self,
        *,
        columns: Iterable[str] | None = None,
        rows: Iterable[Mapping[str, Any]] | None = None,
        name: str | None = None,
    ) -> "Table":
        return Table(
            columns=tuple(columns) if columns is not None else self.columns,
            rows=tuple(dict(row) for row in rows) if rows is not None else self.rows,
            name=self.name if name is None else name,
        )


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
