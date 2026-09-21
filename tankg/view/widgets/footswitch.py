"""
Botão estilo footswitch com anel metálico e LED indicador de status (ON / BYPASS).
"""

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPaintEvent, QMouseEvent
from PySide6.QtWidgets import QWidget


class Footswitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, label: str = "BYPASS", is_active: bool = True, parent=None):
        super().__init__(parent)
        self.label = label
        self._is_active = is_active
        self._is_pressed = False

        self.setFixedSize(64, 76)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    @property
    def is_active(self) -> bool:
        return self._is_active

    def setActive(self, active: bool, emit_signal: bool = False):
        if self._is_active != active:
            self._is_active = active
            self.update()
            if emit_signal:
                self.toggled.emit(self._is_active)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._is_pressed:
            self._is_pressed = False
            self._is_active = not self._is_active
            self.update()
            self.toggled.emit(self._is_active)
            event.accept()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0

        # 1. LED Indicador no topo
        led_y = 12.0
        led_radius = 5.0
        led_rect = QRectF(cx - led_radius, led_y - led_radius, led_radius * 2, led_radius * 2)

        if self._is_active:
            led_color = QColor("#22c55e")      # Verde brilhante
            glow_color = QColor(34, 197, 94, 70)
        else:
            led_color = QColor("#52525b")      # Apagado / neutro
            glow_color = QColor(0, 0, 0, 0)

        # Efeito de brilho do LED
        if self._is_active:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(led_rect.adjusted(-3, -3, 3, 3))

        painter.setPen(QPen(QColor("#18181b"), 1.0))
        painter.setBrush(QBrush(led_color))
        painter.drawEllipse(led_rect)

        # 2. Botão Footswitch Metálico
        switch_cy = 38.0
        switch_r = 17.0 if not self._is_pressed else 16.0
        switch_rect = QRectF(cx - switch_r, switch_cy - switch_r, switch_r * 2, switch_r * 2)

        # Anel externo prateado
        outer_pen = QPen(QColor("#52525e") if not self._is_pressed else QColor("#3f3f46"), 2.0)
        painter.setPen(outer_pen)
        painter.setBrush(QBrush(QColor("#27272e")))
        painter.drawEllipse(switch_rect)

        # Miolo metálico
        inner_r = switch_r - 4.5
        inner_rect = QRectF(cx - inner_r, switch_cy - inner_r, inner_r * 2, inner_r * 2)
        painter.setPen(QPen(QColor("#71717a"), 1.0))
        painter.setBrush(QBrush(QColor("#383842") if not self._is_pressed else QColor("#1e1e24")))
        painter.drawEllipse(inner_rect)

        # 3. Rótulo inferior
        status_text = "ON" if self._is_active else "OFF"
        status_color = QColor("#22c55e") if self._is_active else QColor("#71717a")

        painter.setPen(status_color)
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, h - 16, w, 14), Qt.AlignCenter, status_text)
