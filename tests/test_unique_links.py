
from app.parser import BlueprintPin, BlueprintNode, extract_unique_links


def test_same_connection_is_counted_once():
    # İki pin de aynı kablonun iki ucunu gösteriyor.
    pin_a = BlueprintPin(
        pin_id="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        pin_name="Output",
        linked_to=["Node_B:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"],
    )

    pin_b = BlueprintPin(
        pin_id="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        pin_name="Input",
        linked_to=["Node_A:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"],
    )

    node_a = BlueprintNode(
        node_id="Node_A",
        node_class="TestNode",
        pins=[pin_a],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        node_class="TestNode",
        pins=[pin_b],
    )

    nodes = [node_a, node_b]

    # Şimdilik beklenen davranışı tanımlıyoruz:
    # İki yönlü kayıt, tek kablo olarak sayılmalı.
    from app.parser import extract_unique_links

    links = extract_unique_links(nodes)

    assert len(links) == 1

from pathlib import Path

from app.parser import parse_blueprint_text, extract_unique_links



def test_unique_links_on_real_blueprint():
    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)
    links = extract_unique_links(result["nodes"])

    print(f"\nNode sayısı: {result['node_count']}")
    print(f"Pin sayısı: {result['pin_count']}")
    print(f"Benzersiz kablo sayısı: {len(links)}")

    assert len(links) > 0, "Örnek Blueprint dosyasından hiç bağlantı çıkarılmadı."

    nodes_by_id = {
        node.node_id: node
        for node in result["nodes"]
    }

    for source_node_id, source_pin_id, target_node_id, target_pin_id in links:
        print(
            f"{source_node_id} [{source_pin_id}]"
            f" -> {target_node_id} [{target_pin_id}]"
        )

        assert source_node_id in nodes_by_id, (
            f"Kaynak node bulunamadı: {source_node_id}"
        )
        assert target_node_id in nodes_by_id, (
            f"Hedef node bulunamadı: {target_node_id}"
        )

        source_pin_ids = {
            pin.pin_id for pin in nodes_by_id[source_node_id].pins
        }
        target_pin_ids = {
            pin.pin_id for pin in nodes_by_id[target_node_id].pins
        }

        assert source_pin_id in source_pin_ids, (
            f"Kaynak pin bulunamadı: {source_node_id}:{source_pin_id}"
        )
        assert target_pin_id in target_pin_ids, (
            f"Hedef pin bulunamadı: {target_node_id}:{target_pin_id}"
        )

def test_link_to_missing_pin_is_rejected():
    pin_a = BlueprintPin(
        pin_id="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        pin_name="Output",
        linked_to=["Node_B:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"],
    )

    pin_b = BlueprintPin(
        pin_id="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        pin_name="Input",
        linked_to=[],
    )

    node_a = BlueprintNode(
        node_id="Node_A",
        node_class="TestNode",
        pins=[pin_a],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        node_class="TestNode",
        pins=[pin_b],
    )

    links = extract_unique_links([node_a, node_b])

    # Node_B mevcut ama CCCC... kimlikli pin mevcut değil.
    assert links == []
def test_link_to_missing_node_is_rejected():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Output",
                linked_to=["Node_Missing:PIN_MISSING"],
            )
        ],
    )

    links = extract_unique_links([node_a])

    assert links == []  
    
def test_one_sided_connection_is_counted_once():
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
                linked_to=[],
            )
        ],
    )

    links = extract_unique_links([node_a, node_b])

    assert len(links) == 1
    assert {
        (links[0][0], links[0][1]),
        (links[0][2], links[0][3]),
    } == {
        ("Node_A", "PIN_A"),
        ("Node_B", "PIN_B"),
    }

def test_one_sided_connection_preserves_source_and_target():
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
                linked_to=[],
            )
        ],
    )

    links = extract_unique_links([node_a, node_b])

    assert links == [
        ("Node_A", "PIN_A", "Node_B", "PIN_B")
    ]

def test_connection_direction_is_not_alphabetically_sorted():
    node_z = BlueprintNode(
        node_id="Node_Z",
        pins=[
            BlueprintPin(
                pin_id="PIN_Z",
                pin_name="Output",
                linked_to=["Node_A:PIN_A"],
            )
        ],
    )

    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Input",
                linked_to=[],
            )
        ],
    )

    links = extract_unique_links([node_z, node_a])

    assert links == [
        ("Node_Z", "PIN_Z", "Node_A", "PIN_A")
    ]

def test_bidirectional_connection_keeps_first_seen_direction():
    node_z = BlueprintNode(
        node_id="Node_Z",
        pins=[
            BlueprintPin(
                pin_id="PIN_Z",
                pin_name="Output",
                linked_to=["Node_A:PIN_A"],
            )
        ],
    )

    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Input",
                linked_to=["Node_Z:PIN_Z"],
            )
        ],
    )

    links = extract_unique_links([node_z, node_a])

    assert links == [
        ("Node_Z", "PIN_Z", "Node_A", "PIN_A")
    ]

def test_self_link_is_counted_once():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Output",
                linked_to=["Node_A:PIN_A"],
            )
        ],
    )

    links = extract_unique_links([node_a])

    assert links == [
        ("Node_A", "PIN_A", "Node_A", "PIN_A")
    ]

def test_explicit_pin_directions_override_pin_names():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Input",
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
                pin_name="Output",
                direction="EGPD_Input",
                linked_to=[],
            )
        ],
    )

    links = extract_unique_links([node_a, node_b])

    assert links == [
        ("Node_A", "PIN_A", "Node_B", "PIN_B")
    ]

def test_self_link_is_deduplicated_when_recorded_twice():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_A",
                pin_name="Output",
                linked_to=["Node_A:PIN_B"],
            ),
            BlueprintPin(
                pin_id="PIN_B",
                pin_name="Input",
                linked_to=["Node_A:PIN_A"],
            ),
        ],
    )

    links = extract_unique_links([node_a])

    assert len(links) == 1
    assert {
        (links[0][0], links[0][1]),
        (links[0][2], links[0][3]),
    } == {
        ("Node_A", "PIN_A"),
        ("Node_A", "PIN_B"),
    }
def test_explicit_direction_works_with_custom_pin_names():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_RESULT",
                pin_name="Result",
                direction="EGPD_Output",
                linked_to=["Node_B:PIN_VALUE"],
            )
        ],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        pins=[
            BlueprintPin(
                pin_id="PIN_VALUE",
                pin_name="Value",
                direction="EGPD_Input",
                linked_to=[],
            )
        ],
    )

    links = extract_unique_links([node_a, node_b])

    assert links == [
        ("Node_A", "PIN_RESULT", "Node_B", "PIN_VALUE")
    ]
def test_missing_direction_uses_standard_pin_name_fallback():
    node_a = BlueprintNode(
        node_id="Node_A",
        pins=[
            BlueprintPin(
                pin_id="PIN_RESULT",
                pin_name="Result",
                linked_to=["Node_B:PIN_VALUE"],
            )
        ],
    )

    node_b = BlueprintNode(
        node_id="Node_B",
        pins=[
            BlueprintPin(
                pin_id="PIN_VALUE",
                pin_name="Value",
            )
        ],
    )

    links = extract_unique_links([node_a, node_b])

    # Yönler belirtilmediğinde mevcut kural iki pini de giriş sayıyor.
    # Bu yüzden bağlantı, ilk kaydın sırasıyla korunuyor.
    assert links == [
        ("Node_A", "PIN_RESULT", "Node_B", "PIN_VALUE")
    ]