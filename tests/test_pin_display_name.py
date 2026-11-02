
import re
from app.parser import _parse_pin, _extract_value


def test_parse_pin_reads_pin_name_and_friendly_name():
    pin_text = (
        'CustomProperties Pin ('
        'PinId=ABC123,'
        'PinName="then",'
        'PinFriendlyName=NSLOCTEXT("K2Node", "true", "true"),'
        'PinType.PinCategory="exec",'
        'LinkedTo=(),'
        'PersistentGuid=00000000000000000000000000000000,'
        'bHidden=False'
        ')'
    )

    print("METİN:", repr(pin_text))
    print("PIN ID:", repr(_extract_value(pin_text, "PinId")))
    print("REGEX TEST:", re.search(r'(?:^|,)\s*PinId\s*=\s*(?:"([^"]*)"|([^,)]*))', pin_text))
    print("BASİT TEST:", re.search(r"PinId=ABC123", pin_text))
    print("PIN NAME:", repr(_extract_value(pin_text, "PinName")))

    pin = _parse_pin(pin_text)

    assert pin.pin_id == "ABC123"
    assert pin.pin_name == "then"
    assert pin.pin_friendly_name == 'NSLOCTEXT("K2Node", "true", "true")'
