# dfcli

A small, scriptable command-line tool for tabular data. It started life as an
interactive pandas demo in a single `main.py`; it is now a real package with a
pipeline command language, safe expressions, undo/history, and a backend-neutral
core.

```bash
dfcli run 'load sales.csv | filter amount > 100 and region == "West" | groupby region sum:amount | show'
```

## Why the rewrite

The old version matched commands with `if 'graph' in query`, mutated the live
DataFrame while plotting, and could not be scripted. `dfcli` replaces that with:

- a real parser: stages separated by `|`, with quote-aware splitting
- a safe expression language (AST whitelist, no `eval`)
- immutable table operations, which makes `undo` and replay possible
- an `explain` command that prints the equivalent pandas code
- a package layout with tests instead of one 300-line script

## Install

```bash
pip install -e .
```

Or run directly from the repo without installing:

```bash
python3 -m dfcli run 'load data.csv | show 5'
```

`pandas` and `matplotlib` are only imported when you use `explain`-grade
export/plot paths; the CSV engine itself uses the standard library.

## Usage

### One-shot pipelines

```bash
dfcli run 'load sales.csv | show 5'
dfcli run 'load sales.csv | filter amount > 100 | add tax=amount * 0.1 | select region, amount, tax | save taxed.csv'
```

### Scripts from stdin

```bash
cat clean.dfcli | dfcli run
```

Example `clean.dfcli`:

```text
load raw.csv
filter status == "ok"
drop temp_column
groupby region sum:amount count:id
save clean.csv
explain
```

### Interactive REPL

```bash
dfcli repl
```

```text
dfcli> load sales.csv
dfcli> filter amount > 10 | head 3 | show
dfcli> undo
dfcli> explain
dfcli> exit
```

## Commands

| Command | Purpose |
| --- | --- |
| `load FILE.csv [as NAME]` | read a CSV into a named table |
| `save FILE.csv` | write the current table to CSV |
| `show [N]` / `info` | print rows / schema |
| `list` / `use NAME` | manage multiple loaded tables |
| `select COL...` / `drop COL...` / `rename OLD=NEW...` | shape columns |
| `filter EXPR` | keep rows where the expression is true |
| `add NAME=EXPR` / `set NAME=EXPR` | computed columns |
| `sort COL [--desc]` / `distinct [COL...]` | order and deduplicate |
| `groupby COL FUNC:COL[:ALIAS]...` | aggregations (`sum`, `count`, `mean`, `min`, `max`) |
| `head [N]` / `tail [N]` | keep first/last rows |
| `plot bar\|line\|... [X] [Y] [--out FILE.png]` | save a chart |
| `explain` / `history` / `undo` | inspect and rewind the session |
| `help [COMMAND]` | built-in docs |

Expressions support comparisons, boolean `and`/`or`, arithmetic, and literals.
Function calls, attribute access, and imports are rejected.

## Architecture

```text
dfcli/
  cli.py         argparse entry point: run / repl / commands
  parser.py      quote-aware pipeline splitter + stage parser
  expr.py        safe AST expression parser/evaluator
  table.py       immutable columns + rows representation
  ops.py         pure transformations (select, filter, groupby, ...)
  io.py          stdlib CSV engine, optional pandas conversion
  plots.py       lazy matplotlib plotting
  session.py     current table, history, code trace, undo stack
  commands.py    command registry and handlers
tests/           parser, expression, ops, and session tests
```

The `main.py` file remains as a two-line compatibility shim; the tool itself is
no longer a single script.

## Development

```bash
pip install -e '.[dev]'
pytest -q
```

## Roadmap

- joins between named tables
- Parquet/JSON backends and a swappable Polars/DuckDB engine
- script files with variables and comments
- config file for default output/plot style
- plugin command discovery
- optional Textual TUI on top of the same core
