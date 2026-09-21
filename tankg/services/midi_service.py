"""
Serviço assíncrono de comunicação MIDI para a Tank-G.
Gerencia conexão, reconexão automática, envio SysEx thread-safe e escuta de eventos.
"""

from typing import List, Optional, Tuple
import threading
import time

from PySide6.QtCore import QObject, Signal, QThread, Slot
import mido


class MidiWorker(QThread):
    """Thread em segundo plano para escutar mensagens MIDI de entrada sem travar a UI."""
    message_received = Signal(list)
    error_occurred = Signal(str, str)

    def __init__(self, port_name: str):
        super().__init__()
        self.port_name = port_name
        self._running = True
        self._inport = None

    def run(self):
        try:
            self._inport = mido.open_input(self.port_name)
        except Exception as e:
            self.error_occurred.emit(
                "Falha ao abrir entrada MIDI",
                f"Não foi possível abrir a porta de entrada '{self.port_name}': {e}"
            )
            return

        while self._running:
            try:
                for msg in self._inport.iter_pending():
                    if msg.type == "sysex":
                        raw = [0xF0] + list(msg.data) + [0xF7]
                        self.message_received.emit(raw)
                time.sleep(0.01)
            except Exception:
                break

        if self._inport:
            try:
                self._inport.close()
            except Exception:
                pass

    def stop(self):
        self._running = False
        self.wait(1000)


class MidiService(QObject):
    """
    Serviço central de I/O MIDI.
    Expõe sinais Qt thread-safe para a ViewModel.
    """
    connection_changed = Signal(bool, str, str)  # (is_connected, port_name, error_detail)
    ports_changed = Signal(list, list)           # (output_ports, input_ports)
    message_received = Signal(list)              # (raw_sysex_bytes)
    message_sent = Signal(list)                  # (raw_sysex_bytes)
    error_occurred = Signal(str, str)            # (title, detail)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._outport_name: Optional[str] = None
        self._outport: Optional[mido.ports.BaseOutput] = None
        self._worker: Optional[MidiWorker] = None
        self._lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        return self._outport is not None and not self._outport.closed

    @property
    def current_port(self) -> Optional[str]:
        return self._outport_name

    def scan_ports(self) -> Tuple[List[str], List[str]]:
        """Retorna lista de portas de saída e de entrada disponíveis."""
        try:
            outputs = mido.get_output_names()
            inputs = mido.get_input_names()
        except Exception:
            outputs, inputs = [], []
        self.ports_changed.emit(outputs, inputs)
        return outputs, inputs

    def find_tankg_port(self, preferred: Optional[str] = None) -> Optional[str]:
        """Tenta encontrar automaticamente o nome da porta da Tank-G."""
        if preferred:
            return preferred

        outputs, _ = self.scan_ports()
        # 1. Procura nomes específicos do fabricante/pedaleira
        for p in outputs:
            plow = p.lower()
            if any(k in plow for k in ("tank", "mvave", "cuvave", "m-vave")):
                return p

        # 2. Procura portas USB-MIDI genéricas (comum no Windows)
        for p in outputs:
            plow = p.lower()
            if "microsoft" not in plow and ("usb-midi" in plow or "midi" in plow):
                return p

        return None

    def connect_device(self, port_name: Optional[str] = None) -> bool:
        """Conecta à porta MIDI especificada ou auto-detectada."""
        self.disconnect_device()

        target_port = port_name or self.find_tankg_port()
        if not target_port:
            msg = "Nenhuma porta MIDI da Tank-G encontrada. Verifique se o cabo USB está plugado."
            self.connection_changed.emit(False, "", msg)
            return False

        try:
            # Abre porta de saída
            self._outport = mido.open_output(target_port)
            self._outport_name = target_port

            # Inicia worker de entrada caso a porta exista também nas entradas
            _, inputs = self.scan_ports()
            matching_in = next((p for p in inputs if target_port.lower() in p.lower() or p.lower() in target_port.lower()), None)
            if matching_in:
                self._worker = MidiWorker(matching_in)
                self._worker.message_received.connect(self.message_received.emit)
                self._worker.start()

            self.connection_changed.emit(True, target_port, "")
            return True

        except Exception as e:
            err_str = str(e)
            hint = (
                f"Falha ao abrir a porta MIDI '{target_port}': {err_str}\n\n"
                "Aviso do Windows: No Windows, portas MIDI são de uso exclusivo.\n"
                "Certifique-se de FECHAR:\n"
                "  - O software oficial da M-Vave (m_efcs.exe)\n"
                "  - Qualquer DAW (Reaper, FL Studio, Ableton) disputando a porta."
            )
            self.disconnect_device()
            self.connection_changed.emit(False, target_port, hint)
            self.error_occurred.emit("Erro de Conexão MIDI", hint)
            return False

    def disconnect_device(self):
        """Fecha as portas abertas e para o worker com segurança."""
        if self._worker:
            self._worker.stop()
            self._worker = None

        with self._lock:
            if self._outport:
                try:
                    self._outport.close()
                except Exception:
                    pass
                self._outport = None

        port = self._outport_name
        self._outport_name = None
        if port:
            self.connection_changed.emit(False, port, "Desconectado")

    def send_sysex(self, data_bytes: List[int]) -> bool:
        """Envia pacote SysEx cru (incluindo 0xF0 e 0xF7)."""
        if not data_bytes or data_bytes[0] != 0xF0 or data_bytes[-1] != 0xF7:
            self.error_occurred.emit("SysEx Inválido", "A mensagem SysEx deve começar com F0 e terminar com F7.")
            return False

        if not self.is_connected:
            # Tenta auto-conectar
            if not self.connect_device(self._outport_name):
                return False

        with self._lock:
            try:
                inner = data_bytes[1:-1]
                msg = mido.Message("sysex", data=inner)
                self._outport.send(msg)
                self.message_sent.emit(data_bytes)
                return True
            except Exception as e:
                self.error_occurred.emit("Falha no Envio MIDI", f"Erro ao transmitir SysEx: {e}")
                self.disconnect_device()
                return False
