
import time
from app.parser import _extract_properties
from app.parser import (
    parse_blueprint_text,
    _remove_nested_object_blocks,
)


def test_parser_performance_baseline():
    node_template = """
Begin Object Class=/Script/BlueprintGraph.K2Node_Test Name="TestNode"
    NegativeValue=-25
    FloatValue=346.41
    BooleanValue=True
    TextValue="Mode=Advanced, (Count=3)"
    VectorValue=(X=1,Y=2,Z=3)
    FunctionReference=(MemberName="TestFunction",bSelfContext=True)
End Object
"""

    text = node_template * 500

    # İlk çalıştırma: Python ve parser için ısınma.
    warmup_result = parse_blueprint_text(text)
    assert warmup_result["node_count"] == 500

    # Aynı metni 10 kez ölç.
    durations = []

    for _ in range(10):
        start = time.perf_counter()
        result = parse_blueprint_text(text)
        elapsed = time.perf_counter() - start

        assert result["node_count"] == 500
        durations.append(elapsed)

    average = sum(durations) / len(durations)
    fastest = min(durations)
    slowest = max(durations)

    print(f"\nÖlçüm sayısı: {len(durations)}")
    print(f"Ortalama süre: {average:.4f} saniye")
    print(f"En kısa süre: {fastest:.4f} saniye")
    print(f"En uzun süre: {slowest:.4f} saniye")
def test_nested_object_removal_performance():
    text = """
Begin Object Class=/Script/Engine.Actor Name="OuterObject"
    Description="Example Begin Object and End Object text"
    Begin Object Class=/Script/Engine.Component Name="InnerObject"
        Value=123
    End Object
    FinalValue=456
End Object
""" * 500

    # Isınma
    _remove_nested_object_blocks(text)

    durations = []

    for _ in range(10):
        start = time.perf_counter()
        result = _remove_nested_object_blocks(text)
        durations.append(time.perf_counter() - start)

    average = sum(durations) / len(durations)

    assert isinstance(result, str)
    print(f"\nNesne temizleme ortalaması: {average:.4f} saniye")
def test_property_extraction_cleaning_performance():
    text = """
    Value=123
    Description="Example text"
    FunctionReference=(MemberName="TestFunction",bSelfContext=True)
    """ * 500

    # Isınma
    _extract_properties(text)
    _extract_properties(text, remove_nested_objects=False)

    cleaning_durations = []
    no_cleaning_durations = []

    for _ in range(10):
        start = time.perf_counter()
        _extract_properties(text, remove_nested_objects=True)
        cleaning_durations.append(time.perf_counter() - start)

        start = time.perf_counter()
        _extract_properties(text, remove_nested_objects=False)
        no_cleaning_durations.append(time.perf_counter() - start)

    cleaning_average = sum(cleaning_durations) / len(cleaning_durations)
    no_cleaning_average = sum(no_cleaning_durations) / len(no_cleaning_durations)

    print(f"\nTemizlemeli ortalama: {cleaning_average:.4f} saniye")
    print(f"Temizlemesiz ortalama: {no_cleaning_average:.4f} saniye")