"""BlueprintReport'tan üç farklı metin çıktısı üretir.

- kısa : tek bakışta fonksiyon özeti
- orta : bir AI'ya 'bunu C++ yaz' demek için gereken tüm yapısal bilgi
- uzun : her node ve her pin, ayrıntılı döküm

Hiçbiri arayüze bağımlı değildir; ayrı ayrı test edilebilir.
"""

from __future__ import annotations

from collections import Counter

from app.report import BlueprintReport, NodeInfo, PinInfo
from app.i18n import tr, localize_cell, localize_node_kind

OUTPUT_MODES = (
    ("short", "Kısa"),
    ("medium", "Orta (AI / C++ için)"),
    ("long", "Uzun (tam döküm)"),
)

_INLINE_ONLY = {"entry", "result", "break", "var_get", "reroute", "comment"}
LINE = "=" * 64
def _t(key: str, language: str) -> str:
    """Çıktı üreticisine ait metinleri çevirir."""
    translations = {
        "tr": {
            "no_nodes": "Blueprint içinde node bulunamadı.",
            "short_title": "KISA ÖZET",
            "function": "Fonksiyon",
            "input": "Girdi",
            "output": "Çıktı",
            "size": "Boyut",
            "contents": "İçerik",
            "what_it_does": "Ne yapıyor:",
            "no_value": "yok",
            "function_name_missing": "(fonksiyon adı bulunamadı)",
            "asset": "Asset",
            "links": "bağlantı",
            "no_return": "Dönüş değeri yok (void).",
            "execution_order": "Yürütme sırasıyla işler:",
            "warning": "Dikkat:",
            "issues_found": "sorun var",
            "long_details": "ayrıntı için Uzun çıktıya bak",
            "no_issues": "Sorun bulunmadı.",
            "medium_title": "UNREAL ENGINE BLUEPRINT → C++ ÇEVİRİ VERİSİ",
            "medium_description": "Aşağıda tek bir Blueprint fonksiyonunun yapısal dökümü var.",
            "node_id_description": (
                "N001, N002... node kısa kimlikleridir; bir ifadede N004 görürsen "
                "o node'un sonucu demektir."
            ),
            "function_section": "FONKSİYON",
            "name": "Ad",
            "inputs": "Girdiler (parametreler):",
            "outputs": "Çıktılar (dönüş değerleri):",
            "none": "(yok)",
            "execution": "YÜRÜTME AKIŞI (exec)",
            "operations": "İŞLEM ADIMLARI (veri bağımlılık sırasıyla; 'saf' = yan etkisiz)",
            "no_operations": "(işlem node'u yok)",
            "assignments": "ÇIKTI ATAMALARI",
            "no_assignments": "(çıktı ataması yok)",
            "open_form": "açık biçim:",
            "notes": "NOTLAR",
            "dangling_note": (
                "Şu pinler, metinde bulunmayan node'lara bağlı: "
            ),
            "dangling_suffix": (
                ". Metin eksik kopyalanmış olabilir; bu değerler bilinmiyor."
            ),
            "cpp_note": (
                "'C++' ipuçları pin türünden otomatik çıkarıldı; "
                "proje türlerine göre doğrula."
            ),
            "long_title": "TAM BLUEPRINT DÖKÜMÜ",
            "type": "Tür",
            "class": "Sınıf",
            "node_id": "Node ID",
            "variable": "Değişken",
            "pins": "Pinler:",
            "hidden": "gizli",
            "default": "varsayılan",
            "execution_flow": "YÜRÜTME AKIŞI",
            "issues": "SORUNLAR",
            "not_found": "bulunamadı",
            "execution_missing": "(yürütme bağlantısı bulunamadı)",
            "branch": "Dallanma",
            "branch_note": (
                "Not: Akış dallanıyor; dal yorumu henüz işlenmiyor, "
                "yukarıdaki bağlantılar ham dökümdür."
            ),
            "pure": "saf",
            "exec": "exec",
            "out": "çıkış",
            "in": "giriş",
        },
        "en": {
            "no_nodes": "No nodes found in the Blueprint.",
            "short_title": "QUICK SUMMARY",
            "function": "Function",
            "input": "Inputs",
            "output": "Outputs",
            "size": "Size",
            "contents": "Contents",
            "what_it_does": "What it does:",
            "function_name_missing": "(function name not found)",
            "asset": "Asset",
            "links": "connections",
            "no_value": "none",
            "no_return": "No return value (void).",
            "execution_order": "Operations in execution order:",
            "warning": "Warning:",
            "issues_found": "issue(s)",
            "long_details": "see the Long output for details",
            "no_issues": "No issues found.",
            "medium_title": "UNREAL ENGINE BLUEPRINT → C++ CONVERSION DATA",
            "medium_description": "Structural breakdown of a single Blueprint function follows.",
            "node_id_description": (
                "N001, N002... are short node IDs; when you see N004 in an "
                "expression, it represents that node's output."
            ),
            "function_section": "FUNCTION",
            "name": "Name",
            "inputs": "Inputs (parameters):",
            "outputs": "Outputs (return values):",
            "none": "(none)",
            "execution": "EXECUTION FLOW (exec)",
            "operations": "OPERATIONS (in data dependency order; 'pure' = no side effects)",
            "no_operations": "(no operation nodes)",
            "assignments": "OUTPUT ASSIGNMENTS",
            "no_assignments": "(no output assignments)",
            "open_form": "expanded:",
            "notes": "NOTES",
            "dangling_note": "These pins are connected to nodes missing from the text: ",
            "dangling_suffix": ". The text may be incomplete; these values are unknown.",
            "cpp_note": (
                "C++ hints were inferred automatically from pin types; "
                "verify them against your project types."
            ),
            "long_title": "FULL BLUEPRINT DUMP",
            "type": "Type",
            "class": "Class",
            "node_id": "Node ID",
            "variable": "Variable",
            "pins": "Pins:",
            "hidden": "hidden",
            "default": "default",
            "execution_flow": "EXECUTION FLOW",
            "issues": "ISSUES",
            "not_found": "not found",
            "execution_missing": "(no execution connections found)",
            "branch": "Branch",
            "branch_note": (
                "Note: The flow contains branches; branch interpretation is "
                "not yet implemented. The connections above represent the "
                "raw execution flow."
            ),
            "pure": "pure",
            "exec": "exec",
            "out": "output",
            "in": "input",
        },
    }
    return translations.get(language, translations["tr"]).get(key, key)

# --------------------------------------------------------------------------
# Ortak parçalar
# --------------------------------------------------------------------------

def _title(report: BlueprintReport, language: str = "tr") -> str:
    name = report.function_name or _t("function_name_missing", language)

    if report.asset_name:
        return f"{name}  ({_t('asset', language)}: {report.asset_name})"

    return name


def _pin_text(
    pin: PinInfo,
    with_cpp: bool = False,
    language: str = "tr",
) -> str:
    text = f"{pin.name} : {pin.type_label}"
    if with_cpp and pin.cpp_hint and pin.cpp_hint != pin.type_label:
        text += f"  [C++: {pin.cpp_hint}]"
    if pin.default != "":
        text += f"  ({_t('default', language)}: {pin.default})"
    return text


def _exec_order(report: BlueprintReport) -> list[str]:
    """Entry'den başlayarak yürütme sırasına göre node kimlikleri."""
    if report.entry is None:
        return []

    order: list[str] = []
    stack = [report.entry.node_id]

    while stack:
        node_id = stack.pop()
        if node_id in order:
            continue
        order.append(node_id)
        successors = [t[0] for t in report.execution.get(node_id, [])]
        stack.extend(reversed(successors))

    return order


def _execution_lines(report: BlueprintReport, language: str = "tr") -> list[str]:
    lines = []
    branching = False

    for node_id in _exec_order(report):
        node = report.node(node_id)
        edges = report.execution.get(node_id, [])

        if node is None:
            continue

        if len(edges) > 1:
            branching = True

        for target_id, source_pin, target_pin in edges:
            target = report.node(target_id)
            target_name = target.short_id if target else target_id
            lines.append(
                f"{node.short_id} ({node.label}).{source_pin}"
                f"  →  {target_name}"
                f" ({target.label if target else '?'}).{target_pin}"
            )

    if not lines:
        lines.append(_t("execution_missing", language))

    if branching:
        lines.append(_t("branch_note", language))

    return lines


def _effect_lines(report: BlueprintReport, language: str = "tr") -> list[str]:
    """Yan etkili adımlar (çağrı, değişken yazma, dallanma) yürütme sırasıyla."""
    lines = []

    for node_id in _exec_order(report):
        node = report.node(node_id)
        if node is None:
            continue

        visible = [p for p in node.data_inputs if p.sources or not p.hidden]

        if node.category == "branch":
            condition = next(
                (p for p in node.data_inputs if p.name.lower() == "condition"),
                None,
            )
            text = report.input_expression(condition) if condition else "?"
            lines.append(f"{_t('branch', language)}: {text}")
        elif node.category == "var_set":
            value = report.input_expression(visible[0]) if visible else "?"
            lines.append(f"{node.variable or '?'} = {value}")
        elif node.category in ("call", "macro") and node.has_exec:
            args = ", ".join(
                report.input_expression(p)
                for p in visible
                if not p.is_implicit_self
            )
            lines.append(f"{node.function_ref or node.label}({args})")

    return lines


def _statement_nodes(report: BlueprintReport) -> list[NodeInfo]:
    """İşlem satırı üretilecek node'ları veri bağımlılık sırasıyla döndürür."""
    candidates = [
        n for n in report.nodes if n.category not in _INLINE_ONLY
    ]
    candidate_ids = {n.node_id for n in candidates}

    exec_index = {
        node_id: index for index, node_id in enumerate(_exec_order(report))
    }

    def dependencies(node: NodeInfo) -> set[str]:
        found = set()
        for pin in node.data_inputs:
            stack = list(pin.sources)
            seen = set()
            while stack:
                source_id, source_pin_id = stack.pop()
                if (source_id, source_pin_id) in seen:
                    continue
                seen.add((source_id, source_pin_id))

                if source_id in candidate_ids:
                    found.add(source_id)
                    continue

                # Satır içi node'lar (BreakStruct, Reroute...) üzerinden geç.
                source_node = report.node(source_id)
                if source_node is not None:
                    for inner in source_node.data_inputs:
                        stack.extend(inner.sources)
        found.discard(node.node_id)
        return found

    remaining = {n.node_id: dependencies(n) for n in candidates}
    original = {n.node_id: i for i, n in enumerate(candidates)}
    by_id = {n.node_id: n for n in candidates}
    ordered: list[NodeInfo] = []

    while remaining:
        ready = [nid for nid, deps in remaining.items() if not deps]

        if not ready:  # döngü: kalanları özgün sırayla ekle
            ready = sorted(remaining, key=original.get)

        ready.sort(
            key=lambda nid: (exec_index.get(nid, 10**6), original[nid])
        )
        chosen = ready[0]
        ordered.append(by_id[chosen])
        del remaining[chosen]

        for deps in remaining.values():
            deps.discard(chosen)

    return ordered


def _statement(report: BlueprintReport, node: NodeInfo, language: str = "tr") -> str:
    kind = (
        f"{localize_node_kind(node.kind_text, language)} · "
        f"{_t('exec' if node.has_exec else 'pure', language)}"
    )
    if node.category == "operator":
        kind += f" · {node.label}"
    outputs = [p for p in node.data_outputs if not p.hidden]
    inputs = [p for p in node.data_inputs if p.sources or not p.hidden]

    if len(outputs) == 1:
        result = f"  ->  {outputs[0].type_label}"
        if outputs[0].cpp_hint:
            result += f" ({outputs[0].cpp_hint})"
    elif outputs:
        result = "  ->  (" + ", ".join(
            f"{p.name}:{p.type_label}" for p in outputs
        ) + ")"
    else:
        result = ""

    if node.category == "var_set":
        value = ", ".join(report.input_ref(p) for p in inputs) or "?"
        return f"{node.short_id} [{kind}]  {node.variable or '?'} = {value}"

    callee = node.function_ref or node.label
    args = ", ".join(f"{p.name}={report.input_ref(p)}" for p in inputs)
    return f"{node.short_id} [{kind}]  {callee}({args}){result}"


# --------------------------------------------------------------------------
# KISA
# --------------------------------------------------------------------------

def build_short(report: BlueprintReport, language: str = "tr") -> str:
    if not report.nodes:
        return _t("no_nodes", language)

    lines = [_t("short_title", language), LINE]
    lines.append(f"{_t('function', language)} : {_title(report, language)}")

    parameters = report.parameters
    returns = report.return_pins

    lines.append(
        f"{_t('input', language):9}: "
        + (
            ", ".join(f"{p.name} ({p.type_label})" for p in parameters)
            or _t("no_value", language)
        )
    )
    lines.append(
        f"{_t('output', language):9}: "
        + (
            ", ".join(f"{p.name} ({p.type_label})" for p in returns)
            or _t("no_value", language)
        )
    )
    lines.append(
        f"{_t('size', language):9}: {len(report.nodes)} node · "
        f"{report.pin_count} pin · {len(report.links)} {_t('links', language)}"
    )

    kinds = Counter(
        localize_node_kind(n.kind_text, language)
        for n in report.nodes
        if n.category not in ("entry", "result")
    )

    if kinds:
        lines.append(
            f"{_t('contents', language):9}: "
            + ", ".join(f"{kind} ×{count}" for kind, count in kinds.items())
        )

    lines += ["", _t("what_it_does", language)]
    produced = False

    for result in report.results:
        for pin in result.pins:
            if pin.direction != "in" or pin.is_exec or pin.hidden:
                continue

            produced = True
            lines.append(f"  {pin.name} = {report.input_expression(pin)}")

    if not produced:
        lines.append(f"  {_t('no_return', language)}")

    effects = _effect_lines(report, language)

    if effects:
        lines += ["", _t("execution_order", language)]
        lines += [f"  {i}. {text}" for i, text in enumerate(effects, 1)]

    lines.append("")

    if report.issues:
        lines.append(
            f"{_t('warning', language)} {len(report.issues)} "
            f"{_t('issues_found', language)} "
            f"({_t('long_details', language)})."
        )
    else:
        lines.append(_t("no_issues", language))

    return "\n".join(lines)


# --------------------------------------------------------------------------
# ORTA  (AI / C++ için)
# --------------------------------------------------------------------------
def build_medium(report: BlueprintReport, language: str = "tr") -> str:
    if not report.nodes:
        return _t("no_nodes", language)

    lines = [
        _t("medium_title", language),
        LINE,
        _t("medium_description", language),
        _t("node_id_description", language),
        "",
        _t("function_section", language),
        f"  {_t('name', language):6}: {_title(report, language)}",
    ]

    parameters = report.parameters
    lines.append(f"  {_t('inputs', language)}")
    lines += [
        f"    - {_pin_text(p, True, language)}" for p in parameters
    ] or [f"    {_t('none', language)}"]

    returns = report.return_pins
    lines.append(f"  {_t('outputs', language)}")
    lines += [
        f"    - {_pin_text(p, True, language)}" for p in returns
    ] or [f"    {_t('none', language)}"]

    lines += ["", _t("execution", language)]
    lines += [
        f"  {line}"
        for line in _execution_lines(report, language)
    ]

    lines += ["", _t("operations", language)]

    statements = _statement_nodes(report)

    if statements:
        lines += [
            f"  {_statement(report, node, language)}"
            for node in statements
        ]
    else:
        lines.append(f"  {_t('no_operations', language)}")

    lines += ["", _t("assignments", language)]

    assigned = False

    for result in report.results:
        for pin in result.pins:
            if pin.direction != "in" or pin.is_exec or pin.hidden:
                continue

            assigned = True
            lines.append(f"  {pin.name} = {report.input_ref(pin)}")
            lines.append(
                f"      {_t('open_form', language)} "
                f"{report.input_expression(pin)}"
            )

    if not assigned:
        lines.append(f"  {_t('no_assignments', language)}")

    notes = []

    unresolved = [
        f"{node.short_id}.{pin.name}"
        for node in report.nodes
        for pin in node.pins
        if pin.dangling
    ]

    if unresolved:
        notes.append(
            _t("dangling_note", language)
            + ", ".join(unresolved)
            + _t("dangling_suffix", language)
        )

    notes.append(_t("cpp_note", language))

    lines += ["", _t("notes", language)]
    lines += [f"  - {note}" for note in notes]

    return "\n".join(lines)
# --------------------------------------------------------------------------
# UZUN
# --------------------------------------------------------------------------
def build_long(report: BlueprintReport, language: str = "tr") -> str:
    if not report.nodes:
        return _t("no_nodes", language)

    lines = [
        _t("long_title", language),
        LINE,
        f"{_t('function', language)}: {_title(report, language)}",
        "",
    ]

    for node in report.nodes:
        lines.append(f"{node.short_id} — {node.label}")
        lines.append(
            f"  {_t('type', language):8}: "
            f"{localize_node_kind(node.kind_text, language)}"
        )
        lines.append(f"  {_t('class', language):8}: {node.node_class}")
        lines.append(f"  {_t('node_id', language):8}: {node.node_id}")

        if node.function_ref:
            lines.append(
                f"  {_t('function', language)}: {node.function_ref}"
            )

        if node.variable:
            lines.append(
                f"  {_t('variable', language):8}: {node.variable}"
            )

        lines.append(f"  {_t('pins', language)}")

        for pin in node.pins:
            arrow = (
                f"→ {_t('out', language)}"
                if pin.direction == "out"
                else f"← {_t('in', language)}"
            )

            flags = []

            if pin.hidden:
                flags.append(_t("hidden", language))

            text = f"    - {pin.name} [{arrow}] {pin.type_label}"

            if pin.cpp_hint and pin.cpp_hint != pin.type_label:
                text += f" (C++: {pin.cpp_hint})"

            if pin.default != "":
                text += (
                    f" | {_t('default', language)}: {pin.default}"
                )

            if flags:
                text += f" | {', '.join(flags)}"

            lines.append(text)

            for source_node, source_pin in pin.sources:
                lines.append(
                    f"        ← {report.pin_label(source_node, source_pin)}"
                )

            for target_node, target_pin in pin.targets:
                lines.append(
                    f"        → {report.pin_label(target_node, target_pin)}"
                )

            for missing in pin.dangling:
                lines.append(
                    f"        ✗ {missing.rsplit(':', 1)[0]} "
                    f"{_t('not_found', language)}"
                )

        lines.append("")

    lines += [_t("execution_flow", language)]
    lines += [
        f"  {line}"
        for line in _execution_lines(report, language)
    ]

    lines += ["", _t("issues", language)]

    if report.issues:
        lines += [f"  - {issue}" for issue in report.issues]
    else:
        lines.append(f"  {_t('no_issues', language)}")

    return "\n".join(lines)

BUILDERS = {
    "short": build_short,
    "medium": build_medium,
    "long": build_long,
}


def build_output(
    report: BlueprintReport, mode: str, language: str = "tr"
) -> str:
    return BUILDERS[mode](report, language)