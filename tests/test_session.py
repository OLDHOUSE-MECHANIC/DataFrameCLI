import pytest

from dfcli.session import Session, SessionError
from dfcli.table import Table


def make_csv(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text("region,amount,id\nWest,10,1\nEast,20,2\nWest,30,3\n", encoding="utf-8")
    return path


def test_full_pipeline_and_explain(tmp_path):
    session = Session()
    path = make_csv(tmp_path)
    out = session.execute(f'load {path} | filter amount > 10 | groupby region sum:amount | show | explain')
    assert "loaded" in out
    assert "West" in out
    assert "pd.read_csv" in out
    assert session.current is not None
    assert session.current.shape == (2, 2)


def test_undo_restores_previous_table(tmp_path):
    session = Session()
    session.execute(f"load {make_csv(tmp_path)}")
    before = session.current
    session.execute("filter amount > 10")
    assert session.current is not before
    session.execute("undo")
    assert session.current is before


def test_pipe_survives_quoted_expression(tmp_path):
    session = Session()
    session.execute(f"load {make_csv(tmp_path)}")
    session.execute("add label='a|b' | select label")
    assert session.current is not None
    assert [row["label"] for row in session.current.rows] == ["a|b", "a|b", "a|b"]


def test_unknown_command_is_reported(tmp_path):
    session = Session()
    with pytest.raises(SessionError, match="unknown command"):
        session.execute("frobnicate everything")
