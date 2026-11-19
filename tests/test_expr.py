import pytest

from dfcli.expr import ExpressionError, evaluate, parse, render


def test_comparison_and_boolean():
    tree = parse('amount > 100 and region == "West"')
    assert evaluate(tree, {"amount": 150, "region": "West"}) is True
    assert evaluate(tree, {"amount": 50, "region": "West"}) is False
    assert evaluate(tree, {"amount": 150, "region": "East"}) is False


def test_arithmetic_and_unary():
    tree = parse("price * qty - discount")
    assert evaluate(tree, {"price": 10, "qty": 3, "discount": 5}) == 25
    assert evaluate(parse("-balance"), {"balance": 7}) == -7


def test_render_roundtrip():
    source = "amount >= 10"
    assert render(parse(source)) == source


def test_rejects_unsafe_calls():
    with pytest.raises(ExpressionError):
        parse("__import__('os').system('echo bad')")


def test_unknown_column_is_clear():
    tree = parse("missing > 1")
    with pytest.raises(ExpressionError, match="unknown column"):
        evaluate(tree, {"amount": 2})
