
from app.parser import parse_blueprint_text


def test_pin_default_value_is_parsed():
    text = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_PromotableOperator Name="K2Node_Test"
   OperationName="Multiply"
   CustomProperties Pin (PinId=11111111111111111111111111111111,PinName="A",PinType.PinCategory="real",DefaultValue="300.0")
End Object
'''

    result = parse_blueprint_text(text)

    node = result["nodes"][0]
    pin = node.pins[0]

    assert pin.pin_name == "A"
    assert pin.default_value == "300.0"
    assert node.operation_name == "Multiply"