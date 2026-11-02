
from app.parser import parse_blueprint_text


def test_nested_objects_are_parsed_separately():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Begin Object Class=/Script/Engine.Component Name="InnerObject"
        TestValue=123
    End Object
    OuterValue=456
End Object
'''

    result = parse_blueprint_text(text)

    node_ids = [node.node_id for node in result["nodes"]]

    assert "OuterObject" in node_ids
    assert "InnerObject" in node_ids
    assert len(result["nodes"]) == 2

def test_object_markers_inside_quoted_text_are_not_parsed_as_objects():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Description="Text contains Begin Object and End Object words"
End Object
'''

    result = parse_blueprint_text(text)

    assert result["node_count"] == 1
    assert result["nodes"][0].node_id == "OuterObject"
    
    outer_node = result["nodes"][0]

    assert outer_node.properties["Description"] == '"Text contains Begin Object and End Object words"'
   

def test_object_markers_inside_quoted_value_do_not_change_nesting():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Description="Example End Object text"
    Begin Object Class=/Script/Engine.Component Name="InnerObject"
        Value=123
    End Object
    FinalValue=456
End Object
'''

    result = parse_blueprint_text(text)

    node_ids = [node.node_id for node in result["nodes"]]

    assert node_ids == ["OuterObject", "InnerObject"]
    assert result["node_count"] == 2

def test_escaped_quotes_do_not_break_object_boundaries():
    text = r'''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Description="He said \"End Object\" today"
    Begin Object Class=/Script/Engine.Component Name="InnerObject"
        Value=123
    End Object
    FinalValue=456
End Object
'''

    result = parse_blueprint_text(text)

    node_ids = [node.node_id for node in result["nodes"]]

    assert node_ids == ["OuterObject", "InnerObject"]
    assert result["node_count"] == 2
    assert result["nodes"][0].properties["FinalValue"] == "456"

def test_unclosed_object_is_not_returned_as_a_complete_node():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="IncompleteObject"
    Value=123
'''

    result = parse_blueprint_text(text)

    assert result["raw_text"] == text
    assert result["node_count"] == 0
    assert result["nodes"] == []

def test_closed_inner_object_is_kept_when_outer_object_is_unclosed():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Begin Object Class=/Script/Engine.Component Name="InnerObject"
        Value=123
    End Object
'''

    result = parse_blueprint_text(text)

    node_ids = [node.node_id for node in result["nodes"]]

    assert node_ids == ["InnerObject"]
    assert result["node_count"] == 1
    assert result["raw_text"] == text

def test_nested_object_pins_are_not_added_to_outer_object():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Begin Object Class=/Script/Engine.Component Name="InnerObject"
        Begin Object Class=/Script/BlueprintGraph.K2Node_VariableGet Name="InnerNode"
            CustomProperties Pin (PinId="inner-pin-1",PinName="Value",Direction="EGPD_Output")
        End Object
    End Object
End Object
'''

    result = parse_blueprint_text(text)
    nodes_by_id = {node.node_id: node for node in result["nodes"]}

    assert "OuterObject" in nodes_by_id
    assert "InnerObject" in nodes_by_id
    assert "InnerNode" in nodes_by_id

    assert len(nodes_by_id["OuterObject"].pins) == 0
    assert len(nodes_by_id["InnerObject"].pins) == 0
    assert len(nodes_by_id["InnerNode"].pins) == 1
    assert nodes_by_id["InnerNode"].pins[0].pin_id == "inner-pin-1"

def test_nested_object_properties_are_not_added_to_outer_object():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Begin Object Class=/Script/BlueprintGraph.K2Node_VariableGet Name="InnerNode"
        Value=123
    End Object
End Object
'''

    result = parse_blueprint_text(text)
    nodes_by_id = {node.node_id: node for node in result["nodes"]}

    assert "OuterObject" in nodes_by_id
    assert "InnerNode" in nodes_by_id

    assert "Value" not in nodes_by_id["OuterObject"].properties
    assert nodes_by_id["InnerNode"].properties["Value"] == "123"

def test_property_cleaner_preserves_object_markers_inside_quoted_text():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Description="The words Begin Object and End Object are examples"
    FinalValue=456
End Object
'''

    result = parse_blueprint_text(text)

    assert result["node_count"] == 1

    outer_node = result["nodes"][0]
    assert outer_node.properties["Description"] == (
        '"The words Begin Object and End Object are examples"'
    )
    assert outer_node.properties["FinalValue"] == "456"

def test_object_marker_words_inside_longer_words_are_not_boundaries():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Description="Begin Objectively and End Objectively"
    Value=123
End Object
'''

    result = parse_blueprint_text(text)

    assert result["node_count"] == 1
    outer_node = result["nodes"][0]

    assert outer_node.properties["Description"] == (
        '"Begin Objectively and End Objectively"'
    )
    assert outer_node.properties["Value"] == "123"

def test_object_markers_followed_by_extra_characters_do_not_close_objects():
    text = '''
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Value=123
    End ObjectExtra
    FinalValue=456
End Object
'''

    result = parse_blueprint_text(text)

    assert result["node_count"] == 1
    outer_node = result["nodes"][0]
    assert outer_node.properties["Value"] == "123"
    assert outer_node.properties["FinalValue"] == "456"
