
from app.parser import (
    BlueprintLink,
    BlueprintNode,
    BlueprintPin,
    build_blueprint_analysis,
)


def make_pin(pin_id, name, default="", direction=""):
    return BlueprintPin(
        pin_id=pin_id,
        pin_name=name,
        default_value=default,
        direction=direction,
    )


def make_node(node_id, node_class, pins, operation=""):
    return BlueprintNode(
        node_id=node_id,
        node_class=node_class,
        pins=pins,
        operation_name=operation,
    )


def test_multiply_resolves_connected_source_pin():
    entry = make_node(
        "Entry",
        "/Script/BlueprintGraph.K2Node_FunctionEntry",
        [make_pin("q", "Q", direction="EGPD_Output")],
    )
    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "346.410000"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink("Entry", "q", "Multiply", "a"),
    ]

    result = build_blueprint_analysis([entry, multiply], links)

    assert any(
        "(Q * 346.410000)" in line
        for line in result
    )


def test_unconnected_inputs_keep_their_default_values():
    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A", "1"),
            make_pin("b", "B", "300"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    result = build_blueprint_analysis([multiply], [])

    assert any("(1 * 300)" in line for line in result)


def test_add_resolves_both_connected_inputs():
    entry = make_node(
        "Entry",
        "/Script/BlueprintGraph.K2Node_FunctionEntry",
        [
            make_pin("q", "Q", direction="EGPD_Output"),
            make_pin("r", "R", direction="EGPD_Output"),
        ],
    )
    add = make_node(
        "Add",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Add",
    )

    links = [
        BlueprintLink("Entry", "q", "Add", "a"),
        BlueprintLink("Entry", "r", "Add", "b"),
    ]

    result = build_blueprint_analysis([entry, add], links)

    assert any("(Q + R)" in line for line in result)

def test_conversion_node_resolves_its_input():
    entry = make_node(
        "Entry",
        "/Script/BlueprintGraph.K2Node_FunctionEntry",
        [make_pin("q", "Q", direction="EGPD_Output")],
    )
    conversion = make_node(
        "Convert",
        "/Script/BlueprintGraph.K2Node_CallFunction",
        [
            make_pin("input", "InInt"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Conv_IntToDouble",
    )
    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "346.410000"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink("Entry", "q", "Convert", "input"),
        BlueprintLink("Convert", "out", "Multiply", "a"),
    ]

    result = build_blueprint_analysis(
        [entry, conversion, multiply],
        links,
    )

    assert any(
        "(Q * 346.410000)" in line
        for line in result
    )


def test_make_vector_resolves_x_y_and_z():
    make_vector = make_node(
        "Vector",
        "/Script/BlueprintGraph.K2Node_CallFunction",
        [
            make_pin("x", "X", "10.0"),
            make_pin("y", "Y", "20.0"),
            make_pin("z", "Z", "0.0"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "MakeVector",
    )
    result_node = make_node(
        "Result",
        "/Script/BlueprintGraph.K2Node_FunctionResult",
        [make_pin("location", "WorldLocation")],
    )

    links = [
        BlueprintLink("Vector", "out", "Result", "location"),
    ]

    result = build_blueprint_analysis(
        [make_vector, result_node],
        links,
    )

    assert any(
        "Vector(X=10.0, Y=20.0, Z=0.0)" in line
        for line in result
    )


def test_unconnected_inputs_do_not_create_fake_source_links():
    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A", "2"),
            make_pin("b", "B", "5"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    result = build_blueprint_analysis([multiply], [])

    assert any("(2 * 5)" in line for line in result)
    assert not any("[Pin bulunamadı]" in line for line in result)

def test_circular_connection_is_detected():
    node_a = make_node(
        "A",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "1"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Add",
    )
    node_b = make_node(
        "B",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "2"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink("A", "out", "B", "a"),
        BlueprintLink("B", "out", "A", "a"),
    ]

    result = build_blueprint_analysis([node_a, node_b], links)

    assert any("[Döngü]" in line for line in result)

def test_missing_connected_source_is_reported():
    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "5"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink("MissingNode", "missing_pin", "Multiply", "a"),
    ]

    result = build_blueprint_analysis([multiply], links)

    assert any("[Pin bulunamadı]" in line for line in result)


def test_unknown_operation_is_not_silently_simplified():
    unknown = make_node(
        "Unknown",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A", "2"),
            make_pin("b", "B", "3"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "UnknownOperation",
    )

    result = build_blueprint_analysis([unknown], [])
    print("TEST OPERATION NAME:", repr(unknown.operation_name))
    print("\n--- UNKNOWN OPERATION ANALYSIS ---")
    print("\n".join(result))
    assert any("UnknownOperation" in line for line in result), repr(result)

def test_unknown_direction_link_is_not_used():
    entry = make_node(
        "Entry",
        "/Script/BlueprintGraph.K2Node_FunctionEntry",
        [make_pin("q", "Q", direction="EGPD_Output")],
    )

    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A", "2"),
            make_pin("b", "B", "5"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink(
            "Entry",
            "q",
            "Multiply",
            "a",
            direction_known=False,
        ),
    ]

    result = build_blueprint_analysis(
        [entry, multiply],
        links,
    )

    assert any("(2 * 5)" in line for line in result)
    assert not any("(Q * 5)" in line for line in result)
def test_unsupported_node_keeps_its_original_identity():
    unknown = make_node(
        "GetLocation",
        "/Script/BlueprintGraph.K2Node_CallFunction",
        [
            make_pin(
                "out",
                "ReturnValue",
                direction="EGPD_Output",
            ),
        ],
        "GetActorLocation",
    )

    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "2"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink("GetLocation", "out", "Multiply", "a"),
    ]

    result = build_blueprint_analysis(
        [unknown, multiply],
        links,
    )

    assert any(
        "GetActorLocation.ReturnValue" in line
        for line in result
    )

def test_break_struct_resolves_struct_field():
    entry = make_node(
        "Entry",
        "/Script/BlueprintGraph.K2Node_FunctionEntry",
        [
            make_pin(
                "transform",
                "Transform",
                direction="EGPD_Output",
            ),
        ],
    )

    break_struct = make_node(
        "Break",
        "/Script/BlueprintGraph.K2Node_BreakStruct",
        [
            BlueprintPin(
                pin_id="struct",
                pin_name="Struct",
                pin_type="struct:Transform",
            ),
            make_pin(
                "location",
                "Location",
                direction="EGPD_Output",
            ),
        ],
    )

    multiply = make_node(
        "Multiply",
        "/Script/BlueprintGraph.K2Node_PromotableOperator",
        [
            make_pin("a", "A"),
            make_pin("b", "B", "2"),
            make_pin("out", "ReturnValue", direction="EGPD_Output"),
        ],
        "Multiply",
    )

    links = [
        BlueprintLink("Entry", "transform", "Break", "struct"),
        BlueprintLink("Break", "location", "Multiply", "a"),
    ]

    result = build_blueprint_analysis(
        [entry, break_struct, multiply],
        links,
    )

    assert any(
        "(Transform.Location * 2)" in line
        for line in result
    )
