
from app.parser import _extract_value


def test_extract_value_with_space_after_comma():
    text = 'SomeField=Value, PinName="Return Value"'
    assert _extract_value(text, "PinName") == "Return Value"


def test_extract_value_with_spaces_around_equals():
    text = 'PinName = "Execute"'
    assert _extract_value(text, "PinName") == "Execute"


def test_extract_value_missing_field():
    text = 'SomeField=Value'
    assert _extract_value(text, "PinName") == ""
