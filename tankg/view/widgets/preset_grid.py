"""
Matriz de Presets (9 Bancos x 4 Slots = 36 Presets) e Barra de Gravação na EEPROM.
"""

from typing import Dict, Union
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QFrame, QComboBox, QMessageBox
)

from ...model.preset import Preset, list_all_presets, parse_preset_name, get_preset_name


class PresetGrid(QFrame):
    preset_selected = Signal(int, str)  # (preset_id, preset_name)
    save_requested = Signal(int)        # (target_preset_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("presetGrid")
        self.setStyleSheet("""
            QFrame#presetGrid {
                background-color: #18181b;
                border: 1px solid #27272e;
                border-radius: 8px;
                padding: 6px;
            }
        """)

        self.buttons: Dict[int, QPushButton] = {}
        self._active_preset_id: int = 0

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Barra Superior de Controles de Preset
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        title = QLabel("BANCOS DE PRESETS (36 SLOTS)")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #a1a1aa; letter-spacing: 1px;")
        top_bar.addWidget(title)

        top_bar.addStretch()

        # Seletor de Destino para Gravação
        save_label = QLabel("Gravar em:")
        save_label.setStyleSheet("color: #71717a; font-size: 12px;")
        top_bar.addWidget(save_label)

        self.save_target_combo = QComboBox()
        self.save_target_combo.setFixedWidth(80)
        for p in list_all_presets():
            self.save_target_combo.addItem(p.name, p.id)
        top_bar.addWidget(self.save_target_combo)

        self.save_button = QPushButton("💾 Salvar na EEPROM")
        self.save_button.setObjectName("saveButton")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self._on_save_clicked)
        top_bar.addWidget(self.save_button)

        layout.addLayout(top_bar)

        # Grade de 9 Bancos x 4 Slots
        # Colunas: Banco 1..9, Linhas: Slots A, B, C, D
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)

        for bank in range(1, 10):
            bank_header = QLabel(f"B{bank}")
            bank_header.setAlignment(Qt.AlignCenter)
            bank_header.setStyleSheet("color: #71717a; font-size: 10px; font-weight: bold;")
            grid_layout.addWidget(bank_header, 0, bank - 1)

            for slot_idx, slot_char in enumerate("ABCD"):
                pid = (bank - 1) * 4 + slot_idx
                pname = f"{bank}{slot_char}"
                btn = QPushButton(slot_char)
                btn.setFixedSize(36, 26)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setToolTip(f"Preset [{pname}] (#{pid + 1})")
                btn.clicked.connect(lambda checked=False, p_id=pid, p_name=pname: self._on_preset_btn_clicked(p_id, p_name))
                self.buttons[pid] = btn
                grid_layout.addWidget(btn, slot_idx + 1, bank - 1)

        layout.addLayout(grid_layout)
        self._update_button_styles()

    def _on_preset_btn_clicked(self, pid: int, pname: str):
        self.setActivePreset(pid)
        self.preset_selected.emit(pid, pname)

    def _on_save_clicked(self):
        target_pid = self.save_target_combo.currentData()
        target_name = get_preset_name(target_pid)
        
        reply = QMessageBox.question(
            self,
            "Confirmar Gravação EEPROM",
            f"Deseja gravar a configuração atual na memória flash do Preset [{target_name}]?\n\n"
            "Isso sobrescreverá as definições gravadas no hardware.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.save_requested.emit(target_pid)

    def setActivePreset(self, preset: Union[str, int]):
        if isinstance(preset, str):
            pid = parse_preset_name(preset)
        else:
            pid = int(preset)

        if 0 <= pid <= 35:
            self._active_preset_id = pid
            self.save_target_combo.setCurrentIndex(pid)
            self._update_button_styles()

    def _update_button_styles(self):
        for pid, btn in self.buttons.items():
            if pid == self._active_preset_id:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #84cc16;
                        color: #121214;
                        border: 1px solid #65a30d;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #202024;
                        color: #d4d4d8;
                        border: 1px solid #2e2e36;
                        border-radius: 4px;
                        font-weight: 500;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #2e2e38;
                        border-color: #52525e;
                        color: #ffffff;
                    }
                """)
