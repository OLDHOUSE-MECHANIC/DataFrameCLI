"""Session state: current table, named tables, history, code trace, and undo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import commands
from .parser import Stage, parse_pipeline
from .table import Table


class SessionError(Exception):
    """Raised when a pipeline cannot be executed."""


@dataclass
class Session:
    tables: dict[str, Table] = field(default_factory=dict)
    current_name: str | None = None
    current: Table | None = None
    history: list[str] = field(default_factory=list)
    code: list[str] = field(default_factory=list)
    output: list[str] = field(default_factory=list)
    current_stage: Stage | None = None
    _undo_stack: list[tuple[str | None, Table | None, list[str]]] = field(default_factory=list)

    # -- output -------------------------------------------------------
    def emit(self, text: str) -> None:
        self.output.append(str(text))

    def drain_output(self) -> str:
        text = "\n".join(self.output)
        self.output.clear()
        return text

    # -- state --------------------------------------------------------
    def require_current(self) -> Table:
        if self.current is None:
            raise commands.CommandError("no table loaded; use 'load FILE.csv' first")
        return self.current

    def set_table(
        self,
        name: str,
        table: Table,
        code_line: str | None = None,
        *,
        record_undo: bool = True,
    ) -> None:
        if record_undo:
            self._push_undo()
        self.tables[name] = table
        self.current_name = name
        self.current = table
        if code_line:
            self.code.append(code_line)

    def replace_current(self, table: Table, code_line: str | None = None) -> None:
        if self.current_name is None:
            raise commands.CommandError("no current table")
        self.set_table(self.current_name, table, code_line)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        name, table, code = self._undo_stack.pop()
        self.current_name = name
        self.current = table
        self.code = code
        return True

    def _push_undo(self) -> None:
        self._undo_stack.append((self.current_name, self.current, list(self.code)))

    # -- execution ----------------------------------------------------
    def execute_stage(self, stage: Stage) -> None:
        self.current_stage = stage
        try:
            commands.run_command(self, stage.command, stage.args)
            self.history.append(stage.source)
        except commands.CommandError as exc:
            raise SessionError(f"{stage.command}: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - user-facing CLI, convert to a clean error
            raise SessionError(f"{stage.command}: {exc}") from exc

    def execute(self, text: str) -> str:
        """Run a whole pipeline and return everything it printed."""
        for stage in parse_pipeline(text):
            self.execute_stage(stage)
        return self.drain_output()

    def snapshot(self) -> dict[str, Any]:
        return {
            "current": self.current_name,
            "tables": list(self.tables),
            "history": list(self.history),
            "code": list(self.code),
        }
