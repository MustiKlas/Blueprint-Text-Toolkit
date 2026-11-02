
import json
import sys
import shutil
from pathlib import Path

from PySide6.QtCore import QStandardPaths


# --------------------------------------------------
# RESOURCE PATHS
# --------------------------------------------------

# Programla birlikte gelen başlangıç kütüphanesi.
if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)
else:
    RESOURCE_DIR = Path(__file__).resolve().parent.parent

SEED_LIBRARY_PATH = RESOURCE_DIR / "data" / "node_library.json"


# --------------------------------------------------
# USER DATA PATHS
# --------------------------------------------------

def _get_user_data_dir():
    """Kullanıcının kalıcı uygulama veri klasörünü döndürür."""
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )

    if not location:
        raise RuntimeError(
            "Uygulama veri klasörü belirlenemedi. "
            "QApplication oluşturulduğundan ve uygulama "
            "kimliğinin ayarlandığından emin olun."
        )

    return Path(location)


def _ensure_user_library():
    """Başlangıç kütüphanesini kullanıcı klasörüne ilk kez kopyalar."""
    user_data_dir = _get_user_data_dir()
    user_data_dir.mkdir(parents=True, exist_ok=True)

    library_path = user_data_dir / "node_library.json"

    if not library_path.exists():
        if SEED_LIBRARY_PATH.exists():
            shutil.copy2(SEED_LIBRARY_PATH, library_path)
        else:
            library_path.write_text("{}", encoding="utf-8")

    return library_path


# --------------------------------------------------
# CACHE
# --------------------------------------------------

_LIBRARY_CACHE = None
_LIBRARY_MTIME_NS = None


# --------------------------------------------------
# NODE SIGNATURE
# --------------------------------------------------

def _node_signature(node):
    """Node'un değişmeyen yapısal özelliklerinden bir kimlik oluşturur."""
    pins = sorted(
        (
            (pin.pin_name, pin.pin_type, pin.direction)
            for pin in node.pins
        ),
        key=lambda item: (item[0], item[1], item[2]),
    )

    return {
        "node_class": node.node_class,
        "operation_name": node.operation_name,
        "pins": [
            {
                "name": name,
                "type": pin_type,
                "direction": direction,
            }
            for name, pin_type, direction in pins
        ],
    }


# --------------------------------------------------
# LIBRARY LOADING
# --------------------------------------------------

def _load_library():
    """Node kütüphanesini önbellekten veya diskten yükler."""
    global _LIBRARY_CACHE, _LIBRARY_MTIME_NS

    library_path = _ensure_user_library()

    try:
        current_mtime = library_path.stat().st_mtime_ns
    except OSError:
        return {}

    if (
        _LIBRARY_CACHE is not None
        and current_mtime == _LIBRARY_MTIME_NS
    ):
        return _LIBRARY_CACHE

    try:
        library = json.loads(
            library_path.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        library = {}

    _LIBRARY_CACHE = library
    _LIBRARY_MTIME_NS = current_mtime

    return library


# --------------------------------------------------
# NODE OBSERVATION / LEARNING
# --------------------------------------------------

def observe_nodes(nodes):
    """Görülen Node yapılarını kalıcı kütüphaneye kaydeder."""
    global _LIBRARY_CACHE, _LIBRARY_MTIME_NS

    library_path = _ensure_user_library()
    library = _load_library()

    for node in nodes:
        signature = _node_signature(node)

        key = json.dumps(
            signature,
            ensure_ascii=False,
            sort_keys=True,
        )

        if key not in library:
            library[key] = {
                "signature": signature,
                "occurrences": 0,
                "behavior": None,
                "learning_status": "observed",
            }

        entry = library[key]
        entry["occurrences"] += 1

        # Güvenilir dönüşüm düğümlerini otomatik tanı.
        if signature["operation_name"].startswith("Conv_"):
            input_pins = [
                pin for pin in signature["pins"]
                if pin["direction"] == "EGPD_Input"
            ]

            output_pins = [
                pin for pin in signature["pins"]
                if pin["direction"] == "EGPD_Output"
            ]

            if len(input_pins) == 1 and len(output_pins) == 1:
                entry["behavior"] = {
                    "kind": "conversion",
                    "input_pin": input_pins[0]["name"],
                    "output_pin": output_pins[0]["name"],
                    "source_type": input_pins[0]["type"],
                    "target_type": output_pins[0]["type"],
                    "resolution": "passthrough",
                }
                entry["learning_status"] = "learned"

        # MakeVector düğümünü otomatik tanı.
        if signature["operation_name"] == "MakeVector":
            pin_map = {
                pin["name"]: pin
                for pin in signature["pins"]
            }

            required_pins = {"X", "Y", "Z", "ReturnValue"}

            if required_pins.issubset(pin_map):
                if (
                    all(
                        pin_map[name]["direction"] == "EGPD_Input"
                        for name in ("X", "Y", "Z")
                    )
                    and pin_map["ReturnValue"]["direction"] == "EGPD_Output"
                ):
                    entry["behavior"] = {
                        "kind": "make_vector",
                        "input_pins": ["X", "Y", "Z"],
                        "output_pin": "ReturnValue",
                        "resolution": "combine_components",
                    }
                    entry["learning_status"] = "learned"

        # BreakStruct düğümünü otomatik tanı.
        if signature["operation_name"] == "BreakStruct":
            input_pins = [
                pin for pin in signature["pins"]
                if pin["direction"] == "EGPD_Input"
                and pin["type"] == "struct"
            ]

            output_pins = [
                pin for pin in signature["pins"]
                if pin["direction"] == "EGPD_Output"
            ]

            if len(input_pins) == 1 and output_pins:
                entry["behavior"] = {
                    "kind": "break_struct",
                    "input_pin": input_pins[0]["name"],
                    "output_pins": [
                        pin["name"] for pin in output_pins
                    ],
                    "resolution": "extract_fields",
                }
                entry["learning_status"] = "learned"

    # Güncel kütüphaneyi diske kaydet.
    library_path.write_text(
        json.dumps(
            library,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Bellekteki önbelleği güncelle.
    _LIBRARY_CACHE = library
    _LIBRARY_MTIME_NS = library_path.stat().st_mtime_ns

    return library


# --------------------------------------------------
# NODE BEHAVIOR LOOKUP
# --------------------------------------------------

def get_node_behavior(node):
    """Bir Node için kayıtlı davranış tanımını döndürür."""
    signature = _node_signature(node)

    key = json.dumps(
        signature,
        ensure_ascii=False,
        sort_keys=True,
    )

    library = _load_library()
    entry = library.get(key)

    if not entry or entry.get("learning_status") != "learned":
        return None

    return entry.get("behavior")
