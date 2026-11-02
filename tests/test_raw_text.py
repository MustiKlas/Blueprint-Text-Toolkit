
from app.parser import parse_blueprint_text


def test_raw_text_is_preserved_exactly():
    original_text = (
        'Begin Object Class="TestClass" Name="TestNode"\n'
        '\tCustomField = "Example Value"\n'
        'End Object\n'
    )

    result = parse_blueprint_text(original_text)

    assert result["raw_text"] == original_text
    assert result["character_count"] == len(original_text)
    assert result["lines"] == original_text.splitlines()
