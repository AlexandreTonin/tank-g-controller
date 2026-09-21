"""
Painel de Criação de Timbres por Inteligência Artificial (Gemini AI Tone Crafter).
Permite inserir prompts em linguagem natural, testar presets em tempo real e salvar em slots.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox, QInputDialog, QWidget
)
from PySide6.QtGui import QFont, QColor

from ...model.pedal_state import PedalState
from ...model.preset import list_all_presets, get_preset_name
from ...services.gemini_preset_service import get_active_api_key, save_api_key


class AITonePanel(QFrame):
    generate_requested = Signal(str)            # (prompt)
    preview_requested = Signal(object)          # (PedalState)
    save_requested = Signal(object, int)        # (PedalState, target_slot_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aiTonePanel")
        self.setStyleSheet("""
            QFrame#aiTonePanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a162b, stop:1 #1e1b2e);
                border: 1px solid #4c1d95;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        self._current_ai_state: Optional[PedalState] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 1. Cabeçalho
        header = QHBoxLayout()
        header.setSpacing(8)

        title_icon = QLabel("✨")
        title_icon.setStyleSheet("font-size: 16px;")
        header.addWidget(title_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_lbl = QLabel("GEMINI AI TONE CRAFTER")
        title_lbl.setStyleSheet("color: #c084fc; font-weight: 800; font-size: 13px; letter-spacing: 1px;")
        subtitle_lbl = QLabel("Crie timbres profissionais para a Tank-G usando inteligência artificial")
        subtitle_lbl.setStyleSheet("color: #a855f7; font-size: 11px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header.addLayout(title_box)

        header.addStretch()

        # Botão de Configurar API Key
        self.key_btn = QPushButton("⚙️ API Key")
        self.key_btn.setToolTip("Configurar chave GEMINI_API_KEY do Google AI Studio")
        self.key_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e1065;
                color: #e9d5ff;
                border: 1px solid #6b21a8;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3b0764;
                border-color: #a855f7;
            }
        """)
        self.key_btn.clicked.connect(self._on_configure_key)
        header.addWidget(self.key_btn)

        layout.addLayout(header)

        # 2. Barra de Input e Botão Gerar
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Ex: Timbre do solo de Stairway to Heaven, Dani California do RHCP, Hard Rock anos 80...")
        self.prompt_input.setStyleSheet("""
            QLineEdit {
                background-color: #120e24;
                color: #f5f3ff;
                border: 1px solid #581c87;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #a855f7;
            }
        """)
        self.prompt_input.returnPressed.connect(self._on_generate_clicked)
        input_row.addWidget(self.prompt_input, 1)

        self.generate_btn = QPushButton("✨ Gerar Timbre")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: #ffffff;
                border: 1px solid #6d28d9;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #8b5cf6;
            }
            QPushButton:disabled {
                background-color: #4c1d95;
                color: #a78bfa;
            }
        """)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        input_row.addWidget(self.generate_btn)

        layout.addLayout(input_row)

        # 3. Pílulas de Prompts Rápidos
        pills_row = QHBoxLayout()
        pills_row.setSpacing(6)

        pills = [
            ("🌶️ Dani California", "Timbre do solo de Dani California do Red Hot Chili Peppers"),
            ("🎸 Stairway Solo", "Timbre do solo de Stairway to Heaven do Led Zeppelin"),
            ("⚡ Slash / Hard Rock", "Distorção anos 80 estilo Slash no Marshall JCM800"),
            ("✨ Neo Soul Clean", "Clean aveludado e dinâmico com chorus e reverb espaçoso"),
            ("🔥 Modern Metal 5150", "High gain moderno pesado e definido para metal com noise gate"),
        ]

        pills_lbl = QLabel("Sugestões:")
        pills_lbl.setStyleSheet("color: #9333ea; font-size: 10px; font-weight: bold;")
        pills_row.addWidget(pills_lbl)

        for label, prompt_text in pills:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #241442;
                    color: #d8b4fe;
                    border: 1px solid #4c1d95;
                    border-radius: 10px;
                    padding: 3px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #3b0764;
                    color: #ffffff;
                    border-color: #a855f7;
                }
            """)
            btn.clicked.connect(lambda checked=False, p=prompt_text: self._set_prompt_and_generate(p))
            pills_row.addWidget(btn)

        pills_row.addStretch()
        layout.addLayout(pills_row)

        # 4. Card de Preview do Resultado (inicialmente oculto)
        self.result_card = QFrame()
        self.result_card.setStyleSheet("""
            QFrame {
                background-color: #151129;
                border: 1px solid #3b0764;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.result_card.setVisible(False)

        res_layout = QVBoxLayout(self.result_card)
        res_layout.setContentsMargins(8, 6, 8, 6)
        res_layout.setSpacing(6)

        # Cabeçalho do Resultado
        res_top = QHBoxLayout()
        res_top.setSpacing(8)

        self.preset_badge = QLabel("AI PRESET")
        self.preset_badge.setStyleSheet("""
            QLabel {
                background-color: #a855f7;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 4px;
            }
        """)
        res_top.addWidget(self.preset_badge)

        self.explanation_label = QLabel("")
        self.explanation_label.setWordWrap(True)
        self.explanation_label.setStyleSheet("color: #e9d5ff; font-size: 11px;")
        res_top.addWidget(self.explanation_label, 1)

        res_layout.addLayout(res_top)

        # Botões de Ação do Preset Gerado
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.preview_btn = QPushButton("🔊 Testar no Pedal (Tempo Real)")
        self.preview_btn.setToolTip("Envia os parâmetros imediatamente para você ouvir e tocar sem alterar a memória EEPROM")
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #0369a1;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
            }
        """)
        self.preview_btn.clicked.connect(self._on_preview_clicked)
        action_row.addWidget(self.preview_btn)

        action_row.addStretch()

        slot_lbl = QLabel("Salvar no Slot:")
        slot_lbl.setStyleSheet("color: #a855f7; font-size: 11px;")
        action_row.addWidget(slot_lbl)

        self.slot_combo = QComboBox()
        self.slot_combo.setFixedWidth(80)
        for p in list_all_presets():
            self.slot_combo.addItem(p.name, p.id)
        action_row.addWidget(self.slot_combo)

        self.save_slot_btn = QPushButton("💾 Gravar na EEPROM")
        self.save_slot_btn.setCursor(Qt.PointingHandCursor)
        self.save_slot_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #121214;
                border: 1px solid #059669;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34d399;
            }
        """)
        self.save_slot_btn.clicked.connect(self._on_save_slot_clicked)
        action_row.addWidget(self.save_slot_btn)

        res_layout.addLayout(action_row)
        layout.addWidget(self.result_card)

    def _set_prompt_and_generate(self, prompt: str):
        self.prompt_input.setText(prompt)
        self._on_generate_clicked()

    def _on_generate_clicked(self):
        text = self.prompt_input.text().strip()
        if not text:
            return
        self.set_loading(True)
        self.generate_requested.emit(text)

    def _on_preview_clicked(self):
        if self._current_ai_state:
            self.preview_requested.emit(self._current_ai_state)

    def _on_save_slot_clicked(self):
        if not self._current_ai_state:
            return
        slot_id = self.slot_combo.currentData()
        slot_name = get_preset_name(slot_id)

        reply = QMessageBox.question(
            self,
            "Gravar Preset da IA",
            f"Deseja gravar permanentemente este timbre no Preset [{slot_name}] da pedaleira?\n\n"
            f"Nome: {self.preset_badge.text()}\n"
            "As configurações anteriores do slot serão substituídas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.save_requested.emit(self._current_ai_state, slot_id)

    def _on_configure_key(self):
        current = get_active_api_key() or ""
        key, ok = QInputDialog.getText(
            self,
            "Chave de API do Gemini",
            "Insira sua GEMINI_API_KEY do Google AI Studio:\n(Obtenha gratuitamente em https://aistudio.google.com)",
            QLineEdit.Password if current else QLineEdit.Normal,
            current
        )
        if ok and key.strip():
            save_api_key(key.strip())
            QMessageBox.information(self, "Chave Configurada", "Chave de API salva com sucesso no arquivo local.")

    def set_loading(self, loading: bool):
        if loading:
            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("✨ Gerando...")
        else:
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("✨ Gerar Timbre")

    def show_ai_result(self, state: PedalState, suggestion_name: str, explanation: str):
        self.set_loading(False)
        self._current_ai_state = state
        self.preset_badge.setText(suggestion_name.upper())
        self.explanation_label.setText(explanation)
        self.result_card.setVisible(True)

    def show_error(self, err_msg: str):
        self.set_loading(False)
        QMessageBox.warning(self, "Agente de IA", err_msg)
