import sys

from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QSettings

from app.i18n import HEADER_KEYS, localize_cell, tr
from app.node_registry import observe_nodes
from app.outputs import OUTPUT_MODES, build_output
from app.parser import parse_blueprint_text
from app.report import (
    LINK_HEADERS,
    NODE_HEADERS,
    PIN_HEADERS,
    BlueprintReport,
    build_report,
    link_rows,
    node_rows,
    pin_rows,
)


class TablePanel(QWidget):
    """Filtre kutusu, tablo ve 'kopyala' düğmesi olan tekrar kullanılabilir panel."""

    def __init__(self, headers, extra_widget=None):
        super().__init__()
        self.header_keys = headers
        self.extra_widget = extra_widget

        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(list(headers))
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(tr("filter"))
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self.apply_filter)

        self.count_label = QLabel("")
        self.copy_button = QPushButton(tr("copy_table"))
        copy_button = self.copy_button
        copy_button.clicked.connect(self.copy_table)

        top = QHBoxLayout()
        top.addWidget(self.filter_edit, 1)
        if extra_widget is not None:
            top.addWidget(extra_widget)
        top.addWidget(self.count_label)
        top.addWidget(copy_button)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)

    def set_language(self, language):
        self.language = language
        self.table.setHorizontalHeaderLabels([tr(HEADER_KEYS.get(key, key), language) for key in self.header_keys])
        self.filter_edit.setPlaceholderText(tr("filter", language))
        self.copy_button.setText(tr("copy_table", language))
        self.apply_filter()

    def set_rows(self, rows):
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                self.table.setItem(
                    row_index, column, QTableWidgetItem(str(localize_cell(value, getattr(self, "language", "tr"))))
                )

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.apply_filter()

    def apply_filter(self):
        needle = self.filter_edit.text().strip().lower()
        visible = 0

        for row in range(self.table.rowCount()):
            match = not needle or any(
                needle in (self.table.item(row, c).text().lower())
                for c in range(self.table.columnCount())
                if self.table.item(row, c)
            )
            self.table.setRowHidden(row, not match)
            visible += match

        self.count_label.setText(f"{visible}/{self.table.rowCount()} {tr('rows_suffix', getattr(self, 'language', 'tr'))}")

    def copy_table(self):
        headers = [
            self.table.horizontalHeaderItem(c).text()
            for c in range(self.table.columnCount())
        ]
        lines = ["\t".join(headers)]

        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            lines.append(
                "\t".join(
                    (self.table.item(row, c).text() if self.table.item(row, c) else "")
                    for c in range(self.table.columnCount())
                )
            )

        QGuiApplication.clipboard().setText("\n".join(lines))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Blueprint Text Toolkit")
        self.resize(1300, 800)

        self.report: BlueprintReport | None = None
        self.settings = QSettings("BlueprintConverter", "BlueprintConverter")
        self.language = self.settings.value("language", "tr", type=str)
        if self.language not in ("tr", "en"):
            self.language = "tr"

        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)

        # --- Sol: girdi ------------------------------------------------------
        self.input_text = QPlainTextEdit()
        self.input_text.setFont(mono)
        self.input_text.setPlaceholderText(
            "Unreal Engine'den kopyaladığın Blueprint metnini buraya yapıştır\n"
            "(Begin Object ... ile başlayan metin)."
        )

        self.parse_button = QPushButton("Blueprint'i Ayrıştır")
        self.parse_button.clicked.connect(self.parse_blueprint)

        self.paste_button = QPushButton()
        paste_button = self.paste_button
        paste_button.clicked.connect(self.paste_from_clipboard)

        self.clear_button = QPushButton()
        clear_button = self.clear_button
        clear_button.clicked.connect(self.clear_all)

        buttons = QHBoxLayout()
        buttons.addWidget(self.parse_button, 2)
        buttons.addWidget(paste_button)
        buttons.addWidget(clear_button)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.input_label = QLabel()
        left_layout.addWidget(self.input_label)
        left_layout.addWidget(self.input_text, 1)
        left_layout.addLayout(buttons)

        # --- Sağ: sekmeler ---------------------------------------------------
        self.output_mode = QComboBox()
        for mode, title in OUTPUT_MODES:
            self.output_mode.addItem(title, mode)
        self.output_mode.currentIndexChanged.connect(self.refresh_output)

        self.copy_output_button = QPushButton()
        copy_output_button = self.copy_output_button
        copy_output_button.clicked.connect(self.copy_output)

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(mono)
        self.output_text.setPlaceholderText(
            tr("output_hint", self.language)
        )

        output_top = QHBoxLayout()
        self.output_format_label = QLabel()
        output_top.addWidget(self.output_format_label)
        output_top.addWidget(self.output_mode, 1)
        output_top.addWidget(copy_output_button)

        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)
        output_layout.addLayout(output_top)
        output_layout.addWidget(self.output_text, 1)

        self.show_hidden = QCheckBox()
        self.show_hidden.toggled.connect(self.refresh_pins)

        self.nodes_panel = TablePanel(NODE_HEADERS)
        self.pins_panel = TablePanel(PIN_HEADERS, self.show_hidden)
        self.links_panel = TablePanel(LINK_HEADERS)

        self.tabs = QTabWidget()
        self.tabs.addTab(output_tab, "")
        self.tabs.addTab(self.nodes_panel, "")
        self.tabs.addTab(self.pins_panel, "")
        self.tabs.addTab(self.links_panel, "")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        self.status_label = QLabel()

        central = QWidget()
        central_layout = QVBoxLayout(central)
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.addItem("Türkçe", "tr")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex(0 if self.language == "tr" else 1)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        language_row = QHBoxLayout()
        language_row.addStretch(1)
        language_row.addWidget(self.language_label)
        language_row.addWidget(self.language_combo)
        central_layout.addLayout(language_row)
        central_layout.addWidget(splitter, 1)
        central_layout.addWidget(self.status_label)
        self.setCentralWidget(central)
        self.apply_language()

    def change_language(self):
        self.language = self.language_combo.currentData()
        self.settings.setValue("language", self.language)
        self.apply_language()
        if self.report is not None:
            self.refresh_output()
            self.nodes_panel.set_rows(node_rows(self.report))
            self.links_panel.set_rows(link_rows(self.report))
            self.refresh_pins()

    def apply_language(self):
        lang = self.language
        self.language_label.setText(tr("language", lang) + ":")
        self.input_label.setText(tr("input", lang))
        self.input_text.setPlaceholderText(tr("paste_hint", lang))
        self.parse_button.setText(tr("parse", lang))
        self.paste_button.setText(tr("paste", lang))
        self.clear_button.setText(tr("clear", lang))
        self.output_format_label.setText(tr("output_format", lang))
        self.copy_output_button.setText(tr("copy_output", lang))
        self.output_text.setPlaceholderText(tr("output_hint", lang))
        self.show_hidden.setText(tr("show_hidden", lang))
        for panel in (self.nodes_panel, self.pins_panel, self.links_panel):
            panel.set_language(lang)
        for index, key in enumerate(("output", "nodes", "pins", "links")):
            self.tabs.setTabText(index, tr(key, lang))
        mode_titles = {"short": "short", "medium": "medium", "long": "long"}
        for index in range(self.output_mode.count()):
            mode = self.output_mode.itemData(index)
            self.output_mode.setItemText(index, tr(mode_titles[mode], lang))
        if self.report is None:
            self.status_label.setText(tr("not_parsed", lang))

    # -- olaylar -----------------------------------------------------------
    def paste_from_clipboard(self):
        self.input_text.setPlainText(QGuiApplication.clipboard().text())

    def clear_all(self):
        self.input_text.clear()
        self.output_text.clear()
        self.report = None
        for panel in (self.nodes_panel, self.pins_panel, self.links_panel):
            panel.set_rows([])
        self.status_label.setText(tr("not_parsed", self.language))

    def parse_blueprint(self):
        raw_text = self.input_text.toPlainText().strip()

        if not raw_text:
            QMessageBox.warning(
                self, tr("empty_title", self.language), tr("empty_message", self.language)
            )
            return

        try:
            parsed = parse_blueprint_text(raw_text)
            observe_nodes(parsed["nodes"])  # node kütüphanesini öğrenmeye devam eder
            self.report = build_report(raw_text)
        except Exception as error:  # noqa: BLE001 - kullanıcıya göster
            QMessageBox.critical(
                self,
                tr("parse_error", self.language),
                f"{type(error).__name__}: {error}",
            )
            return

        if not self.report.nodes:
            QMessageBox.information(
                self,
                tr("not_found_title", self.language),
                tr("not_found_message", self.language),
            )

        self.nodes_panel.set_rows(node_rows(self.report))
        self.links_panel.set_rows(link_rows(self.report))
        self.refresh_pins()
        self.refresh_output()

        self.status_label.setText(
            f"{self.report.function_name or '(unnamed)' if self.language == 'en' else self.report.function_name or '(adsız)'} · "
            f"{len(self.report.nodes)} node · {self.report.pin_count} pin · "
            f"{len(self.report.links)} bağlantı · "
            f"{len(self.report.issues)} sorun"
        )

    def refresh_pins(self):
        if self.report is not None:
            self.pins_panel.set_rows(
                pin_rows(self.report, self.show_hidden.isChecked())
            )

    def refresh_output(self):
        if self.report is None:
            return
        self.output_text.setPlainText(
            build_output(self.report, self.output_mode.currentData(), self.language)
        )

    def copy_output(self):
        QGuiApplication.clipboard().setText(self.output_text.toPlainText())
        self.status_label.setText(tr("copied", self.language))
def main():
    app = QApplication(sys.argv)

    app.setOrganizationName("BlueprintTextToolkit")
    app.setApplicationName("BlueprintTextToolkit")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
if __name__ == "__main__":
    main()