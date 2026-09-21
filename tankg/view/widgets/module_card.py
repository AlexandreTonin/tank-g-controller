"""
Painel modular para agrupar controles de cada seção da pedaleira.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtGui import QColor

from .footswitch import Footswitch


class ModuleCard(QFrame):
    def __init__(
        self,
        title: str,
        accent_color: str = "#f59e0b",
        has_bypass: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.accent_color = accent_color
        self.footswitch: Optional[Footswitch] = None

        self.setObjectName("moduleCard")
        self.setStyleSheet(f"""
            QFrame#moduleCard {{
                background-color: #1a1a1e;
                border: 1px solid #2e2e38;
                border-top: 3px solid {accent_color};
                border-radius: 8px;
            }}
        """)

        # Layout Principal do Card
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 10, 12, 12)
        self.main_layout.setSpacing(10)

        # Cabeçalho: Título e Footswitch (se aplicável)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)
        header_layout.addWidget(self.title_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addStretch()

        if has_bypass:
            self.footswitch = Footswitch(parent=self)
            header_layout.addWidget(self.footswitch, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.main_layout.addLayout(header_layout)

        # Área de Conteúdo
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        self.main_layout.addLayout(self.content_layout)

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)
