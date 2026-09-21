"""
Definições visuais, paleta de cores e QSS para a Tank-G.
Design dark moderno de alta qualidade no estilo de plugins de áudio e modeladores de amplificador.
"""

COLORS = {
    "bg_main": "#121214",
    "bg_surface": "#18181b",
    "bg_card": "#202024",
    "bg_card_hover": "#27272e",
    "border": "#2e2e36",
    "border_focus": "#52525e",
    "text_primary": "#f4f4f5",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    
    # Destaques dos Módulos
    "amp": "#f59e0b",       # Dourado vintage
    "mod": "#a855f7",       # Roxo elétrico
    "dly": "#06b6d4",       # Ciano digital
    "rev": "#10b981",       # Esmeralda
    "gate": "#38bdf8",      # Azul céu
    "cab": "#f97316",       # Laranja
    
    # Status
    "success": "#22c55e",
    "danger": "#ef4444",
    "warning": "#eab308",
    "active_preset": "#84cc16",
}

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #121214;
    color: #f4f4f5;
    font-family: 'Segoe UI', 'Inter', 'SF Pro Text', sans-serif;
}

QWidget {
    color: #f4f4f5;
    font-size: 13px;
}

QToolTip {
    background-color: #27272e;
    color: #f4f4f5;
    border: 1px solid #3f3f46;
    padding: 4px 8px;
    border-radius: 4px;
}

/* Scrollbars modernos */
QScrollBar:vertical {
    border: none;
    background: #18181b;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3f3f46;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #52525b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Botões */
QPushButton {
    background-color: #27272e;
    color: #f4f4f5;
    border: 1px solid #3e3e48;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #32323a;
    border-color: #52525e;
}
QPushButton:pressed {
    background-color: #1a1a1e;
}
QPushButton:disabled {
    background-color: #18181b;
    color: #52525b;
    border-color: #27272e;
}

/* Botão Primário / Destaque */
QPushButton#primaryButton {
    background-color: #f59e0b;
    color: #121214;
    border: 1px solid #d97706;
    font-weight: bold;
}
QPushButton#primaryButton:hover {
    background-color: #fbbf24;
}

/* Botão de Salvar EEPROM */
QPushButton#saveButton {
    background-color: #10b981;
    color: #121214;
    border: 1px solid #059669;
    font-weight: bold;
}
QPushButton#saveButton:hover {
    background-color: #34d399;
}

/* ComboBox */
QComboBox {
    background-color: #202024;
    color: #f4f4f5;
    border: 1px solid #32323a;
    border-radius: 6px;
    padding: 5px 12px;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #52525e;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #202024;
    color: #f4f4f5;
    selection-background-color: #3f3f46;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    outline: none;
}

/* Sliders estilizados */
QSlider::groove:horizontal {
    height: 6px;
    background: #27272e;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #f59e0b;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #f4f4f5;
    border: 2px solid #f59e0b;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
    border-color: #fbbf24;
    width: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 9px;
}

/* Status Bar */
QStatusBar {
    background-color: #18181b;
    color: #a1a1aa;
    border-top: 1px solid #27272e;
    font-size: 12px;
}
"""
