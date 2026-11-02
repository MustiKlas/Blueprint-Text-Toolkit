
import re
_PROPERTY_KEY_PATTERN = re.compile(
    r'(?<![\w.])([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*='
)
from dataclasses import dataclass, field
from app.node_registry import get_node_behavior

@dataclass(frozen=True)
class BlueprintLink:
    source_node_id: str
    source_pin_id: str
    target_node_id: str
    target_pin_id: str
    direction_known: bool = True



@dataclass
class BlueprintPin:
    pin_id: str = ""
    pin_name: str = ""
    pin_friendly_name: str = ""
    pin_type: str = ""
    default_value: str = ""
    direction: str = ""
    linked_to: list[str] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)



@dataclass
class BlueprintNode:
    node_id: str = ""
    node_class: str = ""
    pins: list[BlueprintPin] = field(default_factory=list)
    operation_name: str = ""
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class BlueprintAnalysisPin:
    pin_id: str
    name: str
    direction: str
    pin_type: str
    default_value: str
    incoming: list[tuple[str, str]] = field(default_factory=list)
    outgoing: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class BlueprintAnalysisNode:
    node_id: str
    node_class: str
    operation_name: str
    pins: list[BlueprintAnalysisPin] = field(default_factory=list)
@dataclass
class BlueprintAnalysisExpression:
    node_id: str
    output_pin_id: str
    operation_name: str
    output_name: str
    inputs: list[tuple[str, str]] = field(default_factory=list)
    confidence: str = "structural"
    input_links: list[tuple[str, str, str]] = field(default_factory=list)
@dataclass
class BlueprintAnalysis:
    nodes: list[BlueprintAnalysisNode] = field(default_factory=list)
    links: list[BlueprintLink] = field(default_factory=list)

    # Execution Flow bağlantıları
    execution_links: list[BlueprintLink] = field(default_factory=list)

    # Node ID -> (hedef Node ID, kaynak pin adı, hedef pin adı)
    execution_graph: dict[
        str,
        list[tuple[str, str, str]]
    ] = field(default_factory=dict)

    expressions: list[tuple[str, str]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    structural_expressions: list[BlueprintAnalysisExpression] = field(
        default_factory=list
    )

    expressions_by_output: dict[
        tuple[str, str],
        BlueprintAnalysisExpression
    ] = field(default_factory=dict)
CONFIDENCE_KNOWN = "known"
CONFIDENCE_STRUCTURAL = "structural"
CONFIDENCE_AMBIGUOUS = "ambiguous"

def build_analysis_report(
    analysis: BlueprintAnalysis,
) -> dict:
    """Blueprint analizinin özet raporunu oluşturur."""

    confidence_counts = {
        CONFIDENCE_KNOWN: 0,
        CONFIDENCE_STRUCTURAL: 0,
        CONFIDENCE_AMBIGUOUS: 0,
    }

    for expression in analysis.structural_expressions:
        confidence = expression.confidence

        if confidence in confidence_counts:
            confidence_counts[confidence] += 1

    return {
        "node_count": len(analysis.nodes),
        "link_count": len(analysis.links),
        "execution_link_count": len(analysis.execution_links),
        "expression_count": len(analysis.expressions),
        "structural_expression_count": len(
            analysis.structural_expressions
        ),
        "confidence": confidence_counts,
        "issue_count": len(analysis.issues),
        "issues": list(analysis.issues),
    }

def _extract_value(text: str, key: str) -> str:
    """Bir Unreal metin alanının tırnaklı veya tırnaksız değerini alır."""
    match = re.search(
        rf'(?<![\w.]){re.escape(key)}\s*=\s*',
        text,
    )

    if not match:
        return ""

    start = match.end()

    if start < len(text) and text[start] == '"':
        end = start + 1
        escaped = False

        while end < len(text):
            char = text[end]

            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return text[start + 1:end].strip()

            end += 1

        return ""

    end = start

    while end < len(text) and text[end] not in ",)":
        end += 1

    return text[start:end].strip()

def _remove_nested_object_blocks(text: str) -> str:
    """İç içe Begin Object / End Object bloklarını metinden çıkarır."""
    result = []
    index = 0
    depth = 0
    in_quotes = False
    escaped = False

    while index < len(text):
        char = text[index]

        if in_quotes:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quotes = False

            if depth == 0:
                result.append(char)

            index += 1
            continue

        if char == '"':
            in_quotes = True
            if depth == 0:
                result.append(char)
            index += 1
            continue

        if (
            text.startswith("Begin Object", index)
            and (index == 0 or not (text[index - 1].isalnum() or text[index - 1] == "_"))
            and (
                index + len("Begin Object") == len(text)
                or not (text[index + len("Begin Object")].isalnum() or text[index + len("Begin Object")] == "_")
            )
        ):
            depth += 1
            index += len("Begin Object")
            continue

        if (
            text.startswith("End Object", index)
            and (index == 0 or not (text[index - 1].isalnum() or text[index - 1] == "_"))
            and (
                index + len("End Object") == len(text)
                or not (text[index + len("End Object")].isalnum() or text[index + len("End Object")] == "_")
            )
        ):
            if depth > 0:
                depth -= 1
            index += len("End Object")
            continue

        if depth == 0:
            result.append(char)

        index += 1

    return "".join(result)

def _remove_pin_blocks(text: str) -> str:
    """CustomProperties Pin (...) bloklarını metinden çıkarır."""
    result = []
    index = 0
    length = len(text)
    in_quotes = False
    escaped = False

    while index < length:
        char = text[index]

        if in_quotes:
            result.append(char)

            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quotes = False

            index += 1
            continue

        if char == '"':
            in_quotes = True
            result.append(char)
            index += 1
            continue

        match = re.match(
            r"(?<![\w.])CustomProperties\s+Pin\s*\(",
            text[index:],
        )

        if match:
            # Pin bloğunun açılış parantezinden sonraki konum.
            content_start = index + match.end()

            # Mevcut parantez ayrıştırıcısını kullan.
            pin_content = _parse_pin_content(text, content_start)

            # Kapanış parantezi bulunamazsa metni silmeden devam et.
            if not pin_content and (
                content_start >= length or text[content_start] != ")"
            ):
                result.append(text[index])
                index += 1
                continue

            # Pin bloğunu ve kapatma parantezini atla.
            index = content_start + len(pin_content) + 1
            continue

        result.append(char)
        index += 1

    return "".join(result)


def _extract_properties(
    text: str,
    *,
    remove_nested_objects: bool = True,
) -> dict[str, str]:
    """Metindeki üst seviye key=value alanlarını ham değerleriyle saklar."""
    properties = {}
    if remove_nested_objects:
        text = _remove_nested_object_blocks(text)
    
    length = len(text)
    index = 0
    depth = 0
    in_quotes = False
    escaped = False

    while index < length:
        char = text[index]

        # Karakterin atlanıp atlanmayacağını ve durumları güncelliyoruz
        should_ignore, in_quotes, escaped = _should_ignore_char(
            char, in_quotes, escaped
        )
        if should_ignore:
            index += 1
            continue

        if depth == 0:
            match = _PROPERTY_KEY_PATTERN.match(text, index)

            if match:
                key = match.group(1)
                value_start = match.end()

                pos, value = _parse_property_value(text, value_start, length)

                if value:
                    properties[key] = value

                index = max(pos, value_start)
                continue

        index += 1

    return properties

def _should_ignore_char(
    char: str,
    in_quotes: bool,
    escaped: bool
) -> tuple[bool, bool, bool]:
    """Karakterin atlanıp atlanmayacağını ve escaped/quotes durumunu kontrol eder."""
    
    if escaped:
        return True, in_quotes, False

    if char == "\\" and in_quotes:
        return True, in_quotes, True

    if char == '"':
        return True, not in_quotes, False

    if not in_quotes:
        if char == "(":
            # Parantez derinliği ana döngüde veya burada yönetilebilir
            return False, in_quotes, escaped
        if char == ")":
            return False, in_quotes, escaped
        if char in "\r\n":
            return True, in_quotes, False

    return False, in_quotes, escaped
def _is_key_start(
    char: str,
    index: int,
    length: int,
    text: str
) -> bool:
    """Belirli bir karakterin bir key başlangıcı olup olmadığını kontrol eder."""
    # Sadece '(' ')' ve '"' dışında diğer karakterler için
    if char not in ("(", ")", '"'):
        return _PROPERTY_KEY_PATTERN.match(text, index) is not None
    
    return False





def _extract_friendly_name(text: str) -> str:
    """PinFriendlyName değerini, iç içe parantezleri koruyarak alır."""
    match = re.search(r'(?<![\w.])PinFriendlyName\s*=\s*', text)
    if not match:
        return ""

    start = match.end()

    if text[start:start + 1] not in ('"', "'"):
        if text.startswith(("NSLOCTEXT(", "INVTEXT("), start):
            open_paren = text.find("(", start)
            depth = 0
            in_string = False
            escaped = False

            for i in range(open_paren, len(text)):
                char = text[i]

                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                    continue

                if char == '"':
                    in_string = True
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        return text[start:i + 1].strip()

        return text[start:].split(",", 1)[0].strip()

    quote = text[start]
    end = start + 1
    escaped = False

    while end < len(text):
        char = text[end]

        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == quote:
            return text[start + 1:end]

        end += 1

    return ""


    
def _extract_parenthesized_value(text: str, key: str) -> str:
    """Parantez içindeki alanın tamamını, iç içe parantezleri koruyarak alır."""
    match = re.search(
        rf'(?<![\w.]){re.escape(key)}\s*=\s*\(',
        text,
    )
    if not match:
        return ""

    start = match.end()
    depth = 1
    in_quotes = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if escaped:
            escaped = False
            continue

        if char == "\\" and in_quotes:
            escaped = True
            continue

        if char == '"':
            in_quotes = not in_quotes
            continue

        if not in_quotes:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return text[start:index]

    return ""





def _extract_pin_blocks(node_body: str) -> list[str]:
    """Yalnızca mevcut nesneye ait CustomProperties Pin bloklarını ayırır."""
    blocks = []
    index = 0
    depth_objects = 0
    in_quotes = False
    escaped = False

    while index < len(node_body):
        char = node_body[index]

        if in_quotes:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quotes = False

            index += 1
            continue

        if char == '"':
            in_quotes = True
            index += 1
            continue

        # Gerçek Begin Object ifadesini kontrol et.
        is_begin = (
            node_body.startswith("Begin Object", index)
            and (
                index == 0
                or not (
                    node_body[index - 1].isalnum()
                    or node_body[index - 1] == "_"
                )
            )
            and (
                index + len("Begin Object") == len(node_body)
                or not (
                    node_body[index + len("Begin Object")].isalnum()
                    or node_body[index + len("Begin Object")] == "_"
                )
            )
        )

        # Gerçek End Object ifadesini kontrol et.
        is_end = (
            node_body.startswith("End Object", index)
            and (
                index == 0
                or not (
                    node_body[index - 1].isalnum()
                    or node_body[index - 1] == "_"
                )
            )
            and (
                index + len("End Object") == len(node_body)
                or not (
                    node_body[index + len("End Object")].isalnum()
                    or node_body[index + len("End Object")] == "_"
                )
            )
        )

        if is_begin:
            depth_objects += 1
            index += len("Begin Object")
            continue

        if is_end:
            if depth_objects > 0:
                depth_objects -= 1

            index += len("End Object")
            continue

        if depth_objects == 0 and node_body.startswith(
            "CustomProperties", index
        ):
            match = re.match(
                r"CustomProperties\s+Pin\s*\(",
                node_body[index:],
            )

            if match:
                content_start = index + match.end()

                pin_content = _parse_pin_content(
                    node_body,
                    content_start,
                )

                if pin_content:
                    blocks.append(pin_content)

                # İçeriğin bitişindeki kapatma parantezini geç.
                index = content_start + len(pin_content) + 1
                continue

        index += 1

    return blocks

def _extract_user_defined_pin_directions(
    node_body: str,
) -> dict[str, str]:
    """UserDefinedPin kayıtlarından pin adı ve yön bilgisini çıkarır."""
    directions = {}
    ambiguous_names = set()

    index = 0
    length = len(node_body)
    in_quotes = False
    escaped = False
    depth_objects = 0

    while index < length:
        char = node_body[index]

        if in_quotes:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quotes = False
            index += 1
            continue

        if char == '"':
            in_quotes = True
            index += 1
            continue

        is_begin = (
            node_body.startswith("Begin Object", index)
            and (
                index == 0
                or not (
                    node_body[index - 1].isalnum()
                    or node_body[index - 1] == "_"
                )
            )
            and (
                index + len("Begin Object") == len(node_body)
                or not (
                    node_body[index + len("Begin Object")].isalnum()
                    or node_body[index + len("Begin Object")] == "_"
                )
            )
        )

        is_end = (
            node_body.startswith("End Object", index)
            and (
                index == 0
                or not (
                    node_body[index - 1].isalnum()
                    or node_body[index - 1] == "_"
                )
            )
            and (
                index + len("End Object") == len(node_body)
                or not (
                    node_body[index + len("End Object")].isalnum()
                    or node_body[index + len("End Object")] == "_"
                )
            )
        )

        if is_begin:
            depth_objects += 1
            index += len("Begin Object")
            continue

        if is_end:
            if depth_objects > 0:
                depth_objects -= 1

            index += len("End Object")
            continue
        if (
            depth_objects == 0
            and node_body.startswith("CustomProperties", index)
        ):
            match = re.match(
                r"CustomProperties\s+UserDefinedPin\s*\(",
                node_body[index:],
            )

            if match:
                content_start = index + match.end()
                pin_content = _parse_pin_content(
                    node_body, content_start
                )

                properties = _extract_properties(
                    pin_content,
                    remove_nested_objects=False,
                )

                pin_name = properties.get("PinName", "").strip().strip('"')
                direction = properties.get(
                    "DesiredPinDirection", ""
                ).strip().strip('"')

                if pin_name and direction in {
                    "EGPD_Input",
                    "EGPD_Output",
                }:
                    if pin_name in ambiguous_names:
                        pass
                    elif pin_name in directions and directions[pin_name] != direction:
                        directions.pop(pin_name)
                        ambiguous_names.add(pin_name)
                    else:
                        directions[pin_name] = direction

                index = content_start + len(pin_content) + 1
                continue

        index += 1

    return directions

def _parse_pin_content(node_body: str, start_index: int) -> str:
    """Belirli bir CustomProperties Pin bloğunu analiz ederek içeriği döndürür."""
    depth = 1
    pin_quotes = False
    pin_escaped = False
    end = start_index

    while end < len(node_body):
        pin_char = node_body[end]

        if pin_quotes:
            if pin_escaped:
                pin_escaped = False
            elif pin_char == "\\":
                pin_escaped = True
            elif pin_char == '"':
                pin_quotes = False
        elif pin_char == '"':
            pin_quotes = True
        elif pin_char == "(":
            depth += 1
        elif pin_char == ")":
            depth -= 1
            if depth == 0:
                return node_body[start_index:end]

        end += 1

    return ""  # Tamamlanmamış blokları atmıyoruz




def _parse_pin(pin_text: str) -> BlueprintPin:
    """Belirli bir pin metni üzerinden BlueprintPin nesesi oluşturur."""
    pin_id = _extract_pin_id(pin_text)
    pin_name = _extract_pin_name(pin_text)
    direction = _extract_direction(pin_text)
    pin_friendly_name = _extract_pin_friendly_name(pin_text)
    pin_category, pin_subcategory = _extract_pin_type(pin_text)
    default_value = _extract_default_value(pin_text)
    linked_to = _parse_linked_to(pin_text)
    
    pin_type = pin_category
    if pin_subcategory:
        pin_type = f"{pin_category}:{pin_subcategory}"
    
    properties = _extract_properties(pin_text)
    
    return BlueprintPin(
        pin_id=pin_id,
        pin_name=pin_name,
        pin_friendly_name=pin_friendly_name,
        pin_type=pin_type,
        default_value=default_value,
        linked_to=linked_to,
        properties=properties,
        direction=direction,
    )

def _extract_pin_id(pin_text: str) -> str:
    """PinId değerini metinden çıkarır."""
    return _extract_value(pin_text, "PinId")

def _extract_pin_name(pin_text: str) -> str:
    """PinName değerini metinden çıkarır."""
    return _extract_value(pin_text, "PinName")

def _extract_direction(pin_text: str) -> str:
    """Direction değerini metinden çıkarır ve boşlukları temizler."""
    return _extract_value(pin_text, "Direction").strip().strip('"').strip()





def _infer_pin_direction(
    node_class: str,
    pin_name: str,
    properties: dict[str, str] | None = None,
) -> str:
    """Yalnızca bilinen node ve fonksiyon kurallarından yön çıkarır."""

    if node_class.endswith("K2Node_PromotableOperator"):
        if pin_name in ("A", "B"):
            return "EGPD_Input"

        if pin_name == "ReturnValue":
            return "EGPD_Output"

    if node_class.endswith("K2Node_CallFunction"):
        properties = properties or {}
        function_reference = properties.get("FunctionReference", "")

        if 'MemberName="Conv_IntToDouble"' in function_reference:
            if pin_name == "InInt":
                return "EGPD_Input"

            if pin_name == "ReturnValue":
                return "EGPD_Output"

        if 'MemberName="MakeVector"' in function_reference:
            if pin_name in ("X", "Y", "Z"):
                return "EGPD_Input"

            if pin_name == "ReturnValue":
                return "EGPD_Output"
    
    # FunctionResult düğümünün exec pini giriş yönündedir.
    if node_class.endswith("K2Node_FunctionResult"):
        if pin_name == "execute":
            return "EGPD_Input"

    # BreakStruct düğümünde, yapının kendisi giriş;
    # yapıdan ayrıştırılan alanlar çıkıştır.
    if node_class.endswith("K2Node_BreakStruct"):
        if pin_name == "F_HexCoord":
            return "EGPD_Input"

    return ""

    


def _extract_pin_friendly_name(pin_text: str) -> str:
    """PinFriendlyName değerini metinden çıkarır."""
    return _extract_friendly_name(pin_text)

def _extract_pin_type(pin_text: str) -> tuple[str, str]:
    """PinType.PinCategory ve PinType.PinSubCategory değerlerini çıkarır."""
    category = _extract_value(pin_text, "PinType.PinCategory")
    subcategory = _extract_value(pin_text, "PinType.PinSubCategory") or ""
    return category, subcategory

def _extract_default_value(pin_text: str) -> str:
    """DefaultValue değerini metinden çıkarır."""
    return _extract_value(pin_text, "DefaultValue")

def _parse_linked_to(pin_text: str) -> list[str]:
    """LinkedTo değerini analiz ederek bağlantıları döndürür."""
    linked_text = _extract_parenthesized_value(pin_text, "LinkedTo")

    # Tırnak içindeki metinleri bağlantı aramasından çıkar.
    filtered_chars = []
    in_quotes = False
    escaped = False

    for char in linked_text:
        if in_quotes:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quotes = False

            filtered_chars.append(" ")

        elif char == '"':
            in_quotes = True
            filtered_chars.append(" ")

        else:
            filtered_chars.append(char)

    filtered_text = "".join(filtered_chars)

    matches = re.findall(
        r"([A-Za-z0-9_]+)\s+([A-Fa-f0-9]{32})",
        filtered_text,
    )

    return [
        f"{node_name}:{linked_pin_id}"
        for node_name, linked_pin_id in matches
    ]



def _extract_object_blocks(text: str) -> list[tuple[str, str, str]]:
    """İç içe nesneleri de ayrı ayrı çıkarır; tırnak içindeki
    Begin Object / End Object ifadelerini sınır olarak değerlendirmez.
    """
    object_pattern = re.compile(
        r'Begin Object\s+Class=([^\s]+)\s+Name="([^"]+)"'
    )

    stack = []
    objects = []
    index = 0
    in_quotes = False
    escaped = False

    while index < len(text):
        char = text[index]

        if in_quotes:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quotes = False

            index += 1
            continue

        if char == '"':
            in_quotes = True
            index += 1
            continue

        is_begin = (
            text.startswith("Begin Object", index)
            and (index == 0 or not (text[index - 1].isalnum()
                                    or text[index - 1] == "_"))
            and (
                index + len("Begin Object") == len(text)
                or not (
                    text[index + len("Begin Object")].isalnum()
                    or text[index + len("Begin Object")] == "_"
                )
            )
        )

        is_end = (
            text.startswith("End Object", index)
            and (index == 0 or not (text[index - 1].isalnum()
                                    or text[index - 1] == "_"))
            and (
                index + len("End Object") == len(text)
                or not (
                    text[index + len("End Object")].isalnum()
                    or text[index + len("End Object")] == "_"
                )
            )
        )

        if is_begin:
            header = object_pattern.match(text, index)

            # Başlık eşleşmese bile iç içe blok derinliğini takip et.
            if header:
                stack.append({
                    "header": header,
                    "start": index,
                    "body_start": header.end(),
                })
                index = header.end()
            else:
                stack.append(None)
                index += len("Begin Object")

            continue

        if is_end:
            if stack:
                item = stack.pop()

                if item is not None:
                    header = item["header"]
                    body = text[item["body_start"]:index]

                    objects.append((
                        header.group(1),
                        header.group(2),
                        body,
                        item["start"],
                    ))

            index += len("End Object")
            continue

        index += 1

    # Kapanmış nesneleri kaynak metindeki sıraya göre döndür.
    objects.sort(key=lambda item: item[3])

    return [
        (node_class, node_id, body)
        for node_class, node_id, body, _ in objects
    ]


def _get_node_operation(
    node_class: str,
    properties: dict[str, str],
) -> str:
    """Node özelliklerinden mümkünse işlem adını belirler."""

    function_reference = properties.get("FunctionReference", "")
    operation_name = properties.get("OperationName", "").strip().strip('"')

    if operation_name:
        return operation_name

    member_match = re.search(
        r'MemberName\s*=\s*"([^"]+)"',
        function_reference,
    )

    if member_match:
        return member_match.group(1)

    if node_class.endswith("K2Node_FunctionEntry"):
        return "FunctionEntry"

    if node_class.endswith("K2Node_FunctionResult"):
        return "FunctionResult"

    if node_class.endswith("K2Node_VariableGet"):
        return "VariableGet"

    if node_class.endswith("K2Node_VariableSet"):
        return "VariableSet"

    if node_class.endswith("K2Node_BreakStruct"):
        return "BreakStruct"

    if node_class.endswith("K2Node_MakeStruct"):
        return "MakeStruct"

    return ""


def parse_blueprint_text(text: str) -> dict:
    """
    Unreal Blueprint metnini node ve pin kayıtlarına ayırır.
    Ham metin ayrıca değiştirilmeden korunur.
    """
    if not isinstance(text, str):
        raise TypeError("Blueprint girdisi metin (str) olmalıdır.")

    nodes = []

    for node_class, node_id, node_body in _extract_object_blocks(text):
      

       
        
        pins = [
            _parse_pin(pin_block)
            for pin_block in _extract_pin_blocks(node_body)
        ]

        # Node özelliklerini yön çıkarma işleminden önce al.
        node_properties = _extract_properties(
            _remove_pin_blocks(node_body)
        )

        user_pin_directions = _extract_user_defined_pin_directions(
            node_body
        )


        
        for pin in pins:
            # Öncelik: Kaynak metinde açıkça yazılmış yön.
            if pin.direction:
                continue

            # İkinci öncelik: UserDefinedPin metadata bilgisi.
            if pin.pin_name in user_pin_directions:
                pin.direction = user_pin_directions[pin.pin_name]
                continue

            # Son çare: Bilinen node/pin kurallarından yön çıkar.
            pin.direction = _infer_pin_direction(
                node_class,
                pin.pin_name,
                node_properties,
            )
            
       
       

        
        nodes.append(
            BlueprintNode(
                node_id=node_id,
                node_class=node_class,
                pins=pins,
                operation_name=_get_node_operation(
                    node_class,
                    node_properties,
                ),
                properties=node_properties,
            )
        )


    return {
        "raw_text": text,
        "character_count": len(text),
        "lines": text.splitlines(),
        "nodes": nodes,
        "node_count": len(nodes),
        "pin_count": sum(len(node.pins) for node in nodes),
    }







def extract_unique_links(
    nodes: list[BlueprintNode],
) -> list[tuple[str, str, str, str]]:
    """Bağlantıları tekilleştirir; bilinen yönleri korur."""

    pins_by_node = {
        node.node_id: {pin.pin_id: pin for pin in node.pins}
        for node in nodes
    }

    unique_links = {}

    
   
    def get_direction(pin: BlueprintPin) -> str:
        """UE metninde yalnızca çıkış pinleri Direction taşır; boş yön giriştir."""
        direction = pin.direction.strip().strip('"')

        if direction == "EGPD_Output":
            return "EGPD_Output"

        return "EGPD_Input"

    

    for node in nodes:
        for pin in node.pins:
            for linked in pin.linked_to:
                if ":" not in linked:
                    continue

                target_node_id, target_pin_id = linked.rsplit(":", 1)
                target_pins = pins_by_node.get(target_node_id)

                if target_pins is None:
                    continue

                target_pin = target_pins.get(target_pin_id)
                if target_pin is None:
                    continue

             

                pin_direction = get_direction(pin)
                target_direction = get_direction(target_pin)

                if (
                    pin_direction == "EGPD_Output"
                    and target_direction == "EGPD_Input"
                ):
                    link = (
                        node.node_id,
                        pin.pin_id,
                        target_node_id,
                        target_pin_id,
                    )
                elif (
                    pin_direction == "EGPD_Input"
                    and target_direction == "EGPD_Output"
                ):
                    link = (
                        target_node_id,
                        target_pin_id,
                        node.node_id,
                        pin.pin_id,
                    )
                else:
                   link = (
                        node.node_id,
                        pin.pin_id,
                        target_node_id,
                        target_pin_id,
                    )

                key = frozenset(
                    (
                        (link[0], link[1]),
                        (link[2], link[3]),
                    )
                )

                if key not in unique_links:
                    unique_links[key] = link

    return list(unique_links.values())



def extract_blueprint_links(
    nodes: list[BlueprintNode],
) -> list[BlueprintLink]:
    """Geçerli bağlantıları yön bilgisiyle BlueprintLink nesneleri olarak döndürür."""
    unique_links = extract_unique_links(nodes)

    pins_by_node = {
        node.node_id: {
            pin.pin_id: pin
            for pin in node.pins
        }
        for node in nodes
    }

    def has_known_direction(
        source_pin: BlueprintPin,
        target_pin: BlueprintPin,
    ) -> bool:
        # Boş yön giriş sayılır; bağlantı, tam olarak bir ucu çıkışsa geçerlidir.
        source_is_output = source_pin.direction.strip().strip('"') == "EGPD_Output"
        target_is_output = target_pin.direction.strip().strip('"') == "EGPD_Output"

        return source_is_output != target_is_output

    links = []

    for (
        source_node_id,
        source_pin_id,
        target_node_id,
        target_pin_id,
    ) in unique_links:

        source_pin = pins_by_node[source_node_id][source_pin_id]
        target_pin = pins_by_node[target_node_id][target_pin_id]

        links.append(
            BlueprintLink(
                source_node_id=source_node_id,
                source_pin_id=source_pin_id,
                target_node_id=target_node_id,
                target_pin_id=target_pin_id,
                direction_known=has_known_direction(
                    source_pin,
                    target_pin,
                ),
            )
        )

    return links

def build_node_pin_index(
    nodes: list[BlueprintNode],
) -> dict[tuple[str, str], BlueprintPin]:
    """Node kimliği ve pin kimliği üzerinden pinlere hızlı erişim sağlar."""
    return {
        (node.node_id, pin.pin_id): pin
        for node in nodes
        for pin in node.pins
    }


def get_connected_source_pin(
    node_id: str,
    pin_id: str,
    links: list[BlueprintLink],
    pin_index: dict[tuple[str, str], BlueprintPin],
) -> tuple[BlueprintLink, BlueprintPin] | None:
    """Bir giriş pinine bağlı kaynak bağlantıyı ve kaynak pini bulur."""
    for link in links:
        if not link.direction_known:
            continue

        if (
            link.target_node_id == node_id
            and link.target_pin_id == pin_id
        ):
            source_key = (
                link.source_node_id,
                link.source_pin_id,
            )
            source_pin = pin_index.get(source_key)

            if source_pin is not None:
                return link, source_pin

    return None
def describe_node_inputs(
    node: BlueprintNode,
    links: list[BlueprintLink],
    pin_index: dict[tuple[str, str], BlueprintPin],
) -> list[str]:
    """Yalnızca giriş pinlerini ve kaynaklarını açıklar."""

    descriptions = []

    is_function_entry = node.node_class.endswith(
        "K2Node_FunctionEntry"
    )

    for pin in node.pins:
        # Açıkça çıkış olduğu bilinen pinleri atla.
        if pin.direction == "EGPD_Output":
            continue
        
        connection = get_connected_source_pin(
            node.node_id,
            pin.pin_id,
            links,
            pin_index,
        )

        if connection is None:
            # Fonksiyon girişleri ve açıkça giriş olduğu bilinen
            # diğer pinler varsayılan değerleriyle gösterilebilir.
            if (
                is_function_entry
                or pin.direction == "EGPD_Input"
            ):
                value = pin.default_value or "(varsayılan değer yok)"
                descriptions.append(
                    f"{pin.pin_name} = {value} [fonksiyon girdisi]"
                    if is_function_entry
                    else f"{pin.pin_name} = {value} [giriş]"
                )

            continue

        link, source_pin = connection

        descriptions.append(
            f"{pin.pin_name} <- "
            f"{link.source_node_id}.{source_pin.pin_name}"
        )

    return descriptions 


def create_pin_short_ids(
    nodes: list[BlueprintNode],
) -> dict[tuple[str, str], str]:
    """Her node ve pin çiftine sabit bir kısa ID verir.

    Anahtar: (node_id, pin_id)
    Değer: P0001, P0002 gibi görüntüleme etiketi.
    """
    pin_short_ids = {}
    next_pin_number = 1

    for node in nodes:
        for pin in node.pins:
            if not pin.pin_id:
                continue

            pin_key = (node.node_id, pin.pin_id)

            if pin_key not in pin_short_ids:
                pin_short_ids[pin_key] = f"P{next_pin_number:04d}"
                next_pin_number += 1

    return pin_short_ids
def validate_blueprint_graph(
    nodes: list[BlueprintNode],
) -> list[str]:
    """Node, pin ve bağlantı kimliklerindeki tutarsızlıkları raporlar."""

    issues = []
    seen_node_ids = set()
    nodes_by_id = {}

    for node in nodes:
        if node.node_id in seen_node_ids:
            issues.append(
                f"Tekrarlanan Node ID: {node.node_id}"
            )
        else:
            seen_node_ids.add(node.node_id)
            nodes_by_id[node.node_id] = node

    seen_pin_ids = {}

    for node in nodes:
        node_seen_pins = set()

        for pin in node.pins:
            if pin.pin_id in node_seen_pins:
                issues.append(
                    f"Tekrarlanan Pin ID: "
                    f"{node.node_id}.{pin.pin_id}"
                )

            node_seen_pins.add(pin.pin_id)

            for linked in pin.linked_to:
                if ":" not in linked:
                    issues.append(
                        f"Geçersiz bağlantı biçimi: "
                        f"{node.node_id}.{pin.pin_id} -> {linked}"
                    )
                    continue

                target_node_id, target_pin_id = linked.rsplit(":", 1)
                target_node = nodes_by_id.get(target_node_id)

                if target_node is None:
                    issues.append(
                        f"Bulunamayan hedef Node: {linked}"
                    )
                    continue

                if not any(
                    target_pin.pin_id == target_pin_id
                    for target_pin in target_node.pins
                ):
                    issues.append(
                        f"Bulunamayan hedef Pin: {linked}"
                    )

    return list(dict.fromkeys(issues))

def build_blueprint_analysis(
    nodes: list[BlueprintNode],
    links: list[BlueprintLink],
    return_model: bool = False,
) -> list[str] | tuple[list[str], BlueprintAnalysis]:
    """Blueprint bağlantılarından okunabilir matematik ifadeleri üretir."""
        # Tekrarlanan kimlikler analiz sonuçlarını bozabilir.
    seen_node_ids = set()
    duplicate_node_ids = set()

    for node in nodes:
        if node.node_id in seen_node_ids:
            duplicate_node_ids.add(node.node_id)
        seen_node_ids.add(node.node_id)

    duplicate_pin_ids = []

    for node in nodes:
        seen_pin_ids = set()

        for pin in node.pins:
            if pin.pin_id in seen_pin_ids:
                duplicate_pin_ids.append(
                    f"{node.node_id}.{pin.pin_id}"
                )

            seen_pin_ids.add(pin.pin_id)

    if duplicate_node_ids or duplicate_pin_ids:
        issues = ["İŞLEM ANALİZİ", "- Analiz durduruldu: Kimlik çakışması tespit edildi."]

        for node_id in sorted(duplicate_node_ids):
            issues.append(f"- Tekrarlanan Node ID: {node_id}")

        for pin_id in duplicate_pin_ids:
            issues.append(f"- Tekrarlanan Pin ID: {pin_id}")

        return issues

    # Yapısal analiz modelini oluştur.
    analysis = BlueprintAnalysis(
        links=list(links),
    )

    nodes_by_id = {node.node_id: node for node in nodes}
    pins_by_node = {
        node.node_id: {pin.pin_id: pin for pin in node.pins}
        for node in nodes
    }

    # Her hedef giriş pininin kaynak çıkışını kaydet.
    incoming: dict[
        tuple[str, str],
        list[tuple[str, str]],
    ] = {}

    for link in links:
        if not link.direction_known:
            continue

        target_key = (
            link.target_node_id,
            link.target_pin_id,
        )

        source_key = (
            link.source_node_id,
            link.source_pin_id,
        )

        sources = incoming.setdefault(target_key, [])

        if source_key not in sources:
            sources.append(source_key)

        # Bağlantının kaynak ve hedef pinlerini bul.
        source_pin = pins_by_node.get(
            link.source_node_id, {}
        ).get(link.source_pin_id)

        target_pin = pins_by_node.get(
            link.target_node_id, {}
        ).get(link.target_pin_id)

        # Pin türlerinden biri Exec ise akış bağlantısıdır.
        is_execution_link = any(
            pin is not None
            and "exec" in pin.pin_type.lower()
            for pin in (source_pin, target_pin)
        )

        if is_execution_link:
            if link not in analysis.execution_links:
                analysis.execution_links.append(link)

            source_node_id = link.source_node_id

            source_pin_name = (
                source_pin.pin_friendly_name
                or source_pin.pin_name
                if source_pin is not None
                else "(bilinmeyen çıkış)"
            )

            target_pin_name = (
                target_pin.pin_friendly_name
                or target_pin.pin_name
                if target_pin is not None
                else "(bilinmeyen giriş)"
            )

            connection = (
                link.target_node_id,
                source_pin_name,
                target_pin_name,
            )

            graph_connections = analysis.execution_graph.setdefault(
                source_node_id,
                [],
            )

            if connection not in graph_connections:
                graph_connections.append(connection)

    def display_name(pin: BlueprintPin) -> str:
        friendly = (pin.pin_friendly_name or "").strip()

        if friendly.startswith('INVTEXT("') and friendly.endswith('")'):
            friendly = friendly[9:-2]

        return friendly or pin.pin_name or "(isimsiz)"

    def get_input(node: BlueprintNode, names: set[str]):
        """Belirtilen isimlerden birine sahip pini bul."""
        for pin in node.pins:
            if pin.pin_name.strip().lower() in names:
                return pin
        return None
        # Aynı analiz sırasında Node davranışlarını tekrar sorgulama.
    node_behavior_cache = {}

    def get_cached_node_behavior(node):
        if node.node_id not in node_behavior_cache:
            node_behavior_cache[node.node_id] = get_node_behavior(node)

        return node_behavior_cache[node.node_id]
    def resolve_input(
        node: BlueprintNode,
        pin: BlueprintPin,
        visited: set[tuple[str, str]],
    ) -> str:
        """Bir girişin bağlı olduğu ifadeyi veya varsayılan değerini çöz."""

        sources = incoming.get((node.node_id, pin.pin_id), [])

        if len(sources) > 1:
            issue = (
                f"Ambiguous input: Node {node.node_id}, "
                f"Pin {display_name(pin)} has multiple connections."
            )
            if issue not in analysis.issues:
                analysis.issues.append(issue)

        if sources:
            resolved_sources = [
                resolve_output(source_node_id, source_pin_id, visited)
                for source_node_id, source_pin_id in sources
            ]

            if any(value == "?" for value in resolved_sources):
                issue = (
                    f"Unresolved input: Node {node.node_id}, "
                    f"Pin {display_name(pin)}."
                )
                if issue not in analysis.issues:
                    analysis.issues.append(issue)

            return " | ".join(resolved_sources)

        if pin.default_value != "":
            return pin.default_value

        issue = (
            f"Missing input: Node {node.node_id}, "
            f"Pin {display_name(pin)} has no connection or default value."
        )
        if issue not in analysis.issues:
            analysis.issues.append(issue)

        return "?"

    def get_input_links(node: BlueprintNode) -> list[tuple[str, str, str]]:
        """Node girişlerinin kaynak Node ve Pin bağlantılarını döndür."""

        input_links = []

        for pin in node.pins:
            if pin.direction != "EGPD_Input":
                continue

            sources = incoming.get((node.node_id, pin.pin_id), [])

            for source_node_id, source_pin_id in sources:
                input_links.append(
                    (
                        display_name(pin),
                        source_node_id,
                        source_pin_id,
                    )
                )

        return input_links
    def resolve_output(
        node_id: str,
        pin_id: str,
        visited: set[tuple[str, str]],
    ) -> str:
        key = (node_id, pin_id)

        if key in visited:
            return "[Döngü]"

        node = nodes_by_id.get(node_id)
        pin = pins_by_node.get(node_id, {}).get(pin_id)

        if node is None or pin is None:
            return "[Pin bulunamadı]"

        visited = visited | {key}
        class_name = node.node_class.rsplit(".", 1)[-1]
                # Registry bilgisi yalnızca bir kez alınır.
        behavior = get_cached_node_behavior(node)

        operation_name = (
            node.operation_name
            or node.properties.get("MemberName", "")
            or ""
        ).strip().strip('"')
               # Önce öğrenilmiş BreakStruct davranışını kullan.
        

        

        if (
            behavior
            and behavior.get("kind") == "break_struct"
            and behavior.get("resolution") == "extract_fields"
        ):
            input_name = behavior["input_pin"]
            output_names = behavior["output_pins"]

            if pin.pin_name not in output_names:
                return display_name(pin)

            struct_pin = next(
                (
                    p for p in node.pins
                    if p.pin_name == input_name
                    and (node.node_id, p.pin_id) in incoming
                ),
                None,
            )

        else:
            # Öğrenilmemiş düğümler için eski davranışı koru.
            struct_pin = next(
                (
                    p for p in node.pins
                    if p.pin_type.split(":", 1)[0] == "struct"
                    and (node.node_id, p.pin_id) in incoming
                ),
                None,
            )

        if (
            behavior
            and behavior.get("kind") == "break_struct"
            and behavior.get("resolution") == "extract_fields"
        ) or "BreakStruct" in class_name:

            if struct_pin:
                sources = incoming[(node.node_id, struct_pin.pin_id)]
                resolved_sources = []

                for source_node_id, source_pin_id in sources:
                    source_node = nodes_by_id.get(source_node_id)
                    source_output = pins_by_node.get(source_node_id, {}).get(
                        source_pin_id
                    )

                    if source_node is None or source_output is None:
                        base = "[Pin bulunamadı]"
                    else:
                        source_class = source_node.node_class.rsplit(".", 1)[-1]

                        if "FunctionEntry" in source_class:
                            base = display_name(source_output)
                        else:
                            base = resolve_output(
                                source_node_id,
                                source_pin_id,
                                visited,
                            )

                    resolved_sources.append(
                        f"{base}.{display_name(pin)}"
                    )

                return " | ".join(resolved_sources)

            return display_name(pin)

        # Dönüşüm düğümleri: çıkış, giriş değerini temsil eder.
        
        
        # Önce öğrenilmiş Node davranışını kullan.
        


        if (
            behavior
            and behavior.get("kind") == "conversion"
            and behavior.get("resolution") == "passthrough"
        ):
            input_name = behavior.get("input_pin", "")

            input_pin = next(
                (
                    pin for pin in node.pins
                    if pin.pin_name == input_name
                ),
                None,
            )

            if input_pin:
                return resolve_input(node, input_pin, visited)

        # Öğrenilmemiş dönüşüm düğümleri için mevcut davranışı koru.
        if "Conv_" in operation_name:
            input_pin = get_input(
                node,
                {"input", "inint", "infloat", "indouble", "inbyte"},
            )

            if input_pin:
                return resolve_input(node, input_pin, visited)


        # Matematiksel işlemler.
        if "PromotableOperator" in class_name:
            a_pin = get_input(node, {"a"})
            b_pin = get_input(node, {"b"})

            a = resolve_input(node, a_pin, visited) if a_pin else "?"
            b = resolve_input(node, b_pin, visited) if b_pin else "?"

            raw_operation = (
                node.operation_name
                or node.properties.get("OperationName", "")
            ).strip().strip('"')

            operation = raw_operation.lower()

            symbols = {
                "add": "+",
                "addition": "+",
                "+": "+",
                "subtract": "-",
                "subtraction": "-",
                "-": "-",
                "multiply": "*",
                "multiplication": "*",
                "*": "*",
                "divide": "/",
                "division": "/",
                "/": "/",
            }

            symbol = symbols.get(operation)

            if symbol:
                return f"({a} {symbol} {b})"

            # Tanınmayan işlem adının orijinal yazımını koru.
            return f"{raw_operation or 'İşlem'}({a}, {b})"

                # Önce öğrenilmiş MakeVector davranışını kullan.
        


        if (
            behavior
            and behavior.get("kind") == "make_vector"
            and behavior.get("resolution") == "combine_components"
        ):
            input_pins = behavior["input_pins"]
            output_pin_name = behavior["output_pin"]
        elif node.operation_name == "MakeVector":
            # Öğrenilmemiş düğümler için eski davranışı koru.
            input_pins = ["X", "Y", "Z"]
            output_pin_name = "ReturnValue"
        else:
            input_pins = None

        if input_pins:
            components = []

            for component in input_pins:
                component_pin = get_input(node, {component.lower()})

                value = (
                    resolve_input(node, component_pin, visited)
                    if component_pin else "?"
                )

                components.append(f"{component}={value}")

            return "Vector(" + ", ".join(components) + ")"

        if "FunctionEntry" in class_name:
            return display_name(pin)

        if pin.default_value != "":
            return pin.default_value
        # Daha önce analiz edilmiş çıkışı doğrudan kullan.
        cached_expression = analysis.expressions_by_output.get(
            (node.node_id, pin.pin_id)
        )

        if cached_expression is not None:
            cached_inputs = [
                f"{name}={value}"
                for name, value in cached_expression.inputs
            ]

            return (
                f"{cached_expression.operation_name}."
                f"{cached_expression.output_name}"
                f"({', '.join(cached_inputs)})"
            )
        # Bilinmeyen Node: girişlerini yapısal olarak koru.
        input_pins = [
            input_pin
            for input_pin in node.pins
            if input_pin.direction == "EGPD_Input"
        ]

        if not input_pins:
            return f"{operation_name or class_name}.{display_name(pin)}"

        input_values = []
        structured_inputs = []

        for input_pin in input_pins:
            value = resolve_input(
                node,
                input_pin,
                visited,
            )

            pin_name = display_name(input_pin)

            input_values.append(
                f"{pin_name}={value}"
            )

            structured_inputs.append(
                (pin_name, value)
            )

        # Aynı çıkış için yinelenen kayıt oluşturma.
        already_recorded = (
            node.node_id,
            pin.pin_id,
        ) in analysis.expressions_by_output

        if not already_recorded:
            analysis.structural_expressions.append(
                BlueprintAnalysisExpression(
                    node_id=node.node_id,
                    output_pin_id=pin.pin_id,
                    operation_name=operation_name or class_name,
                    output_name=display_name(pin),
                    inputs=structured_inputs,
                    input_links=get_input_links(node),
                    confidence=(
                        CONFIDENCE_AMBIGUOUS
                        if any(
                            issue.startswith((
                                f"Ambiguous input: Node {node.node_id},",
                                f"Unresolved input: Node {node.node_id},",
                                f"Missing input: Node {node.node_id},",
                            ))
                            for issue in analysis.issues
                        )
                        else CONFIDENCE_STRUCTURAL
                    ),
                )
            )
            record = analysis.structural_expressions[-1]

            analysis.expressions_by_output[
                (record.node_id, record.output_pin_id)
            ] = record
        return (
            f"{operation_name or class_name}."
            f"{display_name(pin)}"
            f"({', '.join(input_values)})"
        )

    
    lines = ["BLUEPRINT GENEL ANALİZİ"]

    # Bağlantıları iki yönde de indeksle.
    outgoing: dict[
        tuple[str, str],
        list[tuple[str, str]],
    ] = {}

    for link in links:
        if not link.direction_known:
            continue

        source_key = (link.source_node_id, link.source_pin_id)
        target_key = (link.target_node_id, link.target_pin_id)

        targets = outgoing.setdefault(source_key, [])

        if target_key not in targets:
            targets.append(target_key)

    # Her Node'u yapısal olarak raporla.
    for node in nodes:
        class_name = node.node_class.rsplit(".", 1)[-1]
        operation_name = (
            node.operation_name
            or node.properties.get("OperationName", "")
        ).strip().strip('"')

        lines.append("")
        lines.append(f"NODE: {node.node_id}")
        lines.append(f"  Sınıf: {class_name}")

        if operation_name:
            lines.append(f"  İşlem: {operation_name}")

        lines.append("  Pinler:")

        for pin in node.pins:
            pin_description = (
                f"    - {display_name(pin)}"
                f" | ID: {pin.pin_id}"
                f" | Yön: {pin.direction or 'Bilinmiyor'}"
                f" | Tür: {pin.pin_type or 'Bilinmiyor'}"
            )

            if pin.default_value != "":
                pin_description += f" | Varsayılan: {pin.default_value}"

            lines.append(pin_description)

            # Bu pinin bağlı olduğu kaynaklar.
            source_keys = incoming.get(
                (node.node_id, pin.pin_id),
                [],
            )

            for source_node_id, source_pin_id in source_keys:
                source_pin = pins_by_node.get(
                    source_node_id, {}
                ).get(source_pin_id)

                source_name = (
                    display_name(source_pin)
                    if source_pin else source_pin_id
                )

                lines.append(
                    f"        Girdi bağlantısı: "
                    f"{source_node_id}.{source_name}"
                )

            # Bu pinden çıkan bağlantılar.
            target_keys = outgoing.get(
                (node.node_id, pin.pin_id),
                [],
            )

            for target_node_id, target_pin_id in target_keys:
                target_pin = pins_by_node.get(
                    target_node_id, {}
                ).get(target_pin_id)

                target_name = (
                    display_name(target_pin)
                    if target_pin else target_pin_id
                )

                lines.append(
                    f"        Çıktı bağlantısı: "
                    f"{target_node_id}.{target_name}"
                )
    analysis_nodes_by_id: dict[str, BlueprintAnalysisNode] = {}

    for node in nodes:
        analysis_node = BlueprintAnalysisNode(
            node_id=node.node_id,
            node_class=node.node_class,
            operation_name=node.operation_name,
        )

        for pin in node.pins:
            analysis_pin = BlueprintAnalysisPin(
                pin_id=pin.pin_id,
                name=display_name(pin),
                direction=pin.direction,
                pin_type=pin.pin_type,
                default_value=pin.default_value,
            )

            analysis_node.pins.append(analysis_pin)

        analysis.nodes.append(analysis_node)
        analysis_nodes_by_id[node.node_id] = analysis_node


    # Her pin için gelen ve giden bağlantıları kaydet.
    for link in links:
        if not link.direction_known:
            continue

        source_node = analysis_nodes_by_id.get(link.source_node_id)
        target_node = analysis_nodes_by_id.get(link.target_node_id)

        if source_node is None or target_node is None:
            continue

        source_pin = next(
            (
                p for p in source_node.pins
                if p.pin_id == link.source_pin_id
            ),
            None,
        )

        target_pin = next(
            (
                p for p in target_node.pins
                if p.pin_id == link.target_pin_id
            ),
            None,
        )

        if source_pin is not None:
            connection = (
                link.target_node_id,
                link.target_pin_id,
            )

            if connection not in source_pin.outgoing:
                source_pin.outgoing.append(connection)

        if target_pin is not None:
            connection = (
                link.source_node_id,
                link.source_pin_id,
            )

            if connection not in target_pin.incoming:
                target_pin.incoming.append(connection)
    lines.append("")
    lines.append("ÇÖZÜMLENEN İFADELER")

    found = False

    for node in nodes:
        class_name = node.node_class.rsplit(".", 1)[-1]

        if "PromotableOperator" not in class_name:
            continue

        output_pin = get_input(node, {"returnvalue", "output"})

        if output_pin is None:
            continue

        expression = resolve_output(
            node.node_id,
            output_pin.pin_id,
            set(),
        )

        raw_operation = (
            node.operation_name
            or node.properties.get("OperationName", "")
        ).strip().strip('"')

        a_pin = get_input(node, {"a"})
        b_pin = get_input(node, {"b"})

        structured_inputs = []

        for input_pin in (a_pin, b_pin):
            if input_pin is None:
                continue

            structured_inputs.append(
                (
                    display_name(input_pin),
                    resolve_input(node, input_pin, set()),
                )
            )

        known_operations = {
            "add", "addition", "+",
            "subtract", "subtraction", "-",
            "multiply", "multiplication", "*",
            "divide", "division", "/",
        }

        analysis.structural_expressions.append(
            BlueprintAnalysisExpression(
                node_id=node.node_id,
                output_pin_id=output_pin.pin_id,
                operation_name=raw_operation or class_name,
                output_name=display_name(output_pin),
                inputs=structured_inputs,
                input_links=get_input_links(node),
                confidence=(
                    CONFIDENCE_AMBIGUOUS
                    if any(
                        issue.startswith((
                            f"Ambiguous input: Node {node.node_id},",
                            f"Unresolved input: Node {node.node_id},",
                            f"Missing input: Node {node.node_id},",
                        ))
                        for issue in analysis.issues
                    )
                    else CONFIDENCE_KNOWN
                ),
            )
        )
        record = analysis.structural_expressions[-1]

        analysis.expressions_by_output[
            (record.node_id, record.output_pin_id)
        ] = record
        analysis.expressions.append((node.node_id, expression))
        lines.append(f"- {node.node_id}: {expression}")
        found = True
    for node in nodes:
        if node.operation_name != "MakeVector":
            continue

        output_pin = get_input(node, {"returnvalue"})

        if output_pin is None:
            continue

        expression = resolve_output(
            node.node_id,
            output_pin.pin_id,
            set(),
        )

        structured_inputs = []

        for component in ("X", "Y", "Z"):
            component_pin = get_input(node, {component.lower()})

            if component_pin is None:
                continue

            structured_inputs.append(
                (
                    display_name(component_pin),
                    resolve_input(node, component_pin, set()),
                )
            )

        analysis.structural_expressions.append(
            BlueprintAnalysisExpression(
                node_id=node.node_id,
                output_pin_id=output_pin.pin_id,
                operation_name="MakeVector",
                output_name=display_name(output_pin),
                inputs=structured_inputs,
                input_links=get_input_links(node),
                confidence=(
                    CONFIDENCE_AMBIGUOUS
                    if any(
                        issue.startswith((
                            f"Ambiguous input: Node {node.node_id},",
                            f"Unresolved input: Node {node.node_id},",
                            f"Missing input: Node {node.node_id},",
                        ))
                        for issue in analysis.issues
                    )
                    else CONFIDENCE_KNOWN
                ),
            )
        )
        record = analysis.structural_expressions[-1]

        analysis.expressions_by_output[
            (record.node_id, record.output_pin_id)
        ] = record
        analysis.expressions.append((node.node_id, expression))
        lines.append(f"- {node.node_id}: {expression}")
        found = True
    if not found:
        lines.append("- Bu grafikte çözümlenmiş matematiksel ifade yok.")

    if return_model:
        return lines, analysis

    return lines

def _parse_property_value(text: str, start_pos: int, length: int) -> tuple[int, str]:
    """Key'den sonraki değeri parantez ve tırnak kurallarına göre güvenle ayrıştırır."""
    pos = start_pos
    value_depth = 0
    value_in_quotes = False
    value_escaped = False

    while pos < length:
        value_char = text[pos]

        if value_escaped:
            value_escaped = False
        elif value_char == "\\" and value_in_quotes:
            value_escaped = True
        elif value_char == '"':
            value_in_quotes = not value_in_quotes
        elif not value_in_quotes:
            if value_char == "(":
                value_depth += 1
            elif value_char == ")":
                if value_depth == 0:
                    break
                value_depth -= 1
            elif value_depth == 0 and value_char in ",\r\n":
                break

        pos += 1

    value = text[start_pos:pos].strip()
    return pos, value