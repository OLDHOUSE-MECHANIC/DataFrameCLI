"""Command implementations and the registry that backs the parser."""

from __future__ import annotations

from typing import Callable

from . import ops
from .io import read_csv, write_csv
from .plots import render_plot
from .table import Table

Handler = Callable[["Session", tuple[str, ...]], None]  # type: ignore[name-defined]
_REGISTRY: dict[str, tuple[Handler, str]] = {}


class CommandError(Exception):
    """A user-facing error raised by a command."""


def register(name: str, help_text: str) -> Callable[[Handler], Handler]:
    def decorator(handler: Handler) -> Handler:
        _REGISTRY[name] = (handler, help_text)
        return handler

    return decorator


def get(name: str) -> tuple[Handler, str] | None:
    return _REGISTRY.get(name)


def all_commands() -> dict[str, str]:
    return {name: help_text for name, (_, help_text) in sorted(_REGISTRY.items())}


def run_command(session: "Session", name: str, args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    entry = get(name)
    if entry is None:
        raise CommandError(f"unknown command {name!r}; try 'help'")
    handler, _ = entry
    handler(session, args)


def _current(session: "Session") -> Table:  # type: ignore[name-defined]
    if session.current is None:
        raise CommandError("no table loaded; use 'load FILE.csv' first")
    return session.current


def _update(session: "Session", table: Table, code: str) -> None:  # type: ignore[name-defined]
    session.replace_current(table, code)


def _assignment(token: str) -> tuple[str, str]:
    """Split ``name=value`` without breaking ``==``, ``>=``, ``!=`` etc."""
    for index, char in enumerate(token):
        if char != "=":
            continue
        before = token[index - 1] if index else ""
        after = token[index + 1] if index + 1 < len(token) else ""
        if before in "=!<>":
            continue
        if after == "=":
            continue
        return token[:index], token[index + 1 :]
    raise CommandError(f"expected name=value, got {token!r}")


# ---------------------------------------------------------------------------
# I/O and introspection
# ---------------------------------------------------------------------------
@register("load", "load FILE.csv [as NAME]")
def cmd_load(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not args:
        raise CommandError("usage: load FILE.csv [as NAME]")
    path = args[0]
    name = args[2] if len(args) > 2 and args[1] == "as" else path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    table = read_csv(path)
    session.set_table(name, table, f'df = pd.read_csv("{path}")')
    session.emit(f"loaded {path} as '{name}' -> {table.shape[0]} rows, {table.shape[1]} columns")


@register("save", "save FILE.csv")
def cmd_save(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not args:
        raise CommandError("usage: save FILE.csv")
    destination = write_csv(_current(session), args[0])
    session.emit(f"saved {destination}")
    session.code.append(f'df.to_csv("{destination}")')


@register("show", "show [N] - print the current table")
def cmd_show(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    try:
        limit = int(args[0]) if args else 20
    except ValueError as exc:
        raise CommandError("show expects an integer row limit") from exc
    session.emit(_current(session).to_text(limit=limit))


@register("info", "print shape, columns, and inferred types")
def cmd_info(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    table = _current(session)
    types = {column: _column_type(table, column) for column in table.columns}
    session.emit(f"table: {table.name}\nshape: {table.shape[0]} rows x {table.shape[1]} columns")
    session.emit("columns:\n" + "\n".join(f"  {name}: {kind}" for name, kind in types.items()))


@register("list", "list loaded tables")
def cmd_list(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not session.tables:
        session.emit("no tables loaded")
        return
    lines = [f"{name}  {table.shape[0]}x{table.shape[1]}" + ("  <- current" if name == session.current_name else "")
             for name, table in sorted(session.tables.items())]
    session.emit("\n".join(lines))


@register("use", "use NAME - switch the current table")
def cmd_use(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if len(args) != 1:
        raise CommandError("usage: use NAME")
    name = args[0]
    if name not in session.tables:
        raise CommandError(f"unknown table {name!r}")
    session.current_name = name
    session.current = session.tables[name]
    session.history.append(f"use {name}")
    session.emit(f"now using '{name}'")


# ---------------------------------------------------------------------------
# Transformations
# ---------------------------------------------------------------------------
@register("select", "select COL [COL ...]")
def cmd_select(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not args:
        raise CommandError("usage: select COL [COL ...]")
    _update(session, ops.select(_current(session), args), f"df = df[{list(args)}]")


@register("filter", "filter EXPR - e.g. filter amount > 100 and region == 'West'")
def cmd_filter(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    stage = getattr(session, "current_stage", None)
    expression = stage.expression if stage and stage.expression else " ".join(args)
    if not expression:
        raise CommandError("usage: filter EXPR")
    _update(session, ops.filter_rows(_current(session), expression), f"df = df.query({expression!r})")


@register("add", "add NAME=EXPR - create a computed column")
def cmd_add(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    stage = getattr(session, "current_stage", None)
    source = stage.expression if stage and stage.expression else " ".join(args)
    name, expression = _assignment(source)
    _update(
        session,
        ops.add_column(_current(session), name, expression),
        f'df["{name}"] = {expression}',
    )


@register("set", "set NAME=EXPR - overwrite a column")
def cmd_set(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    stage = getattr(session, "current_stage", None)
    source = stage.expression if stage and stage.expression else " ".join(args)
    name, expression = _assignment(source)
    _update(
        session,
        ops.set_column(_current(session), name, expression),
        f'df["{name}"] = {expression}',
    )


@register("drop", "drop COL [COL ...]")
def cmd_drop(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not args:
        raise CommandError("usage: drop COL [COL ...]")
    _update(session, ops.drop_columns(_current(session), args), f"df = df.drop(columns={list(args)})")


@register("rename", "rename OLD=NEW [OLD=NEW ...]")
def cmd_rename(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    pairs = [_assignment(token) for token in args]
    if not pairs:
        raise CommandError("usage: rename OLD=NEW [OLD=NEW ...]")
    _update(session, ops.rename_columns(_current(session), pairs), f"df = df.rename(columns={dict(pairs)})")


@register("sort", "sort COL [--desc]")
def cmd_sort(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    descending = bool(args) and args[-1] in {"--desc", "-d"}
    columns = [arg for arg in args if arg not in {"--desc", "-d"}]
    if len(columns) != 1:
        raise CommandError("usage: sort COL [--desc]")
    _update(
        session,
        ops.sort_rows(_current(session), columns[0], descending=descending),
        f'df = df.sort_values("{columns[0]}", ascending={not descending})',
    )


@register("head", "head [N] - keep the first N rows")
def cmd_head(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    count = _positive_int(args, 5)
    _update(session, ops.head(_current(session), count), f"df = df.head({count})")


@register("tail", "tail [N] - keep the last N rows")
def cmd_tail(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    count = _positive_int(args, 5)
    _update(session, ops.tail(_current(session), count), f"df = df.tail({count})")


@register("distinct", "distinct [COL ...] - drop duplicate rows")
def cmd_distinct(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    columns = args or None
    _update(
        session,
        ops.distinct(_current(session), columns),
        f"df = df.drop_duplicates(subset={list(columns) if columns else None})",
    )


@register("groupby", "groupby COL FUNC:COL[:ALIAS] ... - e.g. groupby region sum:amount count:id")
def cmd_groupby(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if len(args) < 2:
        raise CommandError("usage: groupby COL FUNC:COL[:ALIAS] ...")
    key, *specs = args
    parsed: list[tuple[str, str, str | None]] = []
    for token in specs:
        parts = token.replace("(", ":").replace(")", "").split(":")
        if len(parts) not in {2, 3}:
            raise CommandError(f"bad aggregation {token!r}; expected FUNC:COL[:ALIAS]")
        parsed.append((parts[0], parts[1], parts[2] if len(parts) == 3 else None))
    table = ops.group_by(_current(session), key, parsed)
    rendered = ", ".join(f'"{alias or f"{func}_{col}"}": ("{func}", "{col}")' for func, col, alias in parsed)
    _update(session, table, f"df = df.groupby(\"{key}\").agg({{{rendered}}})")


@register("plot", "plot bar|line|... [X] [Y] [--out FILE.png]")
def cmd_plot(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not args:
        raise CommandError("usage: plot bar|line|scatter|hist|area|box [X] [Y] [--out FILE.png]")
    out = "dfcli-plot.png"
    if "--out" in args:
        index = args.index("--out")
        if index + 1 >= len(args):
            raise CommandError("--out needs a filename")
        out = args[index + 1]
        args = args[:index] + args[index + 2 :]
    kind, *rest = args
    x, y = (rest + [None, None])[:2]
    destination = render_plot(_current(session), kind, x, y, out)
    session.emit(f"wrote {destination}")
    session.code.append(f'df.plot(kind="{kind}", x={x!r}, y={y!r}).figure.savefig("{destination}")')


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------
@register("explain", "print the pandas equivalent of this session")
def cmd_explain(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    session.emit("\n".join(session.code) if session.code else "# nothing has changed the table yet")


@register("history", "print commands run in this session")
def cmd_history(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if not session.history:
        session.emit("no commands yet")
        return
    session.emit("\n".join(f"{index:>3}  {command}" for index, command in enumerate(session.history, 1)))


@register("undo", "revert the last table-changing command")
def cmd_undo(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    if session.undo():
        session.emit(f"undone; current table is '{session.current_name}'")
    else:
        session.emit("nothing to undo")


@register("help", "help [COMMAND] - list commands or show one")
def cmd_help(session: "Session", args: tuple[str, ...]) -> None:  # type: ignore[name-defined]
    commands = all_commands()
    if args:
        name = args[0]
        if name not in commands:
            raise CommandError(f"unknown command {name!r}")
        session.emit(f"{name:10} {commands[name]}")
        return
    lines = [f"{name:10} {help_text}" for name, help_text in commands.items()]
    session.emit("COMMANDS\n" + "\n".join(lines) + "\n\nUse | to chain stages:\n  filter amount > 10 | groupby region sum:amount | save out.csv")


def _positive_int(args: tuple[str, ...], default: int) -> int:
    if not args:
        return default
    try:
        value = int(args[0])
    except ValueError as exc:
        raise CommandError(f"expected an integer, got {args[0]!r}") from exc
    if value < 0:
        raise CommandError("count cannot be negative")
    return value


def _column_type(table: Table, column: str) -> str:
    values = [row[column] for row in table.rows if row[column] is not None]
    if not values:
        return "null"
    if all(isinstance(value, bool) for value in values):
        return "bool"
    if all(isinstance(value, int) for value in values):
        return "int"
    if all(isinstance(value, (int, float)) for value in values):
        return "float"
    return "str"
