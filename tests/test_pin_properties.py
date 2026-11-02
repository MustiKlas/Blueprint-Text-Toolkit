
from app.parser import parse_blueprint_text


def test_unknown_pin_properties_are_preserved():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="K2Node_Test"
    CustomProperties Pin (
        PinId=11111111111111111111111111111111,
        PinName="Value",
        PinType.PinCategory="real",
        DefaultValue="346.41",
        bHidden=True
    )
End Object
'''

    result = parse_blueprint_text(text)
    pin = result["nodes"][0].pins[0]

    assert pin.properties["PinName"] == '"Value"'
    assert pin.properties["PinType.PinCategory"] == '"real"'
    assert pin.properties["DefaultValue"] == '"346.41"'
    assert pin.properties["bHidden"] == "True"
def test_pin_nested_property_preserves_following_property():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="K2Node_Test"
    CustomProperties Pin (
        PinId=11111111111111111111111111111111,
        PinName="Value",
        CustomSetting=(Mode=Advanced,Options=(Count=3,Enabled=True)),
        bHidden=True
    )
End Object
'''

    result = parse_blueprint_text(text)
    pin = result["nodes"][0].pins[0]

    assert pin.properties["CustomSetting"] == (
        "(Mode=Advanced,Options=(Count=3,Enabled=True))"
    )
    assert pin.properties["bHidden"] == "True"