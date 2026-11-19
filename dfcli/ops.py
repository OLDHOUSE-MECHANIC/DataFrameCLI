"""Pure table operations.

Every function takes a :class:`~dfcli.table.Table` and returns a new one. That
single rule gives us undo, replay, and testability for free.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .expr import evaluate, parse
from .table import Row, Table

AGGREGATIONS = {"sum", "count", "mean", "min", "max"}


def select(table: Table, columns: Iterable[str]) -> Table:
    columns = tuple(columns)
    table.require(*columns)
    return table.replace(
        columns=columns,
        rows=({column: row[column] for column in columns} for row in table.rows),
    )


def filter_rows(table: Table, source: str) -> Table:
    tree = parse(source)
    return table.replace(
        rows=(row for row in table.rows if bool(evaluate(tree, row)))
    )


def add_column(table: Table, name: str, source: str) -> Table:
    tree = parse(source)
    if name in table.columns:
        raise ValueError(f"column {name!r} already exists; use 'set' to overwrite")
    rows: list[Row] = []
    for row in table.rows:
        new = dict(row)
        new[name] = evaluate(tree, row)
        rows.append(new)
    return table.replace(columns=(*table.columns, name), rows=rows)


def set_column(table: Table, name: str, source: str) -> Table:
    tree = parse(source)
    if name not in table.columns:
        raise KeyError(f"unknown column {name!r}; use 'add' to create it")
    rows: list[Row] = []
    for row in table.rows:
        new = dict(row)
        new[name] = evaluate(tree, row)
        rows.append(new)
    return table.replace(rows=rows)


def drop_columns(table: Table, columns: Iterable[str]) -> Table:
    dropped = set(columns)
    table.require(*dropped)
    kept = tuple(column for column in table.columns if column not in dropped)
    return table.replace(
        columns=kept,
        rows=({column: row[column] for column in kept} for row in table.rows),
    )


def rename_columns(table: Table, pairs: Iterable[tuple[str, str]]) -> Table:
    mapping = dict(pairs)
    table.require(*mapping)
    columns = tuple(mapping.get(column, column) for column in table.columns)
    return table.replace(
        columns=columns,
        rows=({mapping.get(column, column): value for column, value in row.items()} for row in table.rows),
    )


def sort_rows(table: Table, key: str, *, descending: bool = False) -> Table:
    table.require(key)

    def sort_value(row: Row) -> Any:
        value = row[key]
        if value is None:
            return (0, 0)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return (1, value)
        return (2, str(value))

    return table.replace(rows=sorted(table.rows, key=sort_value, reverse=descending))


def head(table: Table, count: int = 5) -> Table:
    return table.replace(rows=table.rows[:max(0, count)])


def tail(table: Table, count: int = 5) -> Table:
    return table.replace(rows=table.rows[-max(0, count):] if count else ())


def distinct(table: Table, columns: Iterable[str] | None = None) -> Table:
    keys = tuple(columns) if columns is not None else table.columns
    table.require(*keys)
    seen: set[tuple[Any, ...]] = set()
    rows: list[Row] = []
    for row in table.rows:
        signature = tuple(row[column] for column in keys)
        if signature not in seen:
            seen.add(signature)
            rows.append(row)
    return table.replace(rows=rows)


def group_by(
    table: Table,
    key: str,
    aggregations: Iterable[tuple[str, str, str | None]],
) -> Table:
    """Group by *key* and apply ``(func, column, alias)`` aggregations."""
    table.require(key)
    specs = list(aggregations)
    for function, column, _ in specs:
        if function not in AGGREGATIONS:
            raise ValueError(
                f"unknown aggregation {function!r}; choose from {', '.join(sorted(AGGREGATIONS))}"
            )
        table.require(column)

    buckets: dict[Any, list[Row]] = defaultdict(list)
    for row in table.rows:
        buckets[row[key]].append(row)

    aliases = [alias or f"{function}_{column}" for function, column, alias in specs]
    columns = (key, *aliases)
    rows: list[Row] = []
    for group in buckets.values():
        record: Row = {key: group[0][key]}
        for (function, column, _), alias in zip(specs, aliases):
            values = [row[column] for row in group if row[column] is not None]
            record[alias] = _aggregate(function, values)
        rows.append(record)
    return Table(columns=columns, rows=tuple(rows), name=f"{table.name}:grouped")


def _aggregate(function: str, values: list[Any]) -> Any:
    if function == "count":
        return len(values)
    if not values:
        return None
    if function == "sum":
        return sum(_number(value) for value in values)
    if function == "mean":
        return sum(_number(value) for value in values) / len(values)
    if function == "min":
        return min(_number(value) for value in values)
    if function == "max":
        return max(_number(value) for value in values)
    raise ValueError(function)


def _number(value: Any) -> int | float:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)
    except ValueError:
        return float(value)
