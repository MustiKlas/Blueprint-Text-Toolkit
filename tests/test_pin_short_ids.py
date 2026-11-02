
from app.parser import (
    BlueprintNode,
    BlueprintPin,
    create_pin_short_ids,
)


def test_same_pin_keeps_same_short_id():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                linked_to=["Node_B:PIN_B", "Node_C:PIN_C"],
            ),
        ],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        pins=[BlueprintPin(pin_id="PIN_B")],
    )

    node_c = BlueprintNode(
        node_id="Node_C",
        pins=[BlueprintPin(pin_id="PIN_C")],
    )

    short_ids = create_pin_short_ids([node_a, node_b, node_c])

    assert short_ids[("Node_A", "PIN_A")] == "P0001"
    assert short_ids[("Node_B", "PIN_B")] == "P0002"
    assert short_ids[("Node_C", "PIN_C")] == "P0003"


def test_different_pins_get_different_short_ids():
    node = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(pin_id="PIN_A"),
            BlueprintPin(pin_id="PIN_B"),
        ],
    )

    short_ids = create_pin_short_ids([node])

    assert short_ids[("Node_A", "PIN_A")] != short_ids[("Node_A", "PIN_B")]


def test_same_pin_id_in_different_nodes_is_separate():
    nodes = [
        BlueprintNode(
            node_id="Node_A",
            pins=[BlueprintPin(pin_id="SHARED_ID")],
        ),
        BlueprintNode(
            node_id="Node_B",
            pins=[BlueprintPin(pin_id="SHARED_ID")],
        ),
    ]

    short_ids = create_pin_short_ids(nodes)

    assert short_ids[("Node_A", "SHARED_ID")] != short_ids[("Node_B", "SHARED_ID")]
