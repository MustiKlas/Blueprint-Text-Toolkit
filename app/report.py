"""Blueprint metninden, ekrandan bağımsız bir 'rapor' modeli üretir.

Parser'ın (parser.py) çıkardığı node/pin/bağlantı verisini; okunabilir adlar,
C++ tür ipuçları, kaynak çözümleme ve ifade üretimi ile zenginleştirir.
Tablolar ve üç çıktı (kısa / orta / uzun) bu modelden beslenir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.parser import (
    build_blueprint_analysis,
    extract_blueprint_links,
    parse_blueprint_text,
    validate_blueprint_graph,
)

# --------------------------------------------------------------------------
# Küçük yardımcılar
# --------------------------------------------------------------------------

_LOC_RE = re.compile(
    r'NSLOCTEXT\(\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"(.*)"\s*\)'
)
_GUID_SUFFIX_RE = re.compile(r"^(?P<name>.+?)_\d+_[0-9A-Fa-f]{32}$")

OPERATOR_SYMBOLS = {
    "Add": "+",
    "Subtract": "-",
    "Multiply": "*",
    "Divide": "/",
    "EqualEqual": "==",
    "NotEqual": "!=",
    "Greater": ">",
    "GreaterEqual": ">=",
    "Less": "<",
    "LessEqual": "<=",
    "BooleanAND": "&&",
    "BooleanOR": "||",
}

# (anahtar kelime, kategori kimliği, çeviri anahtarı)
NODE_KINDS = (
    ("functionentry", "entry", "function_entry"),
    ("functionresult", "result", "function_result"),
    ("callarrayfunction", "call", "function_call_array"),
    ("callfunction", "call", "function_call"),
    ("customevent", "event", "event"),
    ("event", "event", "event"),
    ("ifthenelse", "branch", "conditional_branch"),
    ("branch", "branch", "conditional_branch"),
    ("executionsequence", "sequence", "execution_sequence"),
    ("sequence", "sequence", "execution_sequence"),
    ("macroinstance", "macro", "macro_call"),
    ("breakstruct", "break", "break_struct"),
    ("makestruct", "make", "make_struct"),
    ("promotableoperator", "operator", "math_logic_operation"),
    ("commutativeassociativebinaryoperator", "operator", "math_logic_operation"),
    ("variableget", "var_get", "get_variable"),
    ("variableset", "var_set", "set_variable"),
    ("select", "select", "select_value"),
    ("convert", "convert", "type_conversion"),
    ("dynamiccast", "cast", "type_cast"),
    ("cast", "cast", "type_cast"),
    ("knot", "reroute", "reroute"),
    ("reroute", "reroute", "reroute"),
    ("comment", "comment", "comment_node"),
)

def clean_text(value: str) -> str:
    """NSLOCTEXT / INVTEXT / tırnak sarmalarını temizler."""
    value = (value or "").strip()

    if value.startswith('INVTEXT("') and value.endswith('")'):
        value = value[9:-2]

    match = _LOC_RE.fullmatch(value)
    if match:
        value = match.group(1)

    return value.strip().strip('"').strip()


def clean_member_name(name: str) -> str:
    """'Q_4_F5E0...' gibi UserDefinedStruct üye adlarını 'Q' yapar."""
    match = _GUID_SUFFIX_RE.match(name)
    return match.group("name") if match else name


def _member(text: str, key: str) -> str:
    match = re.search(rf'{key}="([^"]*)"', text or "")
    return match.group(1) if match else ""


def _object_name(path: str) -> str:
    """\"/Script/X.Class'/Script/Engine.Foo'\" -> 'Foo'."""
    match = re.search(r"'([^']+)'", path or "")
    target = match.group(1) if match else (path or "").strip('"')
    return target.rsplit(".", 1)[-1].strip('"')


_CPP_SIMPLE = {
    "int": "int32",
    "int64": "int64",
    "bool": "bool",
    "byte": "uint8",
    "string": "FString",
    "name": "FName",
    "text": "FText",
    "real:double": "double",
    "real:float": "float",
    "real": "double",
}

_CPP_STRUCTS = {
    "Vector": "FVector",
    "Vector2D": "FVector2D",
    "Vector4": "FVector4",
    "Rotator": "FRotator",
    "Transform": "FTransform",
    "LinearColor": "FLinearColor",
    "Color": "FColor",
    "Quat": "FQuat",
}


# --------------------------------------------------------------------------
# Veri sınıfları
# --------------------------------------------------------------------------

@dataclass
class PinInfo:
    node_id: str
    pin_id: str
    name: str
    direction: str  # "in" | "out"
    is_exec: bool
    pin_type: str
    type_label: str
    cpp_hint: str
    default: str
    hidden: bool
    friendly: str = ""
    sources: list[tuple[str, str]] = field(default_factory=list)
    targets: list[tuple[str, str]] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        """'then (true)' gibi, varsa kullanıcıya görünen adı da içeren ad."""
        return f"{self.name} ({self.friendly})" if self.friendly else self.name

    @property
    def is_implicit_self(self) -> bool:
        return (self.pin_type or "").endswith(":self")


@dataclass
class NodeInfo:
    node_id: str
    short_id: str
    label: str
    category: str
    kind_text: str
    node_class: str
    function_ref: str
    variable: str
    properties: dict[str, str]
    pins: list[PinInfo] = field(default_factory=list)

    @property
    def has_exec(self) -> bool:
        return any(pin.is_exec for pin in self.pins)

    @property
    def data_outputs(self) -> list[PinInfo]:
        return [
            pin for pin in self.pins
            if pin.direction == "out" and not pin.is_exec
        ]

    @property
    def data_inputs(self) -> list[PinInfo]:
        return [
            pin for pin in self.pins
            if pin.direction == "in" and not pin.is_exec
        ]


@dataclass
class LinkInfo:
    source_node: str
    source_pin: str
    target_node: str
    target_pin: str
    is_exec: bool
    direction_known: bool


@dataclass
class BlueprintReport:
    nodes: list[NodeInfo] = field(default_factory=list)
    links: list[LinkInfo] = field(default_factory=list)
    function_name: str = ""
    asset_name: str = ""
    entry: NodeInfo | None = None
    results: list[NodeInfo] = field(default_factory=list)
    execution: dict[str, list[tuple[str, str, str]]] = field(
        default_factory=dict
    )
    issues: list[str] = field(default_factory=list)
    pin_count: int = 0

    def __post_init__(self):
        self._nodes_by_id: dict[str, NodeInfo] = {}
        self._pins_by_key: dict[tuple[str, str], PinInfo] = {}

    # -- indeksler --------------------------------------------------------
    def index(self) -> None:
        self._nodes_by_id = {n.node_id: n for n in self.nodes}
        self._pins_by_key = {
            (p.node_id, p.pin_id): p for n in self.nodes for p in n.pins
        }

    def node(self, node_id: str) -> NodeInfo | None:
        return self._nodes_by_id.get(node_id)

    def pin(self, node_id: str, pin_id: str) -> PinInfo | None:
        return self._pins_by_key.get((node_id, pin_id))

    # -- girdi / çıktı ---------------------------------------------------
    @property
    def parameters(self) -> list[PinInfo]:
        if not self.entry:
            return []
        return [
            p for p in self.entry.pins
            if p.direction == "out" and not p.is_exec and not p.hidden
        ]

    @property
    def return_pins(self) -> list[PinInfo]:
        return [
            p
            for result in self.results
            for p in result.pins
            if p.direction == "in" and not p.is_exec and not p.hidden
        ]

    # -- etiketler -------------------------------------------------------
    def pin_label(self, node_id: str, pin_id: str) -> str:
        node = self.node(node_id)
        pin = self.pin(node_id, pin_id)
        if node is None or pin is None:
            return f"{node_id}.{pin_id[:8]}"
        return f"{node.short_id}.{pin.label}"

    # -- değişken üyeleri -------------------------------------------------
    @staticmethod
    def variable_member(node: NodeInfo, pin: PinInfo) -> str:
        """VariableGet/Set pininden 'this->Var' veya 'Var.Üye' başvurusu üretir."""
        variable = node.variable
        if not variable:
            return pin.name

        base = variable.rsplit("->", 1)[-1].rsplit("::", 1)[-1]
        name = pin.name

        if node.category == "var_set" and name.startswith("Output_Get"):
            member = name[len("Output_Get"):].lstrip("_")
            return f"{variable}.{member}" if member else variable

        if name.startswith(base + "_"):
            return f"{variable}.{name[len(base) + 1:]}"

        return variable

    # -- kaynak / ifade çözümleme ---------------------------------------
    def source_ref(self, node: NodeInfo, pin: PinInfo, _stack=None) -> str:
        """Bir ÇIKIŞ pininin düz (iç içe olmayan) başvuru adı."""
        stack = _stack or set()
        key = (node.node_id, pin.pin_id)
        if key in stack:
            return "…"
        stack = stack | {key}

        if node.category == "entry":
            return pin.name

        if node.category == "break":
            inputs = node.data_inputs
            base = self.input_ref(inputs[0], stack) if inputs else "?"
            return f"{base}.{pin.name}"

        if node.category == "var_get":
            return self.variable_member(node, pin)

        if node.category == "var_set" and pin.name.startswith("Output_Get"):
            return self.variable_member(node, pin)

        if node.category == "reroute":
            inputs = node.data_inputs
            return self.input_ref(inputs[0], stack) if inputs else "?"

        if len(node.data_outputs) > 1:
            return f"{node.short_id}.{pin.name}"
        return node.short_id

    def input_ref(self, pin: PinInfo, _stack=None) -> str:
        """Bir GİRİŞ pininin düz başvurusu (kaynak adı ya da varsayılan)."""
        if pin.sources:
            src_node_id, src_pin_id = pin.sources[0]
            src_node = self.node(src_node_id)
            src_pin = self.pin(src_node_id, src_pin_id)
            if src_node and src_pin:
                return self.source_ref(src_node, src_pin, _stack)

        if pin.is_implicit_self:
            return "this"

        if pin.dangling:
            missing = ", ".join(
                sorted({d.rsplit(":", 1)[0] for d in pin.dangling})
            )
            return f"?({missing} bulunamadı)"

        if pin.default != "":
            return f"{pin.default} (varsayılan)"

        return "(bağlı değil)"

    def expression(self, node: NodeInfo, pin: PinInfo, _stack=None) -> str:
        """Bir ÇIKIŞ pininin iç içe (satır içi) ifadesi."""
        stack = _stack or set()
        key = (node.node_id, pin.pin_id)
        if key in stack:
            return "…"
        stack = stack | {key}

        if node.category == "entry":
            return pin.name

        if node.category == "break":
            inputs = node.data_inputs
            base = self.input_expression(inputs[0], stack) if inputs else "?"
            return f"{base}.{pin.name}"

        if node.category == "var_get":
            return self.variable_member(node, pin)

        if node.category == "var_set" and pin.name.startswith("Output_Get"):
            return self.variable_member(node, pin)

        if node.category == "reroute":
            inputs = node.data_inputs
            return (
                self.input_expression(inputs[0], stack) if inputs else "?"
            )

        # Yürütme pini olan (saf olmayan) node: sonucu bir değişkende durur.
        if node.has_exec:
            return self.source_ref(node, pin)

        args = [
            p for p in node.data_inputs if p.sources or not p.hidden
        ]

        if node.category == "make":
            parts = ", ".join(
                f"{p.name}={self.input_expression(p, stack)}" for p in args
            )
            outputs = node.data_outputs
            struct_name = outputs[0].type_label if outputs else "Struct"
            return f"{struct_name}{{{parts}}}"

        values = [self.input_expression(p, stack) for p in args]
        symbol = OPERATOR_SYMBOLS.get(node.label)

        if symbol and len(values) >= 2:
            return "(" + f" {symbol} ".join(values) + ")"

        callee = node.function_ref.rsplit("::", 1)[-1] or node.label
        return f"{callee}({', '.join(values)})"

    def input_expression(self, pin: PinInfo, _stack=None) -> str:
        if pin.sources:
            src_node_id, src_pin_id = pin.sources[0]
            src_node = self.node(src_node_id)
            src_pin = self.pin(src_node_id, src_pin_id)
            if src_node and src_pin:
                return self.expression(src_node, src_pin, _stack)

        if pin.is_implicit_self:
            return "this"

        if pin.dangling:
            return "?"

        if pin.default != "":
            return pin.default

        return "∅"


# --------------------------------------------------------------------------
# Üretim
# --------------------------------------------------------------------------

def node_category(node_class: str) -> tuple[str, str]:
    class_name = (node_class or "").rsplit(".", 1)[-1]
    name = class_name.removeprefix("K2Node_").lower()

    for keyword, category, translation_key in NODE_KINDS:
        if keyword in name:
            return category, translation_key

    return "unknown", "unknown_node"


def _node_label(node, category: str) -> str:
    operation = node.properties.get("OperationName") or node.operation_name
    operation = clean_text(str(operation)) if operation else ""

    class_name = str(node.node_class or "UnknownNode").rsplit(".", 1)[-1]
    class_name = re.sub(r"_\d+$", "", class_name)

    if operation and category not in ("entry", "result"):
        return operation

    label = re.sub(r"^K2Node_", "", class_name)
    label = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", label)
    return re.sub(r"[_\s]+", " ", label).strip() or "UnknownNode"


def _function_ref(node) -> str:
    reference = node.properties.get("FunctionReference", "")
    name = _member(reference, "MemberName")
    parent = _object_name(_member(reference, "MemberParent"))

    if not name:
        return ""
    return f"{parent}::{name}" if parent else name


def _variable_name(node) -> str:
    reference = node.properties.get("VariableReference", "")
    name = _member(reference, "MemberName")

    if not name:
        return ""
    if "bSelfContext=True" in reference:
        return f"this->{name}"

    parent = _object_name(_member(reference, "MemberParent"))
    return f"{parent}::{name}" if parent else name


def _type_label(pin) -> tuple[str, str]:
    """(okunabilir tür, C++ ipucu)."""
    category = (pin.pin_type or "").strip().strip('"')
    sub_object = pin.properties.get("PinType.PinSubCategoryObject", "")
    container = pin.properties.get("PinType.ContainerType", "None")
    obj = _object_name(sub_object) if sub_object not in ("", "None") else ""

    base_category = category.split(":")[0]

    if base_category == "exec":
        return "exec", ""

    if base_category == "struct" and obj:
        label = obj
        cpp = _CPP_STRUCTS.get(obj, obj if obj.startswith("F") else f"F{obj}")
    elif base_category in ("object", "class", "softobject", "softclass") and obj:
        label = f"{base_category}:{obj}"
        cpp = f"{obj}*" if base_category == "object" else f"TSubclassOf<{obj}>"
    elif base_category in ("byte", "enum") and obj:
        label = obj
        cpp = obj
    else:
        label = category or "?"
        cpp = _CPP_SIMPLE.get(category, _CPP_SIMPLE.get(base_category, ""))

    if container not in ("None", ""):
        label = f"{container}<{label}>"
        cpp = {
            "Array": f"TArray<{cpp}>",
            "Set": f"TSet<{cpp}>",
            "Map": "TMap<?, ?>",
        }.get(container, cpp)

    return label, cpp


def _asset_name(raw_text: str) -> str:
    match = re.search(r"/(\w+)\.\1:", raw_text)
    return match.group(1) if match else ""


def build_report(raw_text: str) -> BlueprintReport:
    parsed = parse_blueprint_text(raw_text)
    raw_nodes = parsed["nodes"]

    links = extract_blueprint_links(raw_nodes)
    issues: list[str] = list(validate_blueprint_graph(raw_nodes))

    analysis_result = build_blueprint_analysis(
        raw_nodes, links, return_model=True
    )
    execution: dict[str, list[tuple[str, str, str]]] = {}

    if isinstance(analysis_result, tuple):
        _lines, analysis = analysis_result
        for issue in analysis.issues:
            if issue not in issues:
                issues.append(issue)
    else:
        # Kimlik çakışması gibi durumlarda parser yalnızca sorun listesi döner.
        for issue in analysis_result:
            if issue not in issues:
                issues.append(issue)

    report = BlueprintReport(
        function_name="",
        asset_name=_asset_name(raw_text),
        execution=execution,
        issues=issues,
        pin_count=parsed.get("pin_count", 0),
    )

    node_ids = {n.node_id for n in raw_nodes}
    pin_ids = {
        (n.node_id, p.pin_id) for n in raw_nodes for p in n.pins
    }

    for position, raw in enumerate(raw_nodes, start=1):
        category, kind_text = node_category(raw.node_class)
        node = NodeInfo(
            node_id=raw.node_id,
            short_id=f"N{position:03d}",
            label=_node_label(raw, category),
            category=category,
            kind_text=kind_text,
            node_class=(raw.node_class or "").rsplit(".", 1)[-1],
            function_ref=_function_ref(raw),
            variable=_variable_name(raw),
            properties=dict(raw.properties),
        )

        for raw_pin in raw.pins:
            type_label, cpp_hint = _type_label(raw_pin)
            direction_text = raw_pin.direction.strip().strip('"')
            friendly = clean_text(raw_pin.pin_friendly_name or "")
            name = clean_text(raw_pin.pin_name or "")
            display = friendly if friendly and name.lower() == "self" else name
            display = clean_member_name(display or friendly or "(isimsiz)")
            extra_friendly = (
                friendly
                if friendly
                and friendly.lower() != display.lower()
                and name.lower() != "self"
                else ""
            )

            default_text = clean_text(raw_pin.default_value or "")
            if default_text == "" and direction_text != "EGPD_Output":
                # Unreal, DefaultValue boşsa AutogeneratedDefaultValue'yu gösterir.
                default_text = clean_text(
                    raw_pin.properties.get("AutogeneratedDefaultValue", "")
                )

            dangling = []
            for linked in raw_pin.linked_to:
                if ":" not in linked:
                    dangling.append(linked)
                    continue
                target_node, target_pin = linked.rsplit(":", 1)
                if (target_node, target_pin) not in pin_ids:
                    dangling.append(linked)

            node.pins.append(
                PinInfo(
                    node_id=raw.node_id,
                    pin_id=raw_pin.pin_id,
                    name=display,
                    direction=(
                        "out" if direction_text == "EGPD_Output" else "in"
                    ),
                    is_exec=type_label == "exec",
                    pin_type=raw_pin.pin_type,
                    type_label=type_label,
                    cpp_hint=cpp_hint,
                    default=default_text,
                    hidden=raw_pin.properties.get("bHidden") == "True",
                    friendly=extra_friendly,
                    dangling=dangling,
                )
            )

        report.nodes.append(node)

    report.index()

    # Bağlantılar -----------------------------------------------------------
    for link in links:
        source = report.pin(link.source_node_id, link.source_pin_id)
        target = report.pin(link.target_node_id, link.target_pin_id)
        is_exec = bool(
            (source and source.is_exec) or (target and target.is_exec)
        )

        report.links.append(
            LinkInfo(
                source_node=link.source_node_id,
                source_pin=link.source_pin_id,
                target_node=link.target_node_id,
                target_pin=link.target_pin_id,
                is_exec=is_exec,
                direction_known=link.direction_known,
            )
        )

        if not link.direction_known:
            issues.append(
                "Yönü belirlenemeyen bağlantı: "
                f"{report.pin_label(link.source_node_id, link.source_pin_id)}"
                " ↔ "
                f"{report.pin_label(link.target_node_id, link.target_pin_id)}"
            )
            continue

        if source and target:
            if link.target_pin_id not in [s[1] for s in source.targets]:
                source.targets.append(
                    (link.target_node_id, link.target_pin_id)
                )
            if link.source_pin_id not in [s[1] for s in target.sources]:
                target.sources.append(
                    (link.source_node_id, link.source_pin_id)
                )

    # Yürütme kenarları: pin sırasıyla, temiz pin adlarıyla -----------------
    report.execution = {}
    for node in report.nodes:
        for pin in node.pins:
            if not (pin.is_exec and pin.direction == "out"):
                continue
            for target_node_id, target_pin_id in pin.targets:
                target_pin = report.pin(target_node_id, target_pin_id)
                report.execution.setdefault(node.node_id, []).append(
                    (
                        target_node_id,
                        pin.label,
                        target_pin.label if target_pin else target_pin_id,
                    )
                )

    # Varsayılanı olan girişler için parser'ın yanlış 'Missing input' uyarısını ele.
    defaulted = {
        (node.node_id, pin.name)
        for node in report.nodes
        for pin in node.pins
        if pin.direction == "in" and pin.default != "" and not pin.sources
    }

    def _is_false_missing(issue: str) -> bool:
        if not issue.startswith("Missing input: Node "):
            return False
        node_part, _, rest = issue[len("Missing input: Node "):].partition(",")
        pin_name = rest.strip().removeprefix("Pin ").split(" has ")[0]
        return (node_part.strip(), pin_name) in defaulted

    report.issues[:] = [i for i in report.issues if not _is_false_missing(i)]

    # Giriş / çıkış node'ları ---------------------------------------------
    report.entry = next(
        (n for n in report.nodes if n.category == "entry"), None
    )
    report.results = [n for n in report.nodes if n.category == "result"]

    if report.entry is not None:
        raw_entry = next(n for n in raw_nodes if n.node_id == report.entry.node_id)
        report.function_name = (
            raw_entry.operation_name or report.entry.function_ref
        )

    return report


# --------------------------------------------------------------------------
# Tablo satırları (arayüz bunları olduğu gibi gösterir)
# --------------------------------------------------------------------------

def node_rows(report: BlueprintReport) -> list[tuple]:
    rows = []
    for node in report.nodes:
        connected = sum(
            1 for p in node.pins if p.sources or p.targets
        )
        rows.append(
            (
                node.short_id,
                node.label,
                node.kind_text,
                node.function_ref or node.variable,
                len(node.pins),
                connected,
                node.node_id,
            )
        )
    return rows


NODE_HEADERS = (
    "Kısa ID", "İsim", "Tür", "Fonksiyon / Değişken",
    "Pin", "Bağlı pin", "Node ID",
)


def pin_rows(
    report: BlueprintReport, show_hidden: bool = False
) -> list[tuple]:
    rows = []
    for node in report.nodes:
        for pin in node.pins:
            if pin.hidden and not show_hidden:
                continue

            connections = [
                f"← {report.pin_label(n, p)}" for n, p in pin.sources
            ] + [
                f"→ {report.pin_label(n, p)}" for n, p in pin.targets
            ] + [
                f"✗ {d.rsplit(':', 1)[0]} (bulunamadı)" for d in pin.dangling
            ]

            rows.append(
                (
                    node.short_id,
                    node.label,
                    pin.label,
                    "Çıkış" if pin.direction == "out" else "Giriş",
                    pin.type_label,
                    pin.default,
                    "; ".join(connections),
                )
            )
    return rows


PIN_HEADERS = (
    "Node", "Node adı", "Pin", "Yön", "Tür", "Varsayılan", "Bağlantılar",
)


def link_rows(report: BlueprintReport) -> list[tuple]:
    rows = []
    for link in report.links:
        rows.append(
            (
                report.pin_label(link.source_node, link.source_pin).split(".")[0],
                report.pin_label(link.source_node, link.source_pin),
                report.pin_label(link.target_node, link.target_pin).split(".")[0],
                report.pin_label(link.target_node, link.target_pin),
                "Yürütme" if link.is_exec else "Veri",
                "Evet" if link.direction_known else "Hayır",
            )
        )
    return rows


LINK_HEADERS = (
    "Kaynak node", "Kaynak pin", "Hedef node", "Hedef pin",
    "Tür", "Yön belli",
)
