
from app.parser import (
    BlueprintLink,
    BlueprintNode,
    BlueprintPin,
    BlueprintAnalysis,
    build_blueprint_analysis,
)


def test_analysis_model_preserves_nodes_and_pin_connections():
    source_node = BlueprintNode(
        node_id="node_a",
        node_class="K2Node_CustomSource",
        pins=[
            BlueprintPin(
                pin_id="pin_a",
                pin_name="Output",
                direction="output",
                pin_type="int",
            )
        ],
    )

    target_node = BlueprintNode(
        node_id="node_b",
        node_class="K2Node_CustomTarget",
        pins=[
            BlueprintPin(
                pin_id="pin_b",
                pin_name="Input",
                direction="input",
                pin_type="int",
            )
        ],
    )

    link = BlueprintLink(
        source_node_id="node_a",
        source_pin_id="pin_a",
        target_node_id="node_b",
        target_pin_id="pin_b",
    )

    lines, analysis = build_blueprint_analysis(
        [source_node, target_node],
        [link],
        return_model=True,
    )

    assert isinstance(analysis, BlueprintAnalysis)
    assert len(analysis.nodes) == 2
    assert analysis.links == [link]

    source = analysis.nodes[0]
    target = analysis.nodes[1]

    assert source.node_id == "node_a"
    assert source.node_class == "K2Node_CustomSource"

    assert source.pins[0].outgoing == [("node_b", "pin_b")]
    assert target.pins[0].incoming == [("node_a", "pin_a")]

    assert isinstance(lines, list)


def test_analysis_model_keeps_unknown_nodes_structurally():
    node = BlueprintNode(
        node_id="unknown_node",
        node_class="K2Node_CompletelyUnknown",
        operation_name="UnknownOperation",
        pins=[
            BlueprintPin(
                pin_id="unknown_pin",
                pin_name="Value",
                direction="input",
                pin_type="custom_type",
                default_value="42",
            )
        ],
    )

    _, analysis = build_blueprint_analysis(
        [node],
        [],
        return_model=True,
    )

    analyzed_node = analysis.nodes[0]
    analyzed_pin = analyzed_node.pins[0]

    assert analyzed_node.node_id == "unknown_node"
    assert analyzed_node.operation_name == "UnknownOperation"
    assert analyzed_pin.name == "Value"
    assert analyzed_pin.pin_type == "custom_type"
    assert analyzed_pin.default_value == "42"


def test_analysis_model_is_optional_for_backward_compatibility():
    node = BlueprintNode(
        node_id="node_a",
        node_class="K2Node_Custom",
    )

    result = build_blueprint_analysis([node], [])

    assert isinstance(result, list)
