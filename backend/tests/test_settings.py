from app.settings import parse_comma_separated


def test_parse_comma_separated_origins():
    assert parse_comma_separated(
        " http://localhost:3000/, https://consultant.example.com, http://localhost:3000 "
    ) == [
        "http://localhost:3000",
        "https://consultant.example.com",
    ]


def test_parse_comma_separated_empty_value():
    assert parse_comma_separated(" , ") == []
