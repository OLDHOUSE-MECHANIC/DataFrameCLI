"""Backwards-compatible entry point.

The real CLI lives in the ``dfcli`` package. Prefer ``python -m dfcli`` or the
installed ``dfcli`` console script.
"""

from dfcli.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
