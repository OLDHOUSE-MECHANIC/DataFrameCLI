"""A deliberately small, safe expression language.

We parse with :mod:`ast` and evaluate a whitelist of nodes. There is no
``eval``/``exec``, no attribute access, and no function calls, so a pipeline
coming from a file or stdin cannot run arbitrary Python.
"""

from __future__ import annotations

import ast
from typing import Any, Mapping

_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.UnaryOp,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.Name,
    ast.Constant,
    ast.Load,
    ast.List,
    ast.Tuple,
)


class ExpressionError(ValueError):
    """Raised when an expression is invalid or unsafe."""


def parse(source: str) -> ast.Expression:
    """Parse *source* into a whitelisted AST expression."""
    try:
        tree = ast.parse(source.strip(), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"invalid expression {source!r}: {exc.msg}") from exc

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(
                f"unsupported syntax {type(node).__name__} in {source!r}; "
                "only comparisons, arithmetic, and and/or are allowed"
            )
    return tree


def evaluate(tree: ast.Expression, row: Mapping[str, Any]) -> Any:
    """Evaluate a parsed expression against a single row mapping."""
    return _eval(tree.body, row)


def render(tree: ast.Expression) -> str:
    """Return a stable source representation, used by ``explain``."""
    return ast.unparse(tree)


def _eval(node: ast.AST, row: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, row)

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id not in row:
            raise ExpressionError(
                f"unknown column {node.id!r}; available: {', '.join(map(str, row)) or '(none)'}"
            )
        return row[node.id]

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval(item, row) for item in node.elts]

    if isinstance(node, ast.UnaryOp):
        value = _eval(node.operand, row)
        if isinstance(node.op, ast.USub):
            return -_coerce_number(value)
        if isinstance(node.op, ast.UAdd):
            return +_coerce_number(value)
        if isinstance(node.op, ast.Not):
            return not value
        raise ExpressionError(f"unsupported unary operator: {type(node.op).__name__}")

    if isinstance(node, ast.BinOp):
        left = _eval(node.left, row)
        right = _eval(node.right, row)
        if isinstance(node.op, ast.Add):
            return _coerce_number(left) + _coerce_number(right)
        if isinstance(node.op, ast.Sub):
            return _coerce_number(left) - _coerce_number(right)
        if isinstance(node.op, ast.Mult):
            return _coerce_number(left) * _coerce_number(right)
        if isinstance(node.op, ast.Div):
            return _coerce_number(left) / _coerce_number(right)
        if isinstance(node.op, ast.FloorDiv):
            return _coerce_number(left) // _coerce_number(right)
        if isinstance(node.op, ast.Mod):
            return _coerce_number(left) % _coerce_number(right)
        if isinstance(node.op, ast.Pow):
            return _coerce_number(left) ** _coerce_number(right)
        raise ExpressionError(f"unsupported operator: {type(node.op).__name__}")

    if isinstance(node, ast.BoolOp):
        values = [_eval(value, row) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ExpressionError(f"unsupported boolean operator: {type(node.op).__name__}")

    if isinstance(node, ast.Compare):
        left = _eval(node.left, row)
        for operator, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, row)
            if not _compare(operator, left, right):
                return False
            left = right
        return True

    raise ExpressionError(f"cannot evaluate {type(node).__name__}")


def _compare(operator: ast.cmpop, left: Any, right: Any) -> bool:
    if isinstance(operator, ast.Eq):
        return left == right
    if isinstance(operator, ast.NotEq):
        return left != right
    if isinstance(operator, ast.In):
        return left in right
    if isinstance(operator, ast.NotIn):
        return left not in right

    if left is None or right is None:
        return False
    if isinstance(left, str) and isinstance(right, str):
        a, b = left, right
    else:
        a, b = _coerce_number(left), _coerce_number(right)

    if isinstance(operator, ast.Lt):
        return a < b
    if isinstance(operator, ast.LtE):
        return a <= b
    if isinstance(operator, ast.Gt):
        return a > b
    if isinstance(operator, ast.GtE):
        return a >= b
    raise ExpressionError(f"unsupported comparison: {type(operator).__name__}")


def _coerce_number(value: Any) -> int | float:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return float(value)
    raise ExpressionError(f"expected a number, got {value!r}")
