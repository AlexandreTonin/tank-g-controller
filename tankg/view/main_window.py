"""
Janela principal (MainWindow) da aplicação Tank-G Controller em PySide6.
Conecta os componentes visuais ao ControlViewModel através de data binding reativo.
"""

from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QStatusBar, QScrollArea, QFrame
)
from PySide6.QtGui import QIcon, QFont, QColor

from ..viewmodel.control_viewmodel import ControlViewModel
from ..model.pedal_state import PedalState
from ..core.constants import AMP_NAMES, CAB_NAMES
from .theme import COLORS, MAIN_STYLESHEET
from .widgets.rotary_knob import RotaryKnob
from .widgets.footswitch import Footswitch
from .widgets.module_card import ModuleCard
from .widgets.preset_grid import PresetGrid


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: ControlViewModel, parent=None):
        super().__init__(parent)
        self.vm = viewmodel

        self.setWindowTitle("Tank-G Controller v2.0 (M-Vave / Cuvave)")
        self.resize(1050, 720)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._updating_ui = False

        self._build_ui()
        self._bind_viewmodel()

        # Atualiza a interface com o estado inicial
        self._on_state_updated(self.vm.state)
        self._refresh_ports()
        
        # Tenta auto-conectar na inicialização
        self.vm.connect_midi()

    def _build_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(16, 12, 16, 12)
        root_layout.setSpacing(12)

        # 1. Top Header Bar (Título, Preset Ativo, Porta MIDI, Conectar)
        root_layout.addLayout(self._build_header())

        # 2. Área Central de Efeitos (Scrollable para caber confortavelmente em qualquer tela)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        scroll_content = QWidget()
        self.modules_layout = QVBoxLayout(scroll_content)
        self.modules_layout.setContentsMargins(0, 4, 0, 4)
        self.modules_layout.setSpacing(12)

        # Linha 1 de Módulos: GATE / CAB e PREAMP / AMP
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(12)
        row1_layout.addWidget(self._build_gate_cab_card(), 1)
        row1_layout.addWidget(self._build_amp_card(), 3)
        self.modules_layout.addLayout(row1_layout)

        # Linha 2 de Módulos: MODULATION, DELAY e REVERB
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(12)
        row2_layout.addWidget(self._build_mod_card(), 1)
        row2_layout.addWidget(self._build_dly_card(), 1)
        row2_layout.addWidget(self._build_rev_card(), 1)
        self.modules_layout.addLayout(row2_layout)

        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll, 1)

        # 3. Barra Inferior: Matriz de Presets (36 Slots) e EEPROM Save
        self.preset_grid = PresetGrid(self)
        root_layout.addWidget(self.preset_grid)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto. Conecte a pedaleira via cabo USB para iniciar.")

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(12)

        # Logo / Título
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        app_title = QLabel("TANK-G CONTROLLER")
        app_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #f4f4f5; letter-spacing: 1.5px;")
        app_subtitle = QLabel("M-Vave SysEx MVVM Workstation")
        app_subtitle.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 600;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_subtitle)
        header.addLayout(title_box)

        header.addSpacing(20)

        # Badge do Preset Ativo
        preset_badge_box = QHBoxLayout()
        preset_badge_box.setSpacing(6)
        preset_lbl = QLabel("PRESET:")
        preset_lbl.setStyleSheet("font-size: 11px; color: #a1a1aa; font-weight: bold;")
        self.active_preset_badge = QLabel("1A")
        self.active_preset_badge.setStyleSheet("""
            QLabel {
                background-color: #84cc16;
                color: #121214;
                font-size: 16px;
                font-weight: 900;
                padding: 4px 12px;
                border-radius: 6px;
                min-width: 38px;
                qproperty-alignment: AlignCenter;
            }
        """)
        preset_badge_box.addWidget(preset_lbl)
        preset_badge_box.addWidget(self.active_preset_badge)
        header.addLayout(preset_badge_box)

        header.addStretch()

        # Seletor de Porta MIDI
        port_label = QLabel("Porta MIDI:")
        port_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        header.addWidget(port_label)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(180)
        header.addWidget(self.port_combo)

        self.refresh_ports_btn = QPushButton("🔄")
        self.refresh_ports_btn.setToolTip("Atualizar lista de portas MIDI")
        self.refresh_ports_btn.setFixedWidth(36)
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        header.addWidget(self.refresh_ports_btn)

        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.setObjectName("primaryButton")
        self.connect_btn.clicked.connect(self._on_toggle_connect)
        header.addWidget(self.connect_btn)

        return header

    # --- Módulo: Gate & Cab ---
    def _build_gate_cab_card(self) -> ModuleCard:
        card = ModuleCard(title="UTILITIES (GATE / CAB)", accent_color=COLORS["cab"], has_bypass=False, parent=self)

        content = QHBoxLayout()
        content.setSpacing(14)

        # Knob Noise Gate
        self.knob_gate = RotaryKnob(title="GATE", min_val=0, max_val=100, default_val=0, accent_color=COLORS["gate"])
        self.knob_gate.valueChanged.connect(lambda v: self.vm.set_gate(v) if not self._updating_ui else None)
        content.addWidget(self.knob_gate, alignment=Qt.AlignCenter)

        # Seletor IR Cab
        cab_box = QVBoxLayout()
        cab_box.setSpacing(4)
        cab_lbl = QLabel("IR CAB")
        cab_lbl.setStyleSheet("color: #a1a1aa; font-size: 10px; font-weight: bold;")
        cab_box.addWidget(cab_lbl)

        self.cab_combo = QComboBox()
        for slot, name in CAB_NAMES.items():
            self.cab_combo.addItem(f"[{slot}] {name}", slot)
        self.cab_combo.currentIndexChanged.connect(
            lambda idx: self.vm.set_cab(self.cab_combo.currentData()) if not self._updating_ui else None
        )
        cab_box.addWidget(self.cab_combo)
        cab_box.addStretch()

        content.addLayout(cab_box, 1)
        card.add_layout(content)
        return card

    # --- Módulo: Preamp / Amp ---
    def _build_amp_card(self) -> ModuleCard:
        card = ModuleCard(title="PREAMP & AMPLIFIER", accent_color=COLORS["amp"], has_bypass=True, parent=self)
        self.footswitch_amp = card.footswitch
        self.footswitch_amp.toggled.connect(lambda on: self.vm.set_module_bypass("amp", on) if not self._updating_ui else None)

        # Seletor de Modelo de Amp
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        model_lbl = QLabel("MODEL:")
        model_lbl.setStyleSheet("color: #a1a1aa; font-size: 10px; font-weight: bold;")
        top_row.addWidget(model_lbl)

        self.amp_type_combo = QComboBox()
        for tid, name in AMP_NAMES.items():
            self.amp_type_combo.addItem(f"[{tid}] {name}", tid)
        self.amp_type_combo.currentIndexChanged.connect(
            lambda idx: self.vm.set_amp_type(self.amp_type_combo.currentData()) if not self._updating_ui else None
        )
        top_row.addWidget(self.amp_type_combo, 1)
        card.add_layout(top_row)

        # Fileira de Knobs (Gain, Treble, Mid, Bass, Volume)
        knobs_row = QHBoxLayout()
        knobs_row.setSpacing(6)

        self.knob_gain = RotaryKnob("GAIN", 0, 100, 50, accent_color=COLORS["amp"])
        self.knob_treble = RotaryKnob("TREBLE", 0, 100, 50, accent_color=COLORS["amp"])
        self.knob_middle = RotaryKnob("MIDDLE", 0, 100, 50, accent_color=COLORS["amp"])
        self.knob_bass = RotaryKnob("BASS", 0, 100, 50, accent_color=COLORS["amp"])
        self.knob_volume = RotaryKnob("VOLUME", 0, 100, 50, accent_color=COLORS["amp"])

        self.knob_gain.valueChanged.connect(lambda v: self.vm.set_amp_param("gain", v) if not self._updating_ui else None)
        self.knob_treble.valueChanged.connect(lambda v: self.vm.set_amp_param("treble", v) if not self._updating_ui else None)
        self.knob_middle.valueChanged.connect(lambda v: self.vm.set_amp_param("middle", v) if not self._updating_ui else None)
        self.knob_bass.valueChanged.connect(lambda v: self.vm.set_amp_param("bass", v) if not self._updating_ui else None)
        self.knob_volume.valueChanged.connect(lambda v: self.vm.set_amp_param("volume", v) if not self._updating_ui else None)

        knobs_row.addWidget(self.knob_gain)
        knobs_row.addWidget(self.knob_treble)
        knobs_row.addWidget(self.knob_middle)
        knobs_row.addWidget(self.knob_bass)
        knobs_row.addWidget(self.knob_volume)

        card.add_layout(knobs_row)
        return card

    # --- Módulo: Modulation ---
    def _build_mod_card(self) -> ModuleCard:
        card = ModuleCard(title="MODULATION", accent_color=COLORS["mod"], has_bypass=True, parent=self)
        self.footswitch_mod = card.footswitch
        self.footswitch_mod.toggled.connect(lambda on: self.vm.set_module_bypass("mod", on) if not self._updating_ui else None)

        # Seletor de Tipo (Chorus, Phaser, Tremolo)
        self.mod_type_combo = QComboBox()
        self.mod_type_combo.addItem("Chorus", "chorus")
        self.mod_type_combo.addItem("Phaser", "phaser")
        self.mod_type_combo.addItem("Tremolo", "tremolo")
        self.mod_type_combo.currentIndexChanged.connect(self._on_mod_type_changed)
        card.add_widget(self.mod_type_combo)

        # Knobs de Modulação
        knobs_row = QHBoxLayout()
        knobs_row.setSpacing(6)

        self.knob_mod_val = RotaryKnob("MIX/DEPTH", 1, 40, 20, unit="/40", accent_color=COLORS["mod"])
        self.knob_mod_speed = RotaryKnob("SPEED", 0, 100, 50, accent_color=COLORS["mod"])

        self.knob_mod_val.valueChanged.connect(
            lambda v: self.vm.set_mod_effect(self.mod_type_combo.currentData(), v) if not self._updating_ui else None
        )
        self.knob_mod_speed.valueChanged.connect(
            lambda v: self.vm.set_mod_speed(v) if not self._updating_ui else None
        )

        knobs_row.addWidget(self.knob_mod_val)
        knobs_row.addWidget(self.knob_mod_speed)
        card.add_layout(knobs_row)
        return card

    def _on_mod_type_changed(self):
        if not self._updating_ui:
            mtype = self.mod_type_combo.currentData()
            self.vm.set_mod_effect(mtype, self.knob_mod_val.value)

    # --- Módulo: Delay ---
    def _build_dly_card(self) -> ModuleCard:
        card = ModuleCard(title="DELAY", accent_color=COLORS["dly"], has_bypass=True, parent=self)
        self.footswitch_dly = card.footswitch
        self.footswitch_dly.toggled.connect(lambda on: self.vm.set_module_bypass("dly", on) if not self._updating_ui else None)

        # Seletor de Tipo de Delay
        self.dly_type_combo = QComboBox()
        self.dly_type_combo.addItem("Analog Delay", "analog")
        self.dly_type_combo.addItem("Tape Delay", "tape")
        self.dly_type_combo.addItem("Dual Delay", "dual")
        self.dly_type_combo.currentIndexChanged.connect(self._on_dly_type_changed)
        card.add_widget(self.dly_type_combo)

        # Knobs de Delay
        knobs_row = QHBoxLayout()
        knobs_row.setSpacing(6)

        self.knob_dly_val = RotaryKnob("MIX", 1, 40, 20, unit="/40", accent_color=COLORS["dly"])
        self.knob_dly_time = RotaryKnob("TIME", 0, 100, 50, accent_color=COLORS["dly"])

        self.knob_dly_val.valueChanged.connect(
            lambda v: self.vm.set_delay_effect(self.dly_type_combo.currentData(), v) if not self._updating_ui else None
        )
        self.knob_dly_time.valueChanged.connect(
            lambda v: self.vm.set_delay_time(v) if not self._updating_ui else None
        )

        knobs_row.addWidget(self.knob_dly_val)
        knobs_row.addWidget(self.knob_dly_time)
        card.add_layout(knobs_row)
        return card

    def _on_dly_type_changed(self):
        if not self._updating_ui:
            dtype = self.dly_type_combo.currentData()
            self.vm.set_delay_effect(dtype, self.knob_dly_val.value)

    # --- Módulo: Reverb ---
    def _build_rev_card(self) -> ModuleCard:
        card = ModuleCard(title="REVERB", accent_color=COLORS["rev"], has_bypass=True, parent=self)
        self.footswitch_rev = card.footswitch
        self.footswitch_rev.toggled.connect(lambda on: self.vm.set_module_bypass("rev", on) if not self._updating_ui else None)

        # Seletor de Tipo de Reverb
        self.rev_type_combo = QComboBox()
        self.rev_type_combo.addItem("Room Reverb", "room")
        self.rev_type_combo.addItem("Spring Reverb", "spring")
        self.rev_type_combo.addItem("Cloud Reverb", "cloud")
        self.rev_type_combo.currentIndexChanged.connect(self._on_rev_type_changed)
        card.add_widget(self.rev_type_combo)

        # Knobs de Reverb
        knobs_row = QHBoxLayout()
        knobs_row.setSpacing(6)

        self.knob_rev_val = RotaryKnob("DECAY", 1, 40, 20, unit="/40", accent_color=COLORS["rev"])
        self.knob_rev_mix = RotaryKnob("MIX", 0, 100, 50, accent_color=COLORS["rev"])

        self.knob_rev_val.valueChanged.connect(
            lambda v: self.vm.set_reverb_effect(self.rev_type_combo.currentData(), v) if not self._updating_ui else None
        )
        self.knob_rev_mix.valueChanged.connect(
            lambda v: self.vm.set_reverb_mix(v) if not self._updating_ui else None
        )

        knobs_row.addWidget(self.knob_rev_val)
        knobs_row.addWidget(self.knob_rev_mix)
        card.add_layout(knobs_row)
        return card

    def _on_rev_type_changed(self):
        if not self._updating_ui:
            rtype = self.rev_type_combo.currentData()
            self.vm.set_reverb_effect(rtype, self.knob_rev_val.value)

    # --- Conexões com o ViewModel ---
    def _bind_viewmodel(self):
        self.vm.state_updated.connect(self._on_state_updated)
        self.vm.preset_switched.connect(self._on_preset_switched)
        self.vm.connection_status_changed.connect(self._on_connection_changed)
        self.vm.notification.connect(self._on_notification)
        self.vm.sysex_activity.connect(self._on_sysex_activity)

        # Grid de Presets
        self.preset_grid.preset_selected.connect(self.vm.switch_preset)
        self.preset_grid.save_requested.connect(self.vm.save_current_preset)

    # --- Handlers de Atualização de UI ---
    def _on_state_updated(self, state: PedalState):
        self._updating_ui = True
        try:
            # Preset
            self.active_preset_badge.setText(state.preset)
            self.preset_grid.setActivePreset(state.preset)

            # Utilities (Gate & Cab)
            self.knob_gate.setValue(state.gate)
            cab_idx = self.cab_combo.findData(state.cab)
            if cab_idx != -1:
                self.cab_combo.setCurrentIndex(cab_idx)

            # Preamp / Amp
            self.footswitch_amp.setActive(bool(state.amp_on))
            amp_idx = self.amp_type_combo.findData(state.type)
            if amp_idx != -1:
                self.amp_type_combo.setCurrentIndex(amp_idx)
            self.knob_gain.setValue(state.gain)
            self.knob_treble.setValue(state.treble)
            self.knob_middle.setValue(state.middle)
            self.knob_bass.setValue(state.bass)
            self.knob_volume.setValue(state.volume)

            # Modulation
            self.footswitch_mod.setActive(bool(state.mod_on))
            mtype, mval = state.mod_info
            mod_idx = self.mod_type_combo.findData(mtype)
            if mod_idx != -1:
                self.mod_type_combo.setCurrentIndex(mod_idx)
            self.knob_mod_val.setValue(mval)
            self.knob_mod_speed.setValue(state.mod_speed)

            # Delay
            self.footswitch_dly.setActive(bool(state.dly_on))
            dtype, dval = state.dly_info
            dly_idx = self.dly_type_combo.findData(dtype)
            if dly_idx != -1:
                self.dly_type_combo.setCurrentIndex(dly_idx)
            self.knob_dly_val.setValue(dval)
            self.knob_dly_time.setValue(state.dly_time)

            # Reverb
            self.footswitch_rev.setActive(bool(state.rev_on))
            rtype, rval = state.rev_info
            rev_idx = self.rev_type_combo.findData(rtype)
            if rev_idx != -1:
                self.rev_type_combo.setCurrentIndex(rev_idx)
            self.knob_rev_val.setValue(rval)
            self.knob_rev_mix.setValue(state.rev_mix)

        finally:
            self._updating_ui = False

    def _on_preset_switched(self, pid: int, pname: str):
        self.active_preset_badge.setText(pname)
        self.preset_grid.setActivePreset(pname)

    def _on_connection_changed(self, connected: bool, desc: str):
        if connected:
            self.connect_btn.setText("Desconectar")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27272e;
                    color: #ef4444;
                    border: 1px solid #7f1d1d;
                }
                QPushButton:hover {
                    background-color: #3f1d24;
                }
            """)
            self.status_bar.showMessage(f"🟢 Conectado: {desc}")
        else:
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("")
            self.status_bar.showMessage(f"⚪ {desc}")

    def _on_notification(self, text: str, level: str):
        icon = "🟢 " if level == "success" else ("🔴 " if level == "error" else ("🟡 " if level == "warning" else "ℹ️ "))
        self.status_bar.showMessage(f"{icon}{text}", 5000)

    def _on_sysex_activity(self, direction: str, data: list):
        hex_str = " ".join(f"{b:02X}" for b in data[:12])
        if len(data) > 12:
            hex_str += f" ... ({len(data)} bytes)"
        self.status_bar.showMessage(f"[{direction}] {hex_str}", 2500)

    # --- Controle de Portas MIDI ---
    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = self.vm.get_available_ports()
        for p in ports:
            self.port_combo.addItem(p)

        idx = self.port_combo.findText(current)
        if idx != -1:
            self.port_combo.setCurrentIndex(idx)
        elif self.port_combo.count() > 0:
            # Seleciona porta preferida
            pref = self.vm.midi.find_tankg_port()
            if pref:
                pidx = self.port_combo.findText(pref)
                if pidx != -1:
                    self.port_combo.setCurrentIndex(pidx)

    def _on_toggle_connect(self):
        if self.vm.is_connected:
            self.vm.disconnect_midi()
        else:
            selected_port = self.port_combo.currentText()
            self.vm.connect_midi(selected_port if selected_port else None)
