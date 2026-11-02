
from app.parser import parse_blueprint_text


def test_unknown_node_properties_are_preserved():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="K2Node_Test"
    FunctionReference=(MemberName="TestFunction",bSelfContext=True)
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["FunctionReference"] == (
        '(MemberName="TestFunction",bSelfContext=True)'
    )

from app.parser import parse_blueprint_text


def test_node_properties_do_not_include_pin_properties():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="TestNode"
    NodeComment="My node"
    CustomProperties Pin (
        PinId="11111111111111111111111111111111"
        PinName="Value"
        PinType.PinCategory="real"
        DefaultValue="42"
    )
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["NodeComment"] == '"My node"'
    assert "PinName" not in node.properties
    assert "PinType.PinCategory" not in node.properties
    assert "DefaultValue" not in node.properties

    assert len(node.pins) == 1
    assert node.pins[0].properties["PinName"] == '"Value"'
    assert node.pins[0].properties["DefaultValue"] == '"42"'
