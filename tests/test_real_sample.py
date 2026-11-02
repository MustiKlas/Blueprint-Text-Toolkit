
from pathlib import Path

from app.parser import parse_blueprint_text


def test_real_blueprint_sample():
    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"

    assert sample_file.exists(), (
        f"Örnek dosya bulunamadı: {sample_file}"
    )

    raw_text = sample_file.read_text(encoding="utf-8")
    result = parse_blueprint_text(raw_text)

    print(f"\nKarakter sayısı: {result['character_count']}")
    print(f"Satır sayısı: {len(result['lines'])}")
    print(f"Bulunan node sayısı: {result['node_count']}")
    print(f"Bulunan pin sayısı: {result['pin_count']}")

    assert result["raw_text"] == raw_text
    assert result["node_count"] > 0
    assert result["pin_count"] > 0

    print("\nBulunan node'lar:")
    for node in result["nodes"]:
        print(
            f"  {node.node_id} | "
            f"Pin sayısı: {len(node.pins)}"
        )
