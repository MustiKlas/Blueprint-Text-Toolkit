
from pathlib import Path

from app.parser import parse_blueprint_text


def test_real_blueprint_pin_links():
    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"

    raw_text = sample_file.read_text(encoding="utf-8")
    result = parse_blueprint_text(raw_text)

    total_links = 0
    pins_with_links = 0

    for node in result["nodes"]:
        for pin in node.pins:
            if pin.linked_to:
                pins_with_links += 1
                total_links += len(pin.linked_to)

                print(
                    f"{node.node_id} | "
                    f"Pin: {pin.pin_name} | "
                    f"Bağlantılar: {pin.linked_to}"
                )

    print(f"\nBağlantısı olan pin sayısı: {pins_with_links}")
    print(f"Toplam okunan bağlantı sayısı: {total_links}")

    assert result["node_count"] == 14
    assert pins_with_links > 0
    assert total_links > 0


def test_pin_links_reference_existing_nodes():
    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"

    raw_text = sample_file.read_text(encoding="utf-8")
    result = parse_blueprint_text(raw_text)

    # Mevcut node ve pin kimliklerini kaydet.
    pins_by_node = {
        node.node_id: {pin.pin_id for pin in node.pins}
        for node in result["nodes"]
    }

    checked_links = 0

    for node in result["nodes"]:
        for pin in node.pins:
            for link in pin.linked_to:
                target_node_id, target_pin_id = link.rsplit(":", 1)

                # Hedef node mevcut olmalı.
                assert target_node_id in pins_by_node, (
                    f"Hedef node bulunamadı: {target_node_id}"
                )

                # Hedef pin, belirtilen node içinde mevcut olmalı.
                assert target_pin_id in pins_by_node[target_node_id], (
                    f"Hedef pin bulunamadı: "
                    f"{target_node_id}:{target_pin_id}"
                )

                checked_links += 1

    assert checked_links > 0, "Örnekte doğrulanacak bağlantı bulunamadı."
