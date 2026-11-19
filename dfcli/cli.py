"""Command-line entry point for dfcli."""

from __future__ import annotations

import argparse
import sys

from . import __version__, commands
from .session import Session, SessionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dfcli",
        description="A small, scriptable CLI for tabular data. Chain stages with '|'.",
    )
    parser.add_argument("--version", action="version", version=f"dfcli {__version__}")
    sub = parser.add_subparsers(dest="action", required=True)

    run = sub.add_parser("run", help="execute a pipeline")
    run.add_argument("pipeline", nargs="?", help="pipeline string; reads stdin when omitted")

    sub.add_parser("repl", help="interactive session")

    sub.add_parser("commands", help="list available commands")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    session = Session()

    if args.action == "commands":
        for name, help_text in commands.all_commands().items():
            print(f"{name:10} {help_text}")
        return 0

    if args.action == "run":
        pipeline = args.pipeline if args.pipeline is not None else sys.stdin.read()
        if not pipeline.strip():
            print("error: empty pipeline", file=sys.stderr)
            return 2
        try:
            output = session.execute(pipeline)
        except SessionError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if output:
            print(output)
        return 0

    if args.action == "repl":
        return _repl(session)

    return 2


def _repl(session: Session) -> int:
    print("dfcli REPL - type 'help', 'exit', or a pipeline.")
    while True:
        try:
            line = input("dfcli> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line.lower() in {"exit", "quit"}:
            return 0
        if not line:
            continue
        try:
            output = session.execute(line)
        except SessionError as exc:
            print(f"error: {exc}")
            continue
        if output:
            print(output)
