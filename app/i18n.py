"""Small, centralized Turkish/English localization helpers."""

TRANSLATIONS = {
    "tr": {
        "language": "Dil", "input": "Girdi", "output": "Çıktı",
        "parse": "Blueprint'i Ayrıştır", "paste": "Panodan yapıştır",
        "clear": "Temizle", "output_format": "Çıktı biçimi:",
        "copy_output": "Çıktıyı kopyala", "show_hidden": "Gizli pinleri göster",
        "nodes": "Node'lar", "pins": "Pinler", "links": "Bağlantılar",
        "filter": "Filtrele (node, pin, tür...)", "copy_table": "Tabloyu kopyala",
        "not_parsed": "Henüz ayrıştırma yapılmadı.",
        "paste_hint": "Unreal Engine'den kopyaladığın Blueprint metnini buraya yapıştır\n(Begin Object ... ile başlayan metin).",
        "output_hint": "Ayrıştırma sonucu burada görünecek.",
        "empty_title": "Boş girdi", "empty_message": "Önce Blueprint metnini yapıştır.",
        "parse_error": "Ayrıştırma hatası", "not_found_title": "Node bulunamadı",
        "not_found_message": "Metinde 'Begin Object' ile başlayan node bulunamadı.",
        "copied": "Çıktı panoya kopyalandı.", "row_count": "satır",
        "short": "Kısa", "medium": "Orta (AI / C++ için)", "long": "Uzun (tam döküm)",
        "header_node_id": "Kısa ID", "header_name": "İsim", "header_kind": "Tür",
        "header_function": "Fonksiyon / Değişken", "header_pin": "Pin",
        "header_connected": "Bağlı pin", "header_id": "Node ID",
        "header_node": "Node", "header_node_name": "Node adı", "header_direction": "Yön",
        "header_type": "Tür", "header_default": "Varsayılan", "header_connections": "Bağlantılar",
        "header_source_node": "Kaynak node", "header_source_pin": "Kaynak pin",
        "header_target_node": "Hedef node", "header_target_pin": "Hedef pin",
        "header_known": "Yön belli", "in": "Giriş", "out": "Çıkış",
        "execution": "Yürütme", "data": "Veri", "yes": "Evet", "no": "Hayır",
        "rows_suffix": "satır",
        "unknown_or_unclassified_node": "Bilinmeyen veya sınıflandırılmamış düğüm",
        "branch_flow_note": (
            "Not: Akış dallanıyor; dal yorumu henüz işlenmiyor. "
            "Yukarıdaki bağlantılar ham yürütme akışını gösteriyor."
        ),
        "pure": "saf",
        "array": "dizi",
        "default": "varsayılan",
        "none": "yok",
        "cpp_hints_note": (
            "C++ ipuçları pin türlerinden otomatik çıkarıldı; "
            "proje türlerine göre doğrula."
        ),
    },
    "en": {
        "language": "Language", "input": "Input", "output": "Output",
        "parse": "Parse Blueprint", "paste": "Paste from clipboard",
        "clear": "Clear", "output_format": "Output format:",
        "copy_output": "Copy output", "show_hidden": "Show hidden pins",
        "nodes": "Nodes", "pins": "Pins", "links": "Connections",
        "filter": "Filter (node, pin, type...)", "copy_table": "Copy table",
        "not_parsed": "Nothing parsed yet.",
        "paste_hint": "Paste Blueprint text copied from Unreal Engine here\n(Text beginning with Begin Object ...).",
        "output_hint": "Parsed output will appear here.",
        "empty_title": "Empty input", "empty_message": "Paste Blueprint text first.",
        "parse_error": "Parsing error", "not_found_title": "No nodes found",
        "not_found_message": "No nodes beginning with 'Begin Object' were found in the text.",
        "copied": "Output copied to clipboard.", "row_count": "rows",
        "short": "Short", "medium": "Medium (for AI / C++)", "long": "Long (full dump)",
        "header_node_id": "Short ID", "header_name": "Name", "header_kind": "Kind",
        "header_function": "Function / Variable", "header_pin": "Pins",
        "header_connected": "Connected pins", "header_id": "Node ID",
        "header_node": "Node", "header_node_name": "Node name", "header_direction": "Direction",
        "header_type": "Type", "header_default": "Default", "header_connections": "Connections",
        "header_source_node": "Source node", "header_source_pin": "Source pin",
        "header_target_node": "Target node", "header_target_pin": "Target pin",
        "header_known": "Direction known", "in": "Input", "out": "Output",
        "execution": "Execution", "data": "Data", "yes": "Yes", "no": "No",
        "rows_suffix": "rows",
        "unknown_or_unclassified_node": "Unknown or unclassified node",
        "branch_flow_note": (
            "Note: The flow contains branches; branch interpretation "
            "is not yet implemented. The connections above represent "
            "the raw execution flow."
        ),
        "pure": "pure",
        "array": "array",
        "default": "default",
        "none": "none",
        "cpp_hints_note": (
            "C++ hints were inferred automatically from pin types; "
            "verify them against your project types."
        ),
    },
}

OUTPUT_REPLACEMENTS = {
    # General output
    "Blueprint içinde node bulunamadı.": "No nodes found in the Blueprint.",
    "KISA ÖZET": "QUICK SUMMARY",
    "TAM BLUEPRINT DÖKÜMÜ": "FULL BLUEPRINT DUMP",
    "UNREAL ENGINE BLUEPRINT → C++ ÇEVİRİ VERİSİ": "UNREAL ENGINE BLUEPRINT → C++ CONVERSION DATA",
    "Aşağıda tek bir Blueprint fonksiyonunun yapısal dökümü var.": "Structural breakdown of a single Blueprint function follows.",

    # Function information
    "Fonksiyon:": "Function:",
    "Fonksiyon :": "Function :",
    "Fonksiyon": "Function",
    "Ad     :": "Name   :",
    "Girdi     :": "Inputs    :",
    "Çıktı     :": "Outputs   :",
    "Boyut     :": "Size      :",
    "İçerik    :": "Contents  :",
    "Girdiler (parametreler):": "Inputs (parameters):",
    "Çıktılar (dönüş değerleri):": "Outputs (return values):",

    # Descriptions
    "Ne yapıyor:": "What it does:",
    "Dönüş değeri yok (void).": "No return value (void).",
    "Yürütme sırasıyla işler:": "Operations in execution order:",
    "Dallanma:": "Branch:",
    "N001, N002... node kısa kimlikleridir; bir ifadede N004 görürsen o node'un sonucu demektir.": (
        "N001, N002... are short node IDs; when you see N004 in an expression, "
        "it represents the output of that node."
    ),

    # Warnings and notes
    "Dikkat:": "Warning:",
    "sorun var": "issue(s)",
    "ayrıntı için Uzun çıktıya bak": "see the Long output for details",
    "Sorun bulunmadı.": "No issues found.",
    "Not: Akış dallanıyor; dal yorumu henüz işlenmiyor, yukarıdaki bağlantılar ham dökümdür.": (
        "Note: The flow contains branches; branch interpretation is not yet "
        "implemented. The connections above represent the raw execution flow."
    ),
    "'C++' ipuçları pin türünden otomatik çıkarıldı; proje türlerine göre doğrula.": (
        "C++ hints were inferred automatically from pin types; "
        "verify them against your project types."
    ),

    # Section headings
    "FONKSİYON": "FUNCTION",
    "YÜRÜTME AKIŞI (exec)": "EXECUTION FLOW (exec)",
    "YÜRÜTME AKIŞI": "EXECUTION FLOW",
    "İŞLEM ADIMLARI (veri bağımlılık sırasıyla; 'saf' = yan etkisiz)": (
        "OPERATIONS (in data dependency order; 'pure' = no side effects)"
    ),
    "ÇIKTI ATAMALARI": "OUTPUT ASSIGNMENTS",
    "NOTLAR": "NOTES",
    "SORUNLAR": "ISSUES",

    # Empty values
    "(yok)": "(none)",
    "yok": "none",
    "(işlem node'u yok)": "(no operation nodes)",
    "(çıktı ataması yok)": "(no output assignments)",
    "(yürütme bağlantısı bulunamadı)": "(no execution connections found)",

    # Pin labels
    "Pinler:": "Pins:",
    "→ çıkış": "→ output",
    "← giriş": "← input",
    "varsayılan:": "default:",
    "gizli": "hidden",
    "bulunamadı": "not found",

    # Node classifications
    "Bilinmeyen veya sınıflandırılmamış düğüm": "Unknown or unclassified node",
    "Fonksiyon girişi": "Function entry",
    "Fonksiyon çıkışı": "Function result",
    "Fonksiyon çağrısı (dizi)": "Function call (array)",
    "Fonksiyon çağrısı": "Function call",
    "Olay": "Event",
    "Koşullu dallanma": "Conditional branch",
    "Sıralı yürütme": "Sequence",
    "Makro çağrısı": "Macro call",
    "Yapıyı parçalara ayırma": "Break struct",
    "Yapı oluşturma": "Make struct",
    "Matematiksel / mantıksal işlem": "Math / logic operation",
    "Değişken okuma": "Get variable",
    "Değişken yazma": "Set variable",
    "Koşula göre değer seçme": "Select value by condition",
    "Tür dönüşümü": "Type conversion",
    "Bağlantı yönlendirme": "Reroute",
    "Açıklama düğümü": "Comment node",
}



def tr(key: str, language: str = "tr") -> str:
    return TRANSLATIONS.get(language, TRANSLATIONS["tr"]).get(key, key)


def localize_output(text: str, language: str) -> str:
    if language == "tr":
        return text
    for source, target in sorted(OUTPUT_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    return text


HEADER_KEYS = {
    "Kısa ID": "header_node_id", "İsim": "header_name", "Tür": "header_kind",
    "Fonksiyon / Değişken": "header_function", "Pin": "header_pin",
    "Bağlı pin": "header_connected", "Node ID": "header_id",
    "Node": "header_node", "Node adı": "header_node_name", "Yön": "header_direction",
    "Varsayılan": "header_default", "Bağlantılar": "header_connections",
    "Kaynak node": "header_source_node", "Kaynak pin": "header_source_pin",
    "Hedef node": "header_target_node", "Hedef pin": "header_target_pin",
    "Yön belli": "header_known",
}

TERM_REPLACEMENTS = {
    "Fonksiyon girişi": "Function entry", "Fonksiyon çıkışı": "Function result",
    "Fonksiyon çağrısı (dizi)": "Function call (array)", "Fonksiyon çağrısı": "Function call",
    "Koşullu dallanma": "Conditional branch", "Sıralı yürütme": "Sequence",
    "Makro çağrısı": "Macro call", "Yapıyı parçalara ayırma": "Break struct",
    "Yapı oluşturma": "Make struct", "Matematiksel / mantıksal işlem": "Math / logic operation",
    "Değişken okuma": "Get variable", "Değişken yazma": "Set variable",
    "Koşula göre değer seçme": "Select value by condition", "Tür dönüşümü": "Type conversion",
    "Tür dönüştürme (Cast)": "Type conversion (Cast)", "Tür kontrolü veya dönüştürme": "Type check or conversion",
    "Bağlantı yönlendirme": "Reroute", "Açıklama düğümü": "Comment node",
    "Çıkış": "Output", "Giriş": "Input", "Yürütme": "Execution", "Veri": "Data",
    "Evet": "Yes", "Hayır": "No",
    
}
NODE_KIND_TRANSLATIONS = {
    "tr": {
        "function_entry": "Fonksiyon girişi",
        "function_result": "Fonksiyon çıkışı",
        "function_call_array": "Fonksiyon çağrısı (dizi)",
        "function_call": "Fonksiyon çağrısı",
        "event": "Olay",
        "conditional_branch": "Koşullu dallanma",
        "execution_sequence": "Sıralı yürütme",
        "macro_call": "Makro çağrısı",
        "break_struct": "Break struct",
        "make_struct": "Make struct",
        "math_logic_operation": "Matematiksel / mantıksal işlem",
        "get_variable": "Değişken okuma",
        "set_variable": "Değişken yazma",
        "select_value": "Koşula göre değer seçme",
        "type_conversion": "Tür dönüşümü",
        "type_cast": "Tür dönüştürme (Cast)",
        "reroute": "Bağlantı yönlendirme",
        "comment_node": "Açıklama düğümü",
        "unknown_node": "Bilinmeyen veya sınıflandırılmamış düğüm",
    },
    "en": {
        "function_entry": "Function entry",
        "function_result": "Function result",
        "function_call_array": "Function call (array)",
        "function_call": "Function call",
        "event": "Event",
        "conditional_branch": "Conditional branch",
        "execution_sequence": "Execution sequence",
        "macro_call": "Macro call",
        "break_struct": "Break struct",
        "make_struct": "Make struct",
        "math_logic_operation": "Math / logic operation",
        "get_variable": "Get variable",
        "set_variable": "Set variable",
        "select_value": "Select value",
        "type_conversion": "Type conversion",
        "type_cast": "Type cast",
        "reroute": "Reroute",
        "comment_node": "Comment node",
        "unknown_node": "Unknown or unclassified node",
    },
}


def localize_node_kind(key: str, language: str = "tr") -> str:
    translations = NODE_KIND_TRANSLATIONS.get(
        language, NODE_KIND_TRANSLATIONS["tr"]
    )
    return translations.get(key, key)
def localize_cell(value, language: str):
    if language == "tr" or not isinstance(value, str):
        return value
    if value in TERM_REPLACEMENTS:
        return TERM_REPLACEMENTS[value]
    return value
