from dfcli.ops import add_column, filter_rows, group_by, select, sort_rows
from dfcli.table import Table


def sample() -> Table:
    return Table.from_records(
        [
            {"region": "West", "amount": 10, "id": 1},
            {"region": "East", "amount": 20, "id": 2},
            {"region": "West", "amount": 30, "id": 3},
        ],
        columns=("region", "amount", "id"),
        name="sales",
    )


def test_select_creates_new_table():
    original = sample()
    result = select(original, ["region", "amount"])
    assert result.columns == ("region", "amount")
    assert original.columns == ("region", "amount", "id")


def test_filter_and_add():
    result = add_column(filter_rows(sample(), "amount > 10"), "double", "amount * 2")
    assert result.columns[-1] == "double"
    assert [row["double"] for row in result.rows] == [40, 60]


def test_groupby_sum_and_count():
    result = group_by(sample(), "region", [("sum", "amount", "total"), ("count", "id", "n")])
    by_region = {row["region"]: row for row in result.rows}
    assert by_region["West"]["total"] == 40
    assert by_region["West"]["n"] == 2
    assert by_region["East"]["total"] == 20


def test_sort_descending():
    result = sort_rows(sample(), "amount", descending=True)
    assert [row["amount"] for row in result.rows] == [30, 20, 10]
