"""
ViewModel central da Tank-G (ControlViewModel).
Conecta a View (PySide6) ao Model (PedalState) e coordena I/O através do MidiService.
Gerencia debouncing de parâmetros, prevenção de loopbacks e gravação na EEPROM.
"""

from pathlib import Path
from typing import Optional, Union, List

from PySide6.QtCore import QObject, Signal, QTimer, Slot, QThread

from ..model.pedal_state import PedalState
from ..model.preset import parse_preset_name, get_preset_name
from ..services.midi_service import MidiService
from ..services.gemini_preset_service import GeminiPresetService
from ..services.preset_validator import OutOfDomainPromptError
from ..services.sysex_codec import (
    build_gate_sysex,
    build_cab_sysex,
    build_module_bypass_sysex,
    build_preset_switch_sysex,
    build_preset_param_sysex,
    build_eeprom_save_sysex,
    build_eeprom_flush_sysex,
    parse_sysex,
)


class AIGenerationWorker(QThread):
    """Thread em segundo plano para consultar o Gemini sem congelar a UI."""
    preset_ready = Signal(object, str, str)  # (PedalState, name_suggestion, musical_explanation)
    error_occurred = Signal(str)

    def __init__(self, service: GeminiPresetService, prompt: str, api_key: Optional[str] = None):
        super().__init__()
        self.service = service
        self.prompt = prompt
        self.api_key = api_key

    def run(self):
        try:
            state, name, explanation = self.service.generate_preset(self.prompt, self.api_key)
            self.preset_ready.emit(state, name, explanation)
        except OutOfDomainPromptError as e:
            self.error_occurred.emit(f"⚠️ {e.message}")
        except Exception as e:
            self.error_occurred.emit(f"Erro na geração de timbre: {e}")


class ControlViewModel(QObject):
    """
    ViewModel reativo para controle da pedaleira Tank-G.
    """
    # Sinais emitidos para a View
    state_updated = Signal(PedalState)
    preset_switched = Signal(int, str)
    connection_status_changed = Signal(bool, str)
    notification = Signal(str, str)             # (mensagem, tipo: 'info' | 'success' | 'warning' | 'error')
    sysex_activity = Signal(str, list)          # ('SENT' | 'RECV', hex_bytes)

    # Sinais do Agente de IA (Gemini)
    ai_generation_started = Signal()
    ai_preset_ready = Signal(object, str, str)  # (state, suggestion_name, explanation)
    ai_generation_error = Signal(str)

    def __init__(self, midi_service: Optional[MidiService] = None, state_file: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.state_file = state_file or (Path.cwd() / "state.json")
        self.state = PedalState.load_from_file(self.state_file)

        # Serviço MIDI
        self.midi = midi_service or MidiService(self)
        self.midi.connection_changed.connect(self._on_midi_connection_changed)
        self.midi.message_received.connect(self._on_midi_message_received)
        self.midi.message_sent.connect(self._on_midi_message_sent)
        self.midi.error_occurred.connect(self._on_midi_error)

        # Serviço Gemini AI
        self.gemini_service = GeminiPresetService()
        self._ai_worker: Optional[AIGenerationWorker] = None

        # Controle de debounce para envio em tempo real
        self._suppress_midi_send = False
        self._preset_param_dirty = False
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(30)  # 30ms para resposta ágil sem inundar MIDI
        self._debounce_timer.timeout.connect(self._flush_preset_params)

    # --- Properties ---
    @property
    def is_connected(self) -> bool:
        return self.midi.is_connected

    @property
    def current_port(self) -> Optional[str]:
        return self.midi.current_port

    # --- Persistência de Estado ---
    def save_state_to_disk(self):
        self.state.save_to_file(self.state_file)

    # --- Sincronização e Envio ---
    def _schedule_preset_param_update(self):
        """Agenda o envio do pacote consolidado do preset com debounce."""
        self.save_state_to_disk()
        self.state_updated.emit(self.state)

        if self._suppress_midi_send:
            return

        self._preset_param_dirty = True
        if not self._debounce_timer.isActive():
            self._debounce_timer.start()

    def _flush_preset_params(self):
        if self._preset_param_dirty and not self._suppress_midi_send:
            self._preset_param_dirty = False
            sysex = build_preset_param_sysex(self.state)
            self.midi.send_sysex(sysex)

    # --- Handlers do MidiService ---
    def _on_midi_connection_changed(self, connected: bool, port_name: str, error_msg: str):
        desc = f"Conectado: {port_name}" if connected else ("Desconectado" if not error_msg else error_msg)
        self.connection_status_changed.emit(connected, desc)
        if connected:
            self.notification.emit(f"Porta MIDI '{port_name}' pronta para comunicação.", "success")
        elif error_msg:
            self.notification.emit(error_msg, "error")

    def _on_midi_message_received(self, data: List[int]):
        self.sysex_activity.emit("RECV", data)
        parsed = parse_sysex(data)
        if not parsed:
            return

        # Previne envio redundante quando o sinal vem do próprio pedal
        self._suppress_midi_send = True
        try:
            if parsed["type"] == "preset_switch":
                pid = parsed["preset_id"]
                pname = get_preset_name(pid)
                self.state.preset = pname
                self.save_state_to_disk()
                self.preset_switched.emit(pid, pname)
                self.state_updated.emit(self.state)
                self.notification.emit(f"Pedaleira alternou para preset [{pname}]", "info")

            elif parsed["type"] == "module_bypass":
                mod_id = parsed["module_id"]
                st = parsed["state"]
                key_map = {0: "amp_on", 1: "mod_on", 2: "dly_on", 3: "rev_on"}
                if mod_id in key_map:
                    setattr(self.state, key_map[mod_id], 1 if st else 0)
                    self.save_state_to_disk()
                    self.state_updated.emit(self.state)
        finally:
            self._suppress_midi_send = False

    def _on_midi_message_sent(self, data: List[int]):
        self.sysex_activity.emit("SENT", data)

    def _on_midi_error(self, title: str, detail: str):
        self.notification.emit(f"{title}: {detail}", "error")

    # --- Ações de Controle: Amplificador ---
    def set_amp_type(self, type_id: int):
        t = max(1, min(9, int(type_id)))
        if self.state.type != t:
            self.state.type = t
            self._schedule_preset_param_update()

    def set_amp_param(self, name: str, value: int):
        val = max(0, min(100, int(value)))
        field = "middle" if name in ("mid", "middle") else ("volume" if name in ("vol", "volume") else name)
        if hasattr(self.state, field) and getattr(self.state, field) != val:
            setattr(self.state, field, val)
            self._schedule_preset_param_update()

    # --- Ações de Controle: Bypass dos Módulos ---
    def set_module_bypass(self, module_name: str, on: bool):
        field = f"{module_name.lower()}_on"
        st = 1 if on else 0
        if hasattr(self.state, field):
            setattr(self.state, field, st)
            self.save_state_to_disk()
            self.state_updated.emit(self.state)

            if not self._suppress_midi_send:
                sysex = build_module_bypass_sysex(module_name, on)
                self.midi.send_sysex(sysex)

    # --- Ações de Controle: Modulação ---
    def set_mod_effect(self, mod_type: str, level: int):
        self.state.set_mod_effect(mod_type, level)
        self._schedule_preset_param_update()

    def set_mod_speed(self, speed: int):
        val = max(0, min(100, int(speed)))
        if self.state.mod_speed != val:
            self.state.mod_speed = val
            self._schedule_preset_param_update()

    # --- Ações de Controle: Delay ---
    def set_delay_effect(self, dly_type: str, level: int):
        self.state.set_delay_effect(dly_type, level)
        self._schedule_preset_param_update()

    def set_delay_time(self, time_val: int):
        val = max(0, min(100, int(time_val)))
        if self.state.dly_time != val:
            self.state.dly_time = val
            self._schedule_preset_param_update()

    # --- Ações de Controle: Reverb ---
    def set_reverb_effect(self, rev_type: str, level: int):
        self.state.set_reverb_effect(rev_type, level)
        self._schedule_preset_param_update()

    def set_reverb_mix(self, mix: int):
        val = max(0, min(100, int(mix)))
        if self.state.rev_mix != val:
            self.state.rev_mix = val
            self._schedule_preset_param_update()

    # --- Ações de Controle: Gate & Cab ---
    def set_gate(self, val: int):
        v = max(0, min(100, int(val)))
        if self.state.gate != v:
            self.state.gate = v
            self.save_state_to_disk()
            self.state_updated.emit(self.state)

            if not self._suppress_midi_send:
                sysex = build_gate_sysex(v)
                self.midi.send_sysex(sysex)

    def set_cab(self, slot: int):
        c = max(0, min(8, int(slot)))
        if self.state.cab != c:
            self.state.cab = c
            self.save_state_to_disk()
            self.state_updated.emit(self.state)

            if not self._suppress_midi_send:
                sysex = build_cab_sysex(c)
                self.midi.send_sysex(sysex)

    # --- Ações de Controle: Presets & EEPROM ---
    def switch_preset(self, preset_target: Union[str, int]):
        if isinstance(preset_target, str):
            pid = parse_preset_name(preset_target)
        else:
            pid = int(preset_target)

        pname = get_preset_name(pid)
        self.state.preset = pname
        self.save_state_to_disk()
        self.preset_switched.emit(pid, pname)
        self.state_updated.emit(self.state)

        if not self._suppress_midi_send:
            sysex = build_preset_switch_sysex(pid)
            self.midi.send_sysex(sysex)
            self.notification.emit(f"Preset [{pname}] ativado na Tank-G.", "info")

    def save_current_preset(self, target_preset: Optional[Union[str, int]] = None) -> bool:
        """
        Salva o estado atual na EEPROM da pedaleira.
        Executa os 3 comandos validados:
          1. 0x69 (Gravação do bloco de 21 bytes com checksum de offset)
          2. 0x41 (Flush / verificação de commit)
          3. 0x49 (Ativação e recarga do preset)
        """
        if target_preset is not None:
            pid = parse_preset_name(str(target_preset)) if isinstance(target_preset, str) else int(target_preset)
        else:
            pid = parse_preset_name(self.state.preset)

        pname = get_preset_name(pid)
        self.state.preset = pname
        self.save_state_to_disk()

        # 1. Comando 0x69: Gravação EEPROM
        sysex_save = build_eeprom_save_sysex(pid, self.state)
        ok1 = self.midi.send_sysex(sysex_save)

        # 2. Comando 0x41: Flush
        sysex_flush = build_eeprom_flush_sysex()
        ok2 = self.midi.send_sysex(sysex_flush)

        # 3. Comando 0x49: Ativação
        sysex_switch = build_preset_switch_sysex(pid)
        ok3 = self.midi.send_sysex(sysex_switch)

        if ok1 and ok2 and ok3:
            self.preset_switched.emit(pid, pname)
            self.state_updated.emit(self.state)
            self.notification.emit(f"Preset [{pname}] gravado com sucesso na EEPROM!", "success")
            return True
        else:
            self.notification.emit(f"Falha ao gravar Preset [{pname}] na pedaleira.", "error")
            return False

    # --- Ações de Conexão MIDI ---
    def connect_midi(self, port_name: Optional[str] = None) -> bool:
        return self.midi.connect_device(port_name)

    def disconnect_midi(self):
        self.midi.disconnect_device()

    def get_available_ports(self) -> List[str]:
        outs, _ = self.midi.scan_ports()
        return outs

    # --- Ações do Agente de IA (Gemini) ---
    def generate_ai_preset(self, prompt: str, api_key: Optional[str] = None):
        """Dispara a geração de timbre via IA em thread secundária."""
        if self._ai_worker and self._ai_worker.isRunning():
            self.notification.emit("Aguarde: já existe uma criação de timbre em andamento.", "warning")
            return

        self.ai_generation_started.emit()
        self._ai_worker = AIGenerationWorker(self.gemini_service, prompt, api_key)
        self._ai_worker.preset_ready.connect(self._on_ai_preset_ready)
        self._ai_worker.error_occurred.connect(self._on_ai_generation_error)
        self._ai_worker.start()

    def _on_ai_preset_ready(self, state: PedalState, name: str, explanation: str):
        self.ai_preset_ready.emit(state, name, explanation)
        self.notification.emit(f"Timbre '{name}' gerado com sucesso pela IA!", "success")

    def _on_ai_generation_error(self, err_msg: str):
        self.ai_generation_error.emit(err_msg)
        self.notification.emit(err_msg, "error")

    def apply_ai_preset_preview(self, new_state: PedalState):
        """Aplica o timbre gerado pela IA imediatamente no pedal para teste em tempo real."""
        # Preserva o preset atual enquanto testa os parâmetros de áudio
        new_state.preset = self.state.preset
        self.state = new_state
        self.save_state_to_disk()
        self.state_updated.emit(self.state)

        # Transmite os parâmetros em tempo real para o pedal físico
        if self.is_connected:
            self.midi.send_sysex(build_preset_param_sysex(self.state))
            self.midi.send_sysex(build_gate_sysex(self.state.gate))
            self.midi.send_sysex(build_cab_sysex(self.state.cab))
            self.midi.send_sysex(build_module_bypass_sysex("amp", bool(self.state.amp_on)))
            self.midi.send_sysex(build_module_bypass_sysex("mod", bool(self.state.mod_on)))
            self.midi.send_sysex(build_module_bypass_sysex("dly", bool(self.state.dly_on)))
            self.midi.send_sysex(build_module_bypass_sysex("rev", bool(self.state.rev_on)))
            self.notification.emit("Timbre da IA aplicado no pedal para teste em tempo real!", "info")
        else:
            self.notification.emit("Timbre da IA carregado na tela (pedal desconectado).", "info")

    def save_ai_preset_to_slot(self, state: PedalState, target_slot: Union[str, int]) -> bool:
        """Aplica o timbre e grava na EEPROM do slot indicado."""
        self.state = state
        return self.save_current_preset(target_slot)

