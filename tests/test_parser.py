from dfcli.parser import ParseError, parse_pipeline, split_pipeline


def test_split_respects_quotes():
    result = split_pipeline('load a.csv | filter city == "New York" | show')
    assert result == ['load a.csv', 'filter city == "New York"', 'show']


def test_parse_stages():
    stages = parse_pipeline('filter amount > 10 | groupby region sum:amount')
    assert [stage.command for stage in stages] == ["filter", "groupby"]
    assert stages[0].args == ("amount", ">", "10")
    assert stages[1].args == ("region", "sum:amount")


def test_escaped_pipe():
    stages = parse_pipeline(r'add label="a|b" | show')
    assert stages[0].args == ("label=a|b",)
    assert stages[1].command == "show"


def test_empty_pipeline_rejected():
    try:
        parse_pipeline("   ")
    except ParseError:
        pass
    else:
        raise AssertionError("expected ParseError")
