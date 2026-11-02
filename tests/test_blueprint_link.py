
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.parser import (
    BlueprintLink,
    BlueprintNode,
    BlueprintPin,
    extract_blueprint_links,
    parse_blueprint_text,
)


def test_blueprint_link_stores_endpoints_separately():
    link = BlueprintLink(
        source_node_id="Node_Z",
        source_pin_id="PIN_Z",
        target_node_id="Node_A",
        target_pin_id="PIN_A",
    )

    assert link.source_node_id == "Node_Z"
    assert link.source_pin_id == "PIN_Z"
    assert link.target_node_id == "Node_A"
    assert link.target_pin_id == "PIN_A"


def test_blueprint_link_is_immutable():
    link = BlueprintLink(
        source_node_id="Node_Z",
        source_pin_id="PIN_Z",
        target_node_id="Node_A",
        target_pin_id="PIN_A",
    )

    with pytest.raises(FrozenInstanceError):
        link.source_node_id = "Node_B"


def test_extract_blueprint_links_returns_link_objects():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Output",
                linked_to=["Node_B:PIN_B"],
            )
        ],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        pins=[
            BlueprintPin(
                pin_id="PIN_B",
                pin_name="Input",
            )
        ],
    )

    links = extract_blueprint_links([node_a, node_b])

    assert len(links) == 1
    assert isinstance(links[0], BlueprintLink)
    assert links[0].source_node_id == "Node_A"
    assert links[0].source_pin_id == "PIN_A"
    assert links[0].target_node_id == "Node_B"
    assert links[0].target_pin_id == "PIN_B"


def test_extract_blueprint_links_on_real_sample():
    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)
    links = extract_blueprint_links(result["nodes"])

    assert len(links) > 0

    for link in links:
        assert isinstance(link, BlueprintLink)
        assert link.source_node_id
        assert link.source_pin_id
        assert link.target_node_id
        assert link.target_pin_id
def test_extract_blueprint_links_marks_unknown_direction():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="CustomA",
                direction="",
                linked_to=["Node_B:PIN_B"],
            )
        ],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        pins=[
            BlueprintPin(
                pin_id="PIN_B",
                pin_name="CustomB",
                direction="",
            )
        ],
    )

    links = extract_blueprint_links([node_a, node_b])

    assert len(links) == 1
    assert links[0].direction_known is False
def test_extract_blueprint_links_marks_conflicting_directions_unknown():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                direction="EGPD_Output",
                linked_to=["Node_B:PIN_B"],
            )
        ],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        pins=[
            BlueprintPin(
                pin_id="PIN_B",
                direction="EGPD_Output",
            )
        ],
    )

    links = extract_blueprint_links([node_a, node_b])

    assert len(links) == 1
    assert links[0].direction_known is False
def test_real_sample_reports_direction_coverage():
    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)
    links = extract_blueprint_links(result["nodes"])

    known = sum(link.direction_known for link in links)
    unknown = len(links) - known

    print(f"\nToplam bağlantı: {len(links)}")
    print(f"Yönü bilinen: {known}")
    print(f"Yönü bilinmeyen: {unknown}")

    assert len(links) > 0