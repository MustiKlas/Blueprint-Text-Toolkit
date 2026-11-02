
from app.parser import parse_blueprint_text


def test_node_properties_preserve_different_value_types():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="K2Node_Test"
    NegativeValue=-25
    FloatValue=346.41
    BooleanValue=True
    TextValue="Hello World"
    VectorValue=(X=1,Y=2,Z=3)
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["NegativeValue"] == "-25"
    assert node.properties["FloatValue"] == "346.41"
    assert node.properties["BooleanValue"] == "True"
    assert node.properties["TextValue"] == '"Hello World"'
    assert node.properties["VectorValue"] == "(X=1,Y=2,Z=3)"

def test_properties_preserve_commas_and_parentheses_inside_values():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="TestNode"
    TextValue="Hello, (World)"
    FunctionReference=(MemberName="TestFunction",bSelfContext=True)
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["TextValue"] == '"Hello, (World)"'
    assert (
        node.properties["FunctionReference"]
        == '(MemberName="TestFunction",bSelfContext=True)'
    )

def test_unknown_node_properties_are_preserved():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Custom Name="CustomNode"
    FutureProperty=SomeNewValue
    CustomSetting=(Mode=Advanced,Count=3)
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["FutureProperty"] == "SomeNewValue"
    assert node.properties["CustomSetting"] == "(Mode=Advanced,Count=3)"
def test_equals_signs_inside_quoted_values_are_preserved():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="TestNode"
    TextValue="Mode=Advanced, Count=3"
    NextValue=42
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["TextValue"] == '"Mode=Advanced, Count=3"'
    assert node.properties["NextValue"] == "42"
    assert "Mode" not in node.properties
    assert "Count" not in node.properties
def test_nested_value_does_not_consume_following_properties():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="TestNode"
    Settings=(Mode=Advanced,Options=(Count=3,Enabled=True))
    FinalValue=456
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["Settings"] == (
        "(Mode=Advanced,Options=(Count=3,Enabled=True))"
    )
    assert node.properties["FinalValue"] == "456"
def test_quoted_value_with_equals_commas_and_parentheses():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="TestNode"
    TextValue="Mode=Advanced, (Count=3)"
    NextValue=42
End Object
'''

    result = parse_blueprint_text(text)
    node = result["nodes"][0]

    assert node.properties["TextValue"] == '"Mode=Advanced, (Count=3)"'
    assert node.properties["NextValue"] == "42"
def test_nested_parenthesized_property_is_preserved():
    from app.parser import _extract_properties

    text = (
        'FunctionReference=(MemberName="TestFunction",'
        'bSelfContext=True),'
        'NodePosX=100'
    )

    properties = _extract_properties(text)

    assert properties["FunctionReference"] == (
        '(MemberName="TestFunction",bSelfContext=True)'
    )
    assert properties["NodePosX"] == "100"