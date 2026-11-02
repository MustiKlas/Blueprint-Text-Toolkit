
from app.parser import parse_blueprint_text


def test_raw_text_is_preserved():
    source = (
        'PinName="WorldLocation"\n'
        'PinId="ABC123"\n'
        'LinkedTo=(OtherNode_1 Output)'
    )

    result = parse_blueprint_text(source)

    assert result["raw_text"] == source
    assert result["character_count"] == len(source)
    assert len(result["lines"]) == 3


def test_empty_text_is_preserved():
    result = parse_blueprint_text("")

    assert result["raw_text"] == ""
    assert result["character_count"] == 0
    assert result["lines"] == []


def test_non_string_input_is_rejected():
    try:
        parse_blueprint_text(None)
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Metin olmayan girdi reddedilmeliydi."
        )

def test_blueprint_node_and_pin_are_parsed():
    source = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="K2Node_CallFunction_0"
   CustomProperties Pin (PinId=ABCDEF0123456789ABCDEF0123456789,PinName="ReturnValue",Direction="EGPD_Output",PinType.PinCategory="real",PinType.PinSubCategory="double",LinkedTo=(K2Node_Add_0 1234567890ABCDEF1234567890ABCDEF,))
End Object
'''

    result = parse_blueprint_text(source)

    assert result["node_count"] == 1
    assert result["pin_count"] == 1

    node = result["nodes"][0]
    assert node.node_id == "K2Node_CallFunction_0"
    assert node.node_class == "/Script/BlueprintGraph.K2Node_CallFunction"

    pin = node.pins[0]
    assert pin.pin_id == "ABCDEF0123456789ABCDEF0123456789"
    assert pin.pin_name == "ReturnValue"
    assert pin.pin_type == "real:double"
    assert pin.linked_to == [
        "K2Node_Add_0:1234567890ABCDEF1234567890ABCDEF"
    ]


def test_blueprint_without_nodes_returns_empty_node_list():
    result = parse_blueprint_text("Henüz node içermeyen metin")

    assert result["nodes"] == []
    assert result["node_count"] == 0
    assert result["pin_count"] == 0

def test_multiple_nodes_and_pins_are_parsed():
    source = '''
Begin Object Class=/Script/BlueprintGraph.K2Node_FunctionEntry Name="Entry"
   CustomProperties Pin (PinId=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,PinName="then",Direction="EGPD_Output",PinType.PinCategory="exec",LinkedTo=(Result BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,))
   CustomProperties Pin (PinId=CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC,PinName="Coord",Direction="EGPD_Output",PinType.PinCategory="struct",LinkedTo=(Break DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD,))
End Object
Begin Object Class=/Script/BlueprintGraph.K2Node_FunctionResult Name="Result"
   CustomProperties Pin (PinId=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,PinName="execute",PinType.PinCategory="exec",LinkedTo=(Entry AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,))
End Object
'''

    result = parse_blueprint_text(source)

    assert result["node_count"] == 2
    assert result["pin_count"] == 3

    entry = result["nodes"][0]
    assert entry.node_id == "Entry"
    assert len(entry.pins) == 2

    assert entry.pins[0].linked_to == [
        "Result:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
    ]
    assert entry.pins[1].linked_to == [
        "Break:DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
    ]
def test_extract_properties_reads_desired_pin_direction():
    from app.parser import _extract_properties

    text = (
        'CustomProperties UserDefinedPin '
        '(PinName="Coord",'
        'DesiredPinDirection=EGPD_Output)'
    )

    properties = _extract_properties(text, remove_nested_objects=False)

    assert properties["PinName"] == '"Coord"'
    assert properties["DesiredPinDirection"] == "EGPD_Output"
def test_user_defined_pin_direction_is_available_by_pin_name():
    from app.parser import _extract_properties

    text = (
        'CustomProperties UserDefinedPin '
        '(PinName="Coord",'
        'DesiredPinDirection=EGPD_Output)'
    )

    properties = _extract_properties(text, remove_nested_objects=False)

    pin_name = properties.get("PinName", "").strip('"')
    direction = properties.get("DesiredPinDirection", "")

    assert pin_name == "Coord"
    assert direction == "EGPD_Output"

def test_extract_user_defined_pin_directions():
    from app.parser import _extract_user_defined_pin_directions

    node_body = '''
    CustomProperties Pin (
        PinId=ABC,
        PinName="Coord",
        Direction="EGPD_Output",
    )
    CustomProperties UserDefinedPin (
        PinName="Coord",
        DesiredPinDirection=EGPD_Output
    )
    CustomProperties UserDefinedPin (
        PinName="WorldLocation",
        DesiredPinDirection=EGPD_Input
    )
    '''

    directions = _extract_user_defined_pin_directions(node_body)

    assert directions == {
        "Coord": "EGPD_Output",
        "WorldLocation": "EGPD_Input",
    }

def test_real_blueprint_user_defined_pin_directions():
    from pathlib import Path
    from app.parser import parse_blueprint_text

    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)

    entry_node = next(
        node for node in result["nodes"]
        if "K2Node_FunctionEntry" in node.node_class
    )
    result_node = next(
        node for node in result["nodes"]
        if "K2Node_FunctionResult" in node.node_class
    )

    coord_pin = next(
        pin for pin in entry_node.pins
        if pin.pin_name == "Coord"
    )
    world_location_pin = next(
        pin for pin in result_node.pins
        if pin.pin_name == "WorldLocation"
    )

    assert coord_pin.direction == "EGPD_Output"
    assert world_location_pin.direction == "EGPD_Input"

def test_user_defined_pin_direction_does_not_override_explicit_direction():
    from app.parser import BlueprintPin, _extract_user_defined_pin_directions

    node_body = '''
    CustomProperties UserDefinedPin (
        PinName="CustomValue",
        DesiredPinDirection=EGPD_Input
    )
    '''

    directions = _extract_user_defined_pin_directions(node_body)

    pin = BlueprintPin(
        pin_id="PIN_1",
        pin_name="CustomValue",
        direction="EGPD_Output",
        linked_to=[],
    )

    # Açık yön bilgisi, UserDefinedPin yönünden önceliklidir.
    assert pin.direction == "EGPD_Output"
    assert directions["CustomValue"] == "EGPD_Input"

def test_parser_fills_missing_pin_direction_from_user_defined_pin():
    from app.parser import parse_blueprint_text

    text = '''
    Begin Object Class=/Script/BlueprintGraph.K2Node_FunctionResult Name="ResultNode"
        CustomProperties Pin (
            PinId=PIN_WORLD,
            PinName="WorldLocation",
            LinkedTo=()
        )
        CustomProperties UserDefinedPin (
            PinName="WorldLocation",
            DesiredPinDirection=EGPD_Input
        )
    End Object
    '''

    result = parse_blueprint_text(text)

    pin = next(
        pin
        for node in result["nodes"]
        for pin in node.pins
        if pin.pin_name == "WorldLocation"
    )

    assert pin.direction == "EGPD_Input"

def test_user_defined_pin_directions_with_duplicate_names():
    from app.parser import _extract_user_defined_pin_directions

    node_body = '''
    CustomProperties UserDefinedPin (
        PinName="Value",
        DesiredPinDirection=EGPD_Input
    )
    CustomProperties UserDefinedPin (
        PinName="Value",
        DesiredPinDirection=EGPD_Output
    )
    '''

    directions = _extract_user_defined_pin_directions(node_body)

    # Mevcut davranışı belgeler: aynı isimdeki son kayıt kazanır.
    assert "Value" not in directions

def test_explicit_pin_direction_is_not_overwritten():
    from app.parser import BlueprintPin

    pin = BlueprintPin(
        pin_id="PIN_1",
        pin_name="Value",
        direction="EGPD_Output",
        linked_to=[],
    )

    user_pin_directions = {"Value": "EGPD_Input"}

    if not pin.direction and pin.pin_name in user_pin_directions:
        pin.direction = user_pin_directions[pin.pin_name]

    assert pin.direction == "EGPD_Output"

def test_parser_preserves_explicit_direction_over_user_defined_direction():
    from app.parser import parse_blueprint_text

    text = '''
    Begin Object Class=/Script/BlueprintGraph.K2Node_FunctionEntry Name="EntryNode"
        CustomProperties Pin (
            PinId=PIN_VALUE,
            PinName="Value",
            Direction="EGPD_Output",
            LinkedTo=()
        )
        CustomProperties UserDefinedPin (
            PinName="Value",
            DesiredPinDirection=EGPD_Input
        )
    End Object
    '''

    result = parse_blueprint_text(text)

    pin = next(
        pin
        for node in result["nodes"]
        for pin in node.pins
        if pin.pin_name == "Value"
    )

    assert pin.direction == "EGPD_Output"

def test_extract_unique_links_uses_explicit_pin_directions():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    output_pin = BlueprintPin(
        pin_id="PIN_OUT",
        pin_name="AnyCustomName",
        direction="EGPD_Output",
        linked_to=["NodeB:PIN_IN"],
    )

    input_pin = BlueprintPin(
        pin_id="PIN_IN",
        pin_name="AnotherCustomName",
        direction="EGPD_Input",
        linked_to=["NodeA:PIN_OUT"],
    )

    node_a = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNodeA",
        pins=[output_pin],
    )

    node_b = BlueprintNode(
        node_id="NodeB",
        node_class="CustomNodeB",
        pins=[input_pin],
    )

    links = extract_unique_links([node_a, node_b])

    assert links == [
        ("NodeA", "PIN_OUT", "NodeB", "PIN_IN")
    ]

def test_extract_unique_links_preserves_connection_with_unknown_directions():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    pin_a = BlueprintPin(
        pin_id="PIN_A",
        pin_name="CustomA",
        direction="",
        linked_to=["NodeB:PIN_B"],
    )
    pin_b = BlueprintPin(
        pin_id="PIN_B",
        pin_name="CustomB",
        direction="",
        linked_to=[],
    )

    node_a = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNodeA",
        pins=[pin_a],
    )
    node_b = BlueprintNode(
        node_id="NodeB",
        node_class="CustomNodeB",
        pins=[pin_b],
    )

    links = extract_unique_links([node_a, node_b])

    # Bağlantı korunur; ancak yönün doğru olduğu iddia edilmez.
    assert links == [
        ("NodeA", "PIN_A", "NodeB", "PIN_B")
    ]

def test_extract_unique_links_deduplicates_bidirectional_records():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    pin_a = BlueprintPin(
        pin_id="PIN_A",
        pin_name="CustomA",
        direction="EGPD_Output",
        linked_to=["NodeB:PIN_B"],
    )
    pin_b = BlueprintPin(
        pin_id="PIN_B",
        pin_name="CustomB",
        direction="EGPD_Input",
        linked_to=["NodeA:PIN_A"],
    )

    node_a = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNodeA",
        pins=[pin_a],
    )
    node_b = BlueprintNode(
        node_id="NodeB",
        node_class="CustomNodeB",
        pins=[pin_b],
    )

    
    links = extract_unique_links([node_a, node_b])

    assert links == [
        ("NodeA", "PIN_A", "NodeB", "PIN_B")
    ]

    # Node sırası değişse bile bağlantının yönü aynı kalmalı.
    reversed_links = extract_unique_links([node_b, node_a])

    assert reversed_links == [
        ("NodeA", "PIN_A", "NodeB", "PIN_B")
    ]



def test_extract_unique_links_ignores_missing_target_node_or_pin():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    pin_a = BlueprintPin(
        pin_id="PIN_A",
        pin_name="CustomA",
        direction="EGPD_Output",
        linked_to=[
            "MissingNode:PIN_X",
            "NodeB:MissingPin",
            "NodeB:PIN_B",
        ],
    )

    pin_b = BlueprintPin(
        pin_id="PIN_B",
        pin_name="CustomB",
        direction="EGPD_Input",
        linked_to=[],
    )

    node_a = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNodeA",
        pins=[pin_a],
    )
    node_b = BlueprintNode(
        node_id="NodeB",
        node_class="CustomNodeB",
        pins=[pin_b],
    )

    links = extract_unique_links([node_a, node_b])

    assert links == [
        ("NodeA", "PIN_A", "NodeB", "PIN_B")
    ]

def test_extract_unique_links_handles_self_link():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    pin = BlueprintPin(
        pin_id="PIN_A",
        pin_name="CustomA",
        direction="EGPD_Output",
        linked_to=["NodeA:PIN_A"],
    )

    node = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNode",
        pins=[pin],
    )

    links = extract_unique_links([node])

    assert links == [
        ("NodeA", "PIN_A", "NodeA", "PIN_A")
    ]

def test_real_blueprint_links_reference_existing_pins():
    from pathlib import Path
    from app.parser import parse_blueprint_text

    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)
    nodes = result["nodes"]

    node_ids = {node.node_id for node in nodes}
    pins_by_node = {
        node.node_id: {pin.pin_id for pin in node.pins}
        for node in nodes
    }

    for node in nodes:
        for pin in node.pins:
            for linked in pin.linked_to:
                assert ":" in linked, (
                    f"Beklenmeyen bağlantı biçimi: {linked}"
                )

                target_node_id, target_pin_id = linked.rsplit(":", 1)

                assert target_node_id in node_ids, (
                    f"Bağlantının hedef node'u bulunamadı: {linked}"
                )
                assert target_pin_id in pins_by_node[target_node_id], (
                    f"Bağlantının hedef pini bulunamadı: {linked}"
                )

def test_real_blueprint_known_link_directions_are_opposite():
    from pathlib import Path
    from app.parser import parse_blueprint_text, extract_unique_links

    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)
    nodes = result["nodes"]

    pins_by_node = {
        node.node_id: {pin.pin_id: pin for pin in node.pins}
        for node in nodes
    }

    links = extract_unique_links(nodes)

    checked_links = 0

    for source_node_id, source_pin_id, target_node_id, target_pin_id in links:
        source_pin = pins_by_node[source_node_id][source_pin_id]
        target_pin = pins_by_node[target_node_id][target_pin_id]

        source_direction = source_pin.direction.strip().strip('"')
        target_direction = target_pin.direction.strip().strip('"')

        # Yönü bilinmeyen bağlantıları doğrulanmış sayma.
        if not source_direction or not target_direction:
            continue

        assert source_direction == "EGPD_Output", (
            f"Kaynak pin çıkış değil: {source_node_id}:{source_pin_id} "
            f"({source_direction})"
        )
        assert target_direction == "EGPD_Input", (
            f"Hedef pin giriş değil: {target_node_id}:{target_pin_id} "
            f"({target_direction})"
        )

        checked_links += 1

    assert checked_links > 0, (
        "Gerçek dosyada yönü bilinen hiçbir bağlantı doğrulanamadı."
    )

def test_report_real_blueprint_pins_with_unknown_direction():
    from pathlib import Path
    from app.parser import parse_blueprint_text

    project_folder = Path(__file__).resolve().parent.parent
    sample_file = project_folder / "sample_blueprint.txt"
    raw_text = sample_file.read_text(encoding="utf-8")

    result = parse_blueprint_text(raw_text)

    unknown_pins = []

    for node in result["nodes"]:
        for pin in node.pins:
            direction = pin.direction.strip().strip('"')

            if direction not in ("EGPD_Input", "EGPD_Output"):
                unknown_pins.append(
                    (
                        node.node_id,
                        node.node_class,
                        pin.pin_id,
                        pin.pin_name,
                        direction,
                    )
                )

    print(f"\nYönü bilinmeyen pin sayısı: {len(unknown_pins)}")

    for item in unknown_pins[:30]:
        print(item)


def test_inspect_unknown_direction_pin_text():
    from pathlib import Path
    from app.parser import (
        parse_blueprint_text,
        _extract_pin_blocks,
        _extract_direction,
        _extract_object_blocks,
    )

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    result = parse_blueprint_text(raw_text)

    # Node ID -> ham node metni
    raw_nodes = {
        node_id: node_body
        for _, node_id, node_body in _extract_object_blocks(raw_text)
    }

    inspected = 0

    for node in result["nodes"]:
        raw_node = raw_nodes.get(node.node_id, "")

        for pin in node.pins:
            if pin.direction.strip().strip('"'):
                continue

            if inspected >= 5:
                break

            matching_block = next(
                (
                    block
                    for block in _extract_pin_blocks(raw_node)
                    if pin.pin_id in block
                ),
                None,
            )

            print(f"\n--- {node.node_class} | {pin.pin_name} ---")
            print(f"Pin ID: {pin.pin_id}")

            if matching_block is None:
                print("Ham pin kaydı bulunamadı.")
            else:
                print(f"Çıkarılan yön: {repr(_extract_direction(matching_block))}")
                print("Ham pin kaydı:")
                print(matching_block)

            inspected += 1

        if inspected >= 5:
            break

    assert inspected > 0, "İncelenecek pin bulunamadı."


def test_report_unknown_directions_by_node_class():
    from collections import Counter
    from pathlib import Path
    from app.parser import parse_blueprint_text

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    result = parse_blueprint_text(raw_text)

    counts = Counter()

    for node in result["nodes"]:
        for pin in node.pins:
            direction = pin.direction.strip().strip('"')

            if direction not in ("EGPD_Input", "EGPD_Output"):
                counts[node.node_class] += 1

    print("\nYönü bilinmeyen pinler node türüne göre:")

    for node_class, count in sorted(counts.items()):
        print(f"{node_class}: {count}")

    assert sum(counts.values()) > 0

def test_inspect_node_properties_for_unknown_pin_directions():
    from pathlib import Path
    from app.parser import parse_blueprint_text

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    result = parse_blueprint_text(raw_text)

    target_classes = {
        "/Script/BlueprintGraph.K2Node_CallFunction",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
    }

    inspected = 0

    for node in result["nodes"]:
        if node.node_class not in target_classes:
            continue

        unknown_pins = [
            pin for pin in node.pins
            if pin.direction.strip().strip('"')
            not in ("EGPD_Input", "EGPD_Output")
        ]

        if not unknown_pins:
            continue

        print(f"\n--- {node.node_class} | {node.node_id} ---")
        print("Node özellikleri:")

        for key, value in node.properties.items():
            print(f"  {key} = {value}")

        for pin in unknown_pins:
            print(
                f"  Bilinmeyen pin: {pin.pin_name!r}, "
                f"tip={pin.pin_type!r}, "
                f"özellikler={pin.properties}"
            )

        inspected += 1

        if inspected >= 2:
            break

    assert inspected > 0

def test_report_real_blueprint_link_direction_coverage():
    from pathlib import Path
    from app.parser import parse_blueprint_text, extract_unique_links

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    result = parse_blueprint_text(raw_text)
    nodes = result["nodes"]

    pins_by_node = {
        node.node_id: {pin.pin_id: pin for pin in node.pins}
        for node in nodes
    }

    links = extract_unique_links(nodes)

    known = 0
    unknown = 0

    for source_node_id, source_pin_id, target_node_id, target_pin_id in links:
        source_pin = pins_by_node[source_node_id][source_pin_id]
        target_pin = pins_by_node[target_node_id][target_pin_id]

        source_direction = source_pin.direction.strip().strip('"')
        target_direction = target_pin.direction.strip().strip('"')

        if (
            source_direction in ("EGPD_Input", "EGPD_Output")
            and target_direction in ("EGPD_Input", "EGPD_Output")
        ):
            assert source_direction != target_direction, (
                f"İki ucun yönü aynı: "
                f"{source_node_id}:{source_pin_id} "
                f"({source_direction}) -> "
                f"{target_node_id}:{target_pin_id} "
                f"({target_direction})"
            )
            known += 1
        else:
            unknown += 1
            print(
                f"\nYönü belirsiz bağlantı: "
                f"{source_node_id}:{source_pin_id} -> "
                f"{target_node_id}:{target_pin_id}"
            )

    print(f"\nToplam bağlantı: {len(links)}")
    print(f"İki ucu da bilinen bağlantı: {known}")
    print(f"En az bir ucu bilinmeyen bağlantı: {unknown}")

    assert len(links) == known + unknown

def test_inspect_unknown_link_pin_details():
    from pathlib import Path
    from app.parser import parse_blueprint_text, extract_unique_links

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    nodes = parse_blueprint_text(raw_text)["nodes"]

    pins_by_node = {
        node.node_id: {pin.pin_id: pin for pin in node.pins}
        for node in nodes
    }
    nodes_by_id = {node.node_id: node for node in nodes}

    for source_id, source_pin_id, target_id, target_pin_id in extract_unique_links(nodes):
        source_node = nodes_by_id[source_id]
        target_node = nodes_by_id[target_id]
        source_pin = pins_by_node[source_id][source_pin_id]
        target_pin = pins_by_node[target_id][target_pin_id]

        source_dir = source_pin.direction.strip().strip('"')
        target_dir = target_pin.direction.strip().strip('"')

        if source_dir and target_dir:
            continue

        print("\n--- BELİRSİZ BAĞLANTI ---")
        print(
            f"İlk uç: {source_node.node_class} / "
            f"{source_node.operation_name} / "
            f"{source_pin.pin_name} / "
            f"tür={source_pin.pin_type} / yön={source_dir or 'BİLİNMİYOR'}"
        )
        print(
            f"İkinci uç: {target_node.node_class} / "
            f"{target_node.operation_name} / "
            f"{target_pin.pin_name} / "
            f"tür={target_pin.pin_type} / yön={target_dir or 'BİLİNMİYOR'}"
        )

def test_inspect_promotable_operator_raw_pins():
    from pathlib import Path
    from app.parser import parse_blueprint_text, _extract_object_blocks, _extract_pin_blocks

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    result = parse_blueprint_text(raw_text)
    nodes = result["nodes"]

    raw_nodes = {
        node_id: body
        for _, node_id, body in _extract_object_blocks(raw_text)
    }

    for node in nodes:
        if not node.node_class.endswith("K2Node_PromotableOperator"):
            continue

        raw_node = raw_nodes.get(node.node_id, "")

        print(f"\n--- {node.node_id} ---")
        print(f"Operation: {node.operation_name}")

        for pin in node.pins:
            if pin.pin_name not in ("A", "B", "ReturnValue"):
                continue

            raw_pin = next(
                (
                    block
                    for block in _extract_pin_blocks(raw_node)
                    if f'PinId={pin.pin_id}' in block
                ),
                "",
            )

            print(
                f"\nPin: {pin.pin_name}, type={pin.pin_type}, "
                f"direction={pin.direction or 'BİLİNMİYOR'}"
            )
            print(raw_pin)

def test_inspect_unknown_call_function_pins():
    from pathlib import Path
    from app.parser import (
        parse_blueprint_text,
        _extract_object_blocks,
        _extract_pin_blocks,
    )

    project_folder = Path(__file__).resolve().parent.parent
    raw_text = (project_folder / "sample_blueprint.txt").read_text(
        encoding="utf-8"
    )

    nodes = parse_blueprint_text(raw_text)["nodes"]
    raw_nodes = {
        node_id: body
        for _, node_id, body in _extract_object_blocks(raw_text)
    }

    for node in nodes:
        if not node.node_class.endswith("K2Node_CallFunction"):
            continue

        unknown_pins = [
            pin for pin in node.pins
            if not pin.direction
        ]

        if not unknown_pins:
            continue

        print(f"\n--- {node.node_id} ---")
        print(f"Operation: {node.operation_name}")
        print(f"FunctionReference: {node.properties.get('FunctionReference', '')}")

        raw_node = raw_nodes.get(node.node_id, "")
        raw_pin_blocks = _extract_pin_blocks(raw_node)

        for pin in unknown_pins:
            raw_pin = next(
                (
                    block for block in raw_pin_blocks
                    if f"PinId={pin.pin_id}" in block
                ),
                "",
            )

            print(
                f"\nPin={pin.pin_name}, type={pin.pin_type}, "
                f"properties={pin.properties}"
            )
            print(raw_pin)

def test_extract_unique_links_deduplicates_self_links_between_different_pins():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    output_pin = BlueprintPin(
        pin_id="PIN_OUT",
        pin_name="Output",
        direction="EGPD_Output",
        linked_to=["NodeA:PIN_IN", "NodeA:PIN_IN"],
    )

    input_pin = BlueprintPin(
        pin_id="PIN_IN",
        pin_name="Input",
        direction="EGPD_Input",
        linked_to=["NodeA:PIN_OUT"],
    )

    node = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNode",
        pins=[output_pin, input_pin],
    )

    links = extract_unique_links([node])

    assert links == [
        ("NodeA", "PIN_OUT", "NodeA", "PIN_IN")
    ]

def test_extract_unique_links_preserves_unknown_direction_without_claiming_orientation():
    from app.parser import BlueprintNode, BlueprintPin, extract_unique_links

    pin_a = BlueprintPin(
        pin_id="PIN_A",
        pin_name="CustomA",
        direction="",
        linked_to=["NodeB:PIN_B"],
    )

    pin_b = BlueprintPin(
        pin_id="PIN_B",
        pin_name="CustomB",
        direction="",
        linked_to=["NodeA:PIN_A"],
    )

    node_a = BlueprintNode(
        node_id="NodeA",
        node_class="CustomNodeA",
        pins=[pin_a],
    )

    node_b = BlueprintNode(
        node_id="NodeB",
        node_class="CustomNodeB",
        pins=[pin_b],
    )

    links_forward = extract_unique_links([node_a, node_b])
    links_reversed = extract_unique_links([node_b, node_a])

    assert len(links_forward) == 1
    assert len(links_reversed) == 1

    # Her iki sırada da bağlantı korunmalı.
    # Ancak yön bilgisi bilinmediği için yönün aynı kalması şart değil.
    assert {
        frozenset((("NodeA", "PIN_A"), ("NodeB", "PIN_B")))
    } == {
        frozenset(((link[0], link[1]), (link[2], link[3])))
        for link in links_forward
    }

    assert {
        frozenset((("NodeA", "PIN_A"), ("NodeB", "PIN_B")))
    } == {
        frozenset(((link[0], link[1]), (link[2], link[3])))
        for link in links_reversed
    }
def test_extract_object_blocks_finds_nested_objects():
    from app.parser import _extract_object_blocks

    source = '''
Begin Object Class=OuterClass Name="Outer"
    OuterProperty=1
    Begin Object Class=InnerClass Name="Inner"
        InnerProperty=2
    End Object
End Object
'''

    objects = _extract_object_blocks(source)

    assert objects == [
        (
            "OuterClass",
            "Outer",
            '''
    OuterProperty=1
    Begin Object Class=InnerClass Name="Inner"
        InnerProperty=2
    End Object
''',
        ),
        (
            "InnerClass",
            "Inner",
            '''
        InnerProperty=2
    ''',
        ),
    ]
def test_extract_object_blocks_ignores_object_keywords_inside_quotes():
    from app.parser import _extract_object_blocks

    source = '''
Begin Object Class=TestClass Name="TestNode"
    Description="Begin Object Class=Fake Name=\"FakeNode\""
    Comment="End Object"
End Object
'''

    objects = _extract_object_blocks(source)

    assert len(objects) == 1
    assert objects[0][0] == "TestClass"
    assert objects[0][1] == "TestNode"
def test_extract_object_blocks_tracks_invalid_nested_object():
    from app.parser import _extract_object_blocks

    source = '''
Begin Object Class=OuterClass Name="Outer"
    Begin Object InvalidHeader
        InnerProperty=2
    End Object
    OuterProperty=3
End Object
'''

    objects = _extract_object_blocks(source)

    assert len(objects) == 1
    assert objects[0][0] == "OuterClass"
    assert objects[0][1] == "Outer"
    assert "OuterProperty=3" in objects[0][2]
    assert "InnerProperty=2" in objects[0][2]
def test_extract_object_blocks_ignores_unclosed_objects():
    from app.parser import _extract_object_blocks

    source = '''
Begin Object Class=ValidClass Name="Valid"
    ValidProperty=1
End Object

Begin Object Class=UnclosedClass Name="Unclosed"
    UnclosedProperty=2
'''

    objects = _extract_object_blocks(source)

    assert len(objects) == 1
    assert objects[0][0] == "ValidClass"
    assert objects[0][1] == "Valid"
def test_get_node_operation_uses_operation_name_first():
    from app.parser import _get_node_operation

    result = _get_node_operation(
        "K2Node_CallFunction",
        {
            "OperationName": '"MyOperation"',
            "FunctionReference": '(MemberName="MakeVector")',
        },
    )

    assert result == "MyOperation"


def test_get_node_operation_reads_function_member_name():
    from app.parser import _get_node_operation

    result = _get_node_operation(
        "K2Node_CallFunction",
        {
            "FunctionReference": '(MemberName="MakeVector")',
        },
    )

    assert result == "MakeVector"


def test_get_node_operation_recognizes_known_node_classes():
    from app.parser import _get_node_operation

    node_classes = {
        "K2Node_FunctionEntry": "FunctionEntry",
        "K2Node_FunctionResult": "FunctionResult",
        "K2Node_VariableGet": "VariableGet",
        "K2Node_VariableSet": "VariableSet",
        "K2Node_BreakStruct": "BreakStruct",
        "K2Node_MakeStruct": "MakeStruct",
    }

    for node_class, expected in node_classes.items():
        assert _get_node_operation(node_class, {}) == expected


def test_get_node_operation_returns_empty_for_unknown_node():
    from app.parser import _get_node_operation

    result = _get_node_operation(
        "K2Node_Unknown",
        {},
    )

    assert result == ""
def test_extract_pin_blocks_ignores_nested_object_pins():
    from app.parser import _extract_pin_blocks

    node_body = '''
CustomProperties Pin (
    PinId=OUTER_PIN,
    PinName="OuterPin"
)

Begin Object Class=InnerClass Name="Inner"
    CustomProperties Pin (
        PinId=INNER_PIN,
        PinName="InnerPin"
    )
End Object

CustomProperties Pin (
    PinId=ANOTHER_OUTER_PIN,
    PinName="AnotherOuterPin"
)
'''

    pins = _extract_pin_blocks(node_body)

    assert len(pins) == 2
    assert "OUTER_PIN" in pins[0]
    assert "ANOTHER_OUTER_PIN" in pins[1]
    assert all("INNER_PIN" not in pin for pin in pins)
def test_extract_pin_blocks_handles_parentheses_inside_quotes():
    from app.parser import _extract_pin_blocks

    node_body = '''
CustomProperties Pin (
    PinId=TEST_PIN,
    PinName="TestPin",
    DefaultValue="Text with (parentheses)"
)
'''

    pins = _extract_pin_blocks(node_body)

    assert len(pins) == 1
    assert "TEST_PIN" in pins[0]
    assert 'DefaultValue="Text with (parentheses)"' in pins[0]
def test_extract_pin_blocks_handles_escaped_quotes():
    from app.parser import _extract_pin_blocks

    node_body = r'''
CustomProperties Pin (
    PinId=TEST_PIN,
    PinName="TestPin",
    DefaultValue="Text with \"quoted\" words"
)
'''

    pins = _extract_pin_blocks(node_body)

    assert len(pins) == 1
    assert "TEST_PIN" in pins[0]
    assert r'\"quoted\"' in pins[0]
def test_extract_pin_blocks_ignores_object_keywords_with_suffixes():
    from app.parser import _extract_pin_blocks

    node_body = '''
Begin ObjectExtra
CustomProperties Pin (
    PinId=TEST_PIN,
    PinName="TestPin"
)
End ObjectExtra
'''

    pins = _extract_pin_blocks(node_body)

    assert len(pins) == 1
    assert "TEST_PIN" in pins[0]
def test_extract_user_defined_pin_directions_ignores_object_keywords_with_suffixes():
    from app.parser import _extract_user_defined_pin_directions

    node_body = '''
Begin ObjectExtra

CustomProperties UserDefinedPin (
    PinName="TestPin",
    DesiredPinDirection=EGPD_Input
)

End ObjectExtra
'''

    directions = _extract_user_defined_pin_directions(node_body)

    assert directions == {
        "TestPin": "EGPD_Input"
    }
def test_extract_user_defined_pin_directions_ignores_ambiguous_names():
    from app.parser import _extract_user_defined_pin_directions

    node_body = '''
CustomProperties UserDefinedPin (
    PinName="TestPin",
    DesiredPinDirection=EGPD_Input
)

CustomProperties UserDefinedPin (
    PinName="TestPin",
    DesiredPinDirection=EGPD_Output
)

CustomProperties UserDefinedPin (
    PinName="SafePin",
    DesiredPinDirection=EGPD_Input
)
'''

    directions = _extract_user_defined_pin_directions(node_body)

    assert "TestPin" not in directions
    assert directions == {
        "SafePin": "EGPD_Input"
    }
def test_extract_user_defined_pin_directions_ignores_invalid_directions():
    from app.parser import _extract_user_defined_pin_directions

    node_body = '''
CustomProperties UserDefinedPin (
    PinName="ValidPin",
    DesiredPinDirection=EGPD_Input
)

CustomProperties UserDefinedPin (
    PinName="InvalidPin",
    DesiredPinDirection=EGPD_MAX
)
'''

    directions = _extract_user_defined_pin_directions(node_body)

    assert directions == {
        "ValidPin": "EGPD_Input"
    }

    assert "InvalidPin" not in directions
def test_extract_user_defined_pin_directions_accepts_repeated_same_direction():
    from app.parser import _extract_user_defined_pin_directions

    node_body = '''
CustomProperties UserDefinedPin (
    PinName="TestPin",
    DesiredPinDirection=EGPD_Input
)

CustomProperties UserDefinedPin (
    PinName="TestPin",
    DesiredPinDirection=EGPD_Input
)
'''

    directions = _extract_user_defined_pin_directions(node_body)

    assert directions == {
        "TestPin": "EGPD_Input"
    }
def test_parse_pin_content_handles_nested_parentheses():
    from app.parser import _parse_pin_content

    node_body = '(PinName="Test", Nested=(A=(B=C)))'

    result = _parse_pin_content(node_body, 1)

    assert result == 'PinName="Test", Nested=(A=(B=C))'
def test_parse_pin_content_ignores_parentheses_inside_quotes():
    from app.parser import _parse_pin_content

    node_body = '(PinName="Test", DefaultValue="Text (Example)")'

    result = _parse_pin_content(node_body, 1)

    assert result == 'PinName="Test", DefaultValue="Text (Example)"'
def test_parse_pin_content_handles_escaped_quotes():
    from app.parser import _parse_pin_content

    node_body = r'(PinName="Test", DefaultValue="Text with \"quoted\" words")'

    result = _parse_pin_content(node_body, 1)

    assert result == r'PinName="Test", DefaultValue="Text with \"quoted\" words"'
def test_parse_pin_content_returns_empty_for_unclosed_block():
    from app.parser import _parse_pin_content

    node_body = '(PinName="Test", Nested=(A=(B=C))'

    result = _parse_pin_content(node_body, 1)

    assert result == ""
def test_parse_pin_content_stops_at_matching_closing_parenthesis():
    from app.parser import _parse_pin_content

    node_body = '(PinName="Test") EXTRA_DATA'

    result = _parse_pin_content(node_body, 1)

    assert result == 'PinName="Test"'
    assert "EXTRA_DATA" not in result
def test_extract_value_handles_escaped_quotes():
    from app.parser import _extract_value

    text = r'DefaultValue="Text with \"quoted\" words", Other=123'

    result = _extract_value(text, "DefaultValue")

    assert result == r'Text with \"quoted\" words'
def test_extract_value_reads_normal_quoted_value():
    from app.parser import _extract_value

    text = 'PinName="ReturnValue", Other=123'

    assert _extract_value(text, "PinName") == "ReturnValue"


def test_extract_value_reads_unquoted_value():
    from app.parser import _extract_value

    text = "PinId=ABC123, Other=456"

    assert _extract_value(text, "PinId") == "ABC123"
def test_extract_friendly_name_handles_escaped_quotes():
    from app.parser import _extract_friendly_name

    text = r'PinFriendlyName="Text with \"quoted\" words", Other=123'

    result = _extract_friendly_name(text)

    assert result == r'Text with \"quoted\" words'
def test_extract_friendly_name_reads_normal_quoted_value():
    from app.parser import _extract_friendly_name

    text = 'PinFriendlyName="Return Value", Other=123'

    assert _extract_friendly_name(text) == "Return Value"


def test_extract_friendly_name_reads_nsloctext_value():
    from app.parser import _extract_friendly_name

    text = (
        'PinFriendlyName=NSLOCTEXT("Namespace", '
        '"Key", "Display Name"), Other=123'
    )

    assert (
        _extract_friendly_name(text)
        == 'NSLOCTEXT("Namespace", "Key", "Display Name")'
    )
def test_parse_linked_to_extracts_multiple_connections():
    from app.parser import _parse_linked_to

    pin_text = """
    LinkedTo=(
        NodeA 0123456789ABCDEF0123456789ABCDEF,
        NodeB ABCDEF0123456789ABCDEF0123456789
    )
    """

    result = _parse_linked_to(pin_text)

    assert result == [
        "NodeA:0123456789ABCDEF0123456789ABCDEF",
        "NodeB:ABCDEF0123456789ABCDEF0123456789",
    ]
def test_parse_linked_to_ignores_invalid_connections():
    from app.parser import _parse_linked_to

    pin_text = """
    LinkedTo=(
        NodeA 0123456789ABCDEF0123456789ABCDEF,
        NodeB INVALID_PIN_ID,
        NodeC 0123456789ABCDEF,
        NodeD GHIJKLMNOPQRSTUVWXYZ1234567890
    )
    """

    result = _parse_linked_to(pin_text)

    assert result == [
        "NodeA:0123456789ABCDEF0123456789ABCDEF"
    ]
def test_parse_linked_to_preserves_duplicate_connections():
    from app.parser import _parse_linked_to

    pin_text = """
    LinkedTo=(
        NodeA 0123456789ABCDEF0123456789ABCDEF,
        NodeA 0123456789ABCDEF0123456789ABCDEF
    )
    """

    result = _parse_linked_to(pin_text)

    assert result == [
        "NodeA:0123456789ABCDEF0123456789ABCDEF",
        "NodeA:0123456789ABCDEF0123456789ABCDEF",
    ]
def test_parse_linked_to_handles_empty_connections():
    from app.parser import _parse_linked_to

    pin_text = "LinkedTo=()"

    result = _parse_linked_to(pin_text)

    assert result == []
def test_parse_linked_to_ignores_connections_inside_quotes():
    from app.parser import _parse_linked_to

    pin_text = '''
    LinkedTo=(
        NodeA 0123456789ABCDEF0123456789ABCDEF,
        "FakeNode ABCDEF0123456789ABCDEF0123456789"
    )
    '''

    result = _parse_linked_to(pin_text)

    assert result == [
        "NodeA:0123456789ABCDEF0123456789ABCDEF"
    ]
def test_extract_parenthesized_value_handles_nested_parentheses():
    from app.parser import _extract_parenthesized_value

    text = 'TestKey=(First=(Second=Value), Third=Value)'

    result = _extract_parenthesized_value(text, "TestKey")

    assert result == "First=(Second=Value), Third=Value"
def test_extract_parenthesized_value_ignores_parentheses_inside_quotes():
    from app.parser import _extract_parenthesized_value

    text = 'TestKey=(First="Value (inside)", Second=Value)'

    result = _extract_parenthesized_value(text, "TestKey")

    assert result == 'First="Value (inside)", Second=Value'
def test_extract_parenthesized_value_handles_escaped_quotes():
    from app.parser import _extract_parenthesized_value

    text = r'TestKey=(First="Value with \" (parenthesis)", Second=Value)'

    result = _extract_parenthesized_value(text, "TestKey")

    assert result == r'First="Value with \" (parenthesis)", Second=Value'
def test_extract_parenthesized_value_returns_empty_for_unclosed_parentheses():
    from app.parser import _extract_parenthesized_value

    text = "TestKey=(First=Value"

    result = _extract_parenthesized_value(text, "TestKey")

    assert result == ""
def test_extract_pin_id_reads_pin_id():
    from app.parser import _extract_pin_id

    pin_text = 'PinId="ABCDEF0123456789ABCDEF0123456789"'

    assert _extract_pin_id(pin_text) == "ABCDEF0123456789ABCDEF0123456789"
def test_extract_pin_name_reads_pin_name():
    from app.parser import _extract_pin_name

    pin_text = 'PinName="WorldLocation"'

    assert _extract_pin_name(pin_text) == "WorldLocation"


def test_extract_direction_reads_direction():
    from app.parser import _extract_direction

    pin_text = 'Direction="EGPD_Output"'

    assert _extract_direction(pin_text) == "EGPD_Output"
def test_extract_pin_friendly_name_reads_value():
    from app.parser import _extract_pin_friendly_name

    pin_text = 'PinFriendlyName="World Location"'

    assert _extract_pin_friendly_name(pin_text) == "World Location"
def test_extract_pin_type_reads_category_and_subcategory():
    from app.parser import _extract_pin_type

    pin_text = (
        'PinType.PinCategory="struct", '
        'PinType.PinSubCategory="F_HexCoord"'
    )

    assert _extract_pin_type(pin_text) == ("struct", "F_HexCoord")
def test_extract_pin_type_handles_missing_subcategory():
    from app.parser import _extract_pin_type

    pin_text = 'PinType.PinCategory="exec"'

    assert _extract_pin_type(pin_text) == ("exec", "")
def test_extract_default_value_reads_normal_value():
    from app.parser import _extract_default_value

    pin_text = 'DefaultValue="Hello World"'

    assert _extract_default_value(pin_text) == "Hello World"
def test_extract_default_value_handles_empty_value():
    from app.parser import _extract_default_value

    assert _extract_default_value("DefaultValue=") == ""


def test_extract_default_value_handles_unquoted_value():
    from app.parser import _extract_default_value

    assert _extract_default_value("DefaultValue=123") == "123"


def test_extract_default_value_handles_escaped_quotes():
    from app.parser import _extract_default_value

    pin_text = r'DefaultValue="Text with \"quoted\" words"'

    assert _extract_default_value(pin_text) == r'Text with \"quoted\" words'
def test_remove_pin_blocks_ignores_similar_names():
    from app.parser import _remove_pin_blocks

    text = "CustomProperties PinExtra (SomeValue=123)"

    result = _remove_pin_blocks(text)

    assert result == text
def test_remove_pin_blocks_preserves_other_properties():
    from app.parser import _remove_pin_blocks

    text = '''
    NodeGuid="ABC123"
    CustomProperties Pin (
        PinId=123,
        PinName="Value"
    )
    OperationName="SomeOperation"
    '''

    result = _remove_pin_blocks(text)

    assert 'NodeGuid="ABC123"' in result
    assert 'OperationName="SomeOperation"' in result
    assert "PinId=123" not in result
    assert 'PinName="Value"' not in result
def test_extract_properties_preserves_unknown_properties():
    from app.parser import _extract_properties

    text = (
        'CustomField="CustomValue", '
        'ObjectData="SomeData", '
        'AnotherUnknownField=123'
    )

    properties = _extract_properties(text)

    assert properties["CustomField"] == '"CustomValue"'
    assert properties["ObjectData"] == '"SomeData"'
    assert properties["AnotherUnknownField"] == "123"
def test_extract_properties_ignores_nested_object_properties():
    from app.parser import _extract_properties

    text = '''
    NodeName="MainNode"
    Begin Object Class=SomeClass Name="NestedObject"
        NestedOnlyProperty="ShouldNotAppear"
    End Object
    CustomField="PreservedValue"
    '''

    properties = _extract_properties(text)

    assert properties["NodeName"] == '"MainNode"'
    assert properties["CustomField"] == '"PreservedValue"'
    assert "NestedOnlyProperty" not in properties
def test_extract_properties_ignores_property_like_text_inside_quotes():
    from app.parser import _extract_properties

    text = (
        'Description="FakeField=123, AnotherFake=value", '
        'RealField="ActualValue"'
    )

    properties = _extract_properties(text)

    assert "Description" in properties
    assert "RealField" in properties
    assert "FakeField" not in properties
    assert "AnotherFake" not in properties
def test_should_ignore_char_handles_escaped_character():
    from app.parser import _should_ignore_char

    result = _should_ignore_char("n", True, True)
    assert result == (True, True, False)


def test_should_ignore_char_starts_escape_inside_quotes():
    from app.parser import _should_ignore_char

    result = _should_ignore_char("\\", True, False)

    assert result == (True, True, True)


def test_should_ignore_char_toggles_quote_state():
    from app.parser import _should_ignore_char

    result = _should_ignore_char('"', False, False)

    assert result == (True, True, False)


def test_should_ignore_char_preserves_parentheses_outside_quotes():
    from app.parser import _should_ignore_char

    result = _should_ignore_char("(", False, False)

    assert result == (False, False, False)
def test_extract_friendly_name_ignores_similar_property_names():
    from app.parser import _extract_friendly_name

    text = 'CustomPinFriendlyName="Wrong", OtherField="Value"'

    assert _extract_friendly_name(text) == ""

def test_extract_parenthesized_value_ignores_qualified_property_name():
    from app.parser import _extract_parenthesized_value

    text = 'Other.LinkedTo=(FakeValue)'

    assert _extract_parenthesized_value(text, "LinkedTo") == ""

def test_extract_properties_ignores_nested_properties():
    from app.parser import _extract_properties

    text = (
        'Name="Outer", '
        'Settings=(Name="Inner", Value=123), '
        'Enabled=True'
    )

    properties = _extract_properties(
        text,
        remove_nested_objects=False,
    )

    assert properties["Name"] == '"Outer"'
    assert properties["Enabled"] == "True"
    assert "Value" not in properties

def test_should_ignore_char_handles_escaped_quote():
    from app.parser import _should_ignore_char

    result = _should_ignore_char("\\", True, False)
    assert result == (True, True, True)

    result = _should_ignore_char('"', True, True)
    assert result == (True, True, False)


def test_should_ignore_char_ignores_newline_outside_quotes():
    from app.parser import _should_ignore_char

    assert _should_ignore_char("\n", False, False) == (
        True,
        False,
        False,
    )


def test_extract_pin_basic_fields():
    from app.parser import (
        _extract_pin_id,
        _extract_pin_name,
        _extract_direction,
    )

    pin_text = (
        'PinId=0123456789ABCDEF0123456789ABCDEF, '
        'PinName="Target", '
        'Direction="EGPD_Input"'
    )

    assert _extract_pin_id(pin_text) == "0123456789ABCDEF0123456789ABCDEF"
    assert _extract_pin_name(pin_text) == "Target"
    assert _extract_direction(pin_text) == "EGPD_Input"

def test_extract_pin_type_and_default_fields():
    from app.parser import (
        _extract_pin_friendly_name,
        _extract_pin_type,
        _extract_default_value,
    )

    pin_text = (
        'PinFriendlyName="Target Position", '
        'PinType.PinCategory="struct", '
        'PinType.PinSubCategory="Vector", '
        'DefaultValue="X=10 Y=20 Z=30"'
    )

    assert _extract_pin_friendly_name(pin_text) == "Target Position"
    assert _extract_pin_type(pin_text) == ("struct", "Vector")
    assert _extract_default_value(pin_text) == "X=10 Y=20 Z=30"
def test_infer_pin_direction_does_not_assume_specific_struct_name():
    from app.parser import _infer_pin_direction

    assert _infer_pin_direction(
        "K2Node_BreakStruct",
        "ObjectData",
    ) == ""
def test_parse_property_value_preserves_unclosed_value():
    from app.parser import _parse_property_value

    text = 'Settings=(Value=123'

    pos, value = _parse_property_value(text, 9, len(text))

    assert pos == len(text)
    assert value == "(Value=123"

def test_parse_pin_preserves_raw_properties():
    from app.parser import _parse_pin

    pin_text = (
        'PinId=0123456789ABCDEF0123456789ABCDEF, '
        'PinName="Location", '
        'Direction="EGPD_Input", '
        'PinType.PinCategory="struct", '
        'PinType.PinSubCategory="Vector", '
        'DefaultValue="X=10 Y=20 Z=30"'
    )

    pin = _parse_pin(pin_text)

    assert pin.pin_name == "Location"
    assert pin.direction == "EGPD_Input"
    assert pin.pin_type == "struct:Vector"
    assert pin.default_value == "X=10 Y=20 Z=30"
    assert pin.properties["PinType.PinCategory"] == '"struct"'
    assert pin.properties["PinType.PinSubCategory"] == '"Vector"'

def test_parse_blueprint_text_preserves_multiple_nodes():
    from app.parser import parse_blueprint_text

    text = """
Begin Object Class=/Script/BlueprintGraph.K2Node_VariableGet Name="Node_A"
    NodeGuid=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
End Object

Begin Object Class=/Script/BlueprintGraph.K2Node_VariableSet Name="Node_B"
    NodeGuid=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
End Object
"""

    result = parse_blueprint_text(text)

    assert result["node_count"] == 2
    assert result["pin_count"] == 0
    assert len(result["nodes"]) == 2
    assert result["nodes"][0].node_id == "Node_A"
    assert result["nodes"][1].node_id == "Node_B"
    assert result["raw_text"] == text
    assert result["character_count"] == len(text)
    