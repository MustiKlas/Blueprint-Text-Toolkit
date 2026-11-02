from app.i18n import localize_cell, localize_output, tr


def test_ui_translation_has_turkish_and_english_values():
    assert tr("parse", "tr") == "Blueprint'i Ayrıştır"
    assert tr("parse", "en") == "Parse Blueprint"


def test_unknown_translation_key_falls_back_to_key():
    assert tr("missing_key", "en") == "missing_key"


def test_output_localization_preserves_turkish_mode_and_translates_english():
    source = "KISA ÖZET\nSorun bulunmadı."
    assert localize_output(source, "tr") == source
    assert localize_output(source, "en") == "QUICK SUMMARY\nNo issues found."


def test_localized_table_cells_translate_labels_but_preserve_user_data():
    assert localize_cell("Fonksiyon çağrısı", "en") == "Function call"
    assert localize_cell("MyCustomFunction", "en") == "MyCustomFunction"

def test_english_output_has_no_known_turkish_labels():
    from app.i18n import localize_output

    sample = (
        "Dallanma: Example()\n"
        "Outputs : yok\n"
        "→ çıkış\n"
        "← giriş\n"
        "varsayılan: 10\n"
        "gizli"
    )

    result = localize_output(sample, "en")

    assert "Dallanma:" not in result
    assert "yok" not in result
    assert "→ çıkış" not in result
    assert "← giriş" not in result
    assert "varsayılan:" not in result
    assert "gizli" not in result
