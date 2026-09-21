"""
Knob rotativo customizado para controle de áudio estilo pedal/amp.
Renderizado em vetor com QPainter, suporta drag vertical, roda do mouse e duplo clique para reset.
"""

import math
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPaintEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QWidget


class RotaryKnob(QWidget):
    valueChanged = Signal(int)

    def __init__(
        self,
        title: str = "PARAM",
        min_val: int = 0,
        max_val: int = 100,
        default_val: int = 50,
        unit: str = "",
        accent_color: str = "#f59e0b",
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.default_val = default_val
        self.unit = unit
        self.accent_color = QColor(accent_color)
        
        self._value = default_val
        self._last_mouse_pos = None

        self.setFixedSize(70, 95)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    @property
    def value(self) -> int:
        return self._value

    def setValue(self, val: int, emit_signal: bool = False):
        clamped = max(self.min_val, min(self.max_val, int(val)))
        if self._value != clamped:
            self._value = clamped
            self.update()
            if emit_signal:
                self.valueChanged.emit(self._value)

    def setAccentColor(self, hex_color: str):
        self.accent_color = QColor(hex_color)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._last_mouse_pos = event.pos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._last_mouse_pos is not None:
            dy = self._last_mouse_pos.y() - event.pos().y()
            self._last_mouse_pos = event.pos()
            
            # Sensibilidade: arrastar ~150px percorre a faixa completa
            delta_range = self.max_val - self.min_val
            step = (dy / 150.0) * delta_range
            new_val = self._value + step
            self.setValue(int(round(new_val)), emit_signal=True)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._last_mouse_pos = None
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.setValue(self.default_val, emit_signal=True)
            event.accept()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        step = 1 if delta > 0 else -1
        self.setValue(self._value + step, emit_signal=True)
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Right):
            self.setValue(self._value + 1, emit_signal=True)
            event.accept()
        elif event.key() in (Qt.Key_Down, Qt.Key_Left):
            self.setValue(self._value - 1, emit_signal=True)
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Rótulo superior (Título)
        painter.setPen(QColor("#a1a1aa"))
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 2, w, 14), Qt.AlignCenter, self.title)

        # 2. Desenho do Knob
        knob_size = 46
        cx = w / 2.0
        cy = 40.0
        radius = knob_size / 2.0
        knob_rect = QRectF(cx - radius, cy - radius, knob_size, knob_size)

        # Trilha de fundo (arco de 240 graus, de 150° a 390° / -30°)
        start_angle = 210  # em graus Qt (1/16 de grau)
        total_span = -240

        pen_track = QPen(QColor("#27272e"), 3.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_track)
        painter.drawArc(knob_rect.adjusted(-2, -2, 2, 2), int(start_angle * 16), int(total_span * 16))

        # Arco ativo em cor de destaque
        norm = 0.0
        if self.max_val > self.min_val:
            norm = (self._value - self.min_val) / (self.max_val - self.min_val)
        norm = max(0.0, min(1.0, norm))

        active_span = total_span * norm
        pen_active = QPen(self.accent_color, 3.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_active)
        painter.drawArc(knob_rect.adjusted(-2, -2, 2, 2), int(start_angle * 16), int(active_span * 16))

        # Corpo do botão metálico/chumbo
        painter.setPen(QPen(QColor("#3f3f46"), 1.5))
        painter.setBrush(QBrush(QColor("#1e1e24")))
        painter.drawEllipse(knob_rect)

        # Indicador de ponteiro (Needle)
        # Ângulo matemático em radianos
        angle_deg = 150 - (240 * norm)
        angle_rad = math.radians(angle_deg)
        inner_r = radius * 0.35
        outer_r = radius * 0.85

        p1 = QPointF(cx + inner_r * math.cos(angle_rad), cy - inner_r * math.sin(angle_rad))
        p2 = QPointF(cx + outer_r * math.cos(angle_rad), cy - outer_r * math.sin(angle_rad))

        pen_needle = QPen(QColor("#ffffff"), 2.2, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_needle)
        painter.drawLine(p1, p2)

        # 3. Leitura numérica inferior
        val_text = f"{self._value}{self.unit}"
        painter.setPen(QColor("#f4f4f5"))
        val_font = QFont("Segoe UI", 9, QFont.Medium)
        painter.setFont(val_font)
        painter.drawText(QRectF(0, h - 22, w, 18), Qt.AlignCenter, val_text)
