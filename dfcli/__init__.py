"""dfcli - a small, scriptable tabular data CLI.

The project deliberately keeps a backend-neutral core: data is represented as
plain columns + rows, and pandas is only used at the edges (export / plotting).
That keeps the command language testable without a heavy install and leaves the
door open for Polars or DuckDB backends later.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
