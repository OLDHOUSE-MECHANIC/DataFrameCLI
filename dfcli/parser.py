"""Pipeline parser for the dfcli command language.

Syntax is deliberately shell-like: stages are separated by ``|`` and each
stage is ``command arg1 arg2 ...``. Quotes and escapes are respected so that
expressions such as ``filter city == "New York"`` survive intact.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass


class ParseError(ValueError):
    """Raised for malformed pipelines."""


@dataclass(frozen=True)
class Stage:
    command: str
    args: tuple[str, ...]
    source: str
    expression: str = ""


def split_pipeline(text: str) -> list[str]:
    """Split on unquoted ``|`` characters."""
    stages: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    escaped = False

    for char in text:
        if escaped:
            buffer.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            buffer.append(char)
            continue
        if quote:
            buffer.append(char)
            if char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
            buffer.append(char)
            continue
        if char == "|":
            stages.append("".join(buffer))
            buffer = []
            continue
        buffer.append(char)

    if quote:
        raise ParseError("unterminated quote in pipeline")
    if escaped:
        raise ParseError("trailing backslash in pipeline")
    stages.append("".join(buffer))
    return [stage.strip() for stage in stages if stage.strip()]


def parse_pipeline(text: str) -> list[Stage]:
    stages: list[Stage] = []
    for raw in split_pipeline(text):
        try:
            tokens = shlex.split(raw, comments=False, posix=True)
        except ValueError as exc:
            raise ParseError(f"cannot parse stage {raw!r}: {exc}") from exc
        if not tokens:
            continue
        name, args = tokens[0].lower(), tuple(tokens[1:])
        pieces = raw.split(None, 1)
        expression = pieces[1].strip() if len(pieces) > 1 else ""
        stages.append(Stage(command=name, args=args, source=raw, expression=expression))
    if not stages:
        raise ParseError("empty pipeline")
    return stages
