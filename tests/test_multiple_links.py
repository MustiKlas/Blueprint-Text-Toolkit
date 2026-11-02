
from app.parser import _parse_pin


def test_pin_with_multiple_links():
    pin_text = (
        'PinId=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,'
        'PinName="Output",'
        'LinkedTo=('
        '(Node_A BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB),'
        '(Node_B CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)'
        ')'
    )

    pin = _parse_pin(pin_text)

    assert len(pin.linked_to) == 2
    assert (
        "Node_A:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        in pin.linked_to
    )
    assert (
        "Node_B:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
        in pin.linked_to
    )
