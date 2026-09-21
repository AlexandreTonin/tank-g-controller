"""
Codec puro para montagem e decodificação de mensagens SysEx da Tank-G.
Implementa as fórmulas de checksum decifradas e empacotamento de bits.
Sem dependências de bibliotecas de GUI ou de hardware.
"""

from typing import List, Tuple, Optional, Union
from ..core.constants import MODULES
from ..model.pedal_state import PedalState
from .param_map import pack_7bit, unpack_7bit, calc_eeprom_offset


def calc_14bit_checksum(ck_val: int) -> Tuple[int, int]:
    """
    Separa um valor de checksum de 8 bits em dois bytes de 7 bits (14-bit MIDI).
    ck1 = ck & 0x7F, ck2 = (ck >> 7) & 0x7F
    """
    ck = ck_val % 256
    return ck & 0x7F, (ck >> 7) & 0x7F


def build_gate_sysex(val: int) -> List[int]:
    """
    Gera mensagem SysEx para o Noise Gate (0 a 100).
    Checksum: ck = (95 - val) % 256
    """
    v = max(0, min(100, int(val)))
    ck = (95 - v) % 256
    ck1, ck2 = calc_14bit_checksum(ck)
    return [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, v,    0x06, 0x3C,
        0x31, 0x35, 0x68, 0x4B, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, 0x40, 0x01, ck1,  ck2,  0xF7,
    ]


def build_cab_sysex(cab_slot: int) -> List[int]:
    """
    Gera mensagem SysEx para selecionar o slot de IR CAB (0 a 8).
    0 = Bypass, 1 a 8 = Cabs de fábrica.
    Fórmula: val_14 = cab_slot << 6, ck1 = (98 - cab_slot) & 0x7F, ck2 = 0x00
    """
    c = max(0, min(8, int(cab_slot)))
    val_14 = c << 6
    b31 = val_14 & 0x7F
    b32 = (val_14 >> 7) & 0x7F
    ck1 = (98 - c) & 0x7F
    ck2 = 0x00
    return [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x00, 0x06, 0x3C,
        0x31, 0x35, 0x68, 0x4B, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, b31,  b32,  ck1,  ck2,  0xF7,
    ]


def build_module_bypass_sysex(module_name_or_id: Union[str, int], on: bool) -> List[int]:
    """
    Gera mensagem SysEx para ativar ou desativar módulos (AMP, MOD, DLY, REV).
    Comando 0x49, sub-registro 0x11.
    Fórmula: ck1 = 0x54 - (2 * mod_id) - (2 * state), ck2 = 0x03
    """
    if isinstance(module_name_or_id, str):
        key = module_name_or_id.lower()
        if key not in MODULES:
            raise ValueError(f"Módulo desconhecido: '{module_name_or_id}'")
        mod_id = MODULES[key]
    else:
        mod_id = int(module_name_or_id)

    state = 1 if on else 0
    ck1 = 0x54 - (2 * mod_id) - (2 * state)
    ck2 = 0x03
    return [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02,
        mod_id, 0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, state,
        ck1, ck2, 0xF7,
    ]


def build_preset_switch_sysex(preset_id: int) -> List[int]:
    """
    Gera mensagem SysEx para trocar de preset (0 a 35, correspondendo a 1A até 9D).
    Comando 0x49, sub-registro 0x1E.
    Fórmula: ck = (50 - 2 * preset_id) % 256
    """
    if not (0 <= preset_id <= 35):
        raise ValueError(f"Preset ID deve estar entre 0 e 35. Recebido: {preset_id}")

    ck = (50 - 2 * preset_id) % 256
    ck1, ck2 = calc_14bit_checksum(ck)
    return [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02,
        preset_id, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0x01,
        ck1, ck2, 0xF7,
    ]


def build_preset_param_sysex(state: PedalState) -> List[int]:
    """
    Gera mensagem SysEx em tempo real (Comando 0x31, 36 bytes) com todos os parâmetros do preset:
    AMP (tipo, ganho, treble, middle, bass, volume),
    MODULAÇÃO (fx, speed), DELAY (mix, time), REVERB (decay, mix).
    
    Fórmula:
      ck = (211 - type - gain - treble - middle - bass - volume - mod_fx - mod_speed - dly_mix - dly_time - rev_decay - rev_mix) % 256
    """
    t = max(1, min(9, int(state.type)))
    g = max(0, min(100, int(state.gain)))
    tr = max(0, min(100, int(state.treble)))
    m = max(0, min(100, int(state.middle)))
    b = max(0, min(100, int(state.bass)))
    v = max(0, min(100, int(state.volume)))
    mod_fx = max(0, min(127, int(state.mod_fx)))
    mod_sp = max(0, min(100, int(state.mod_speed)))
    dly_mix = max(0, min(127, int(state.dly_mix)))
    dly_time = max(0, min(100, int(state.dly_time)))
    rev_decay = max(0, min(127, int(state.rev_decay)))
    rev_mix = max(0, min(100, int(state.rev_mix)))

    fields = [
        ((t - 1) * 2),
        (g * 2),
        (tr * 2),
        (m * 2),
        (b * 2),
        (v * 2),
        (mod_fx * 2),
        (mod_sp * 2),
        (dly_mix * 2),
        (dly_time * 2),
        (rev_decay * 2),
        (rev_mix * 2),
        0x0E,
    ]

    packed_7 = pack_7bit(fields, 15)

    ck_val = (211 - t - g - tr - m - b - v - mod_fx - mod_sp - dly_mix - dly_time - rev_decay - rev_mix) % 256
    ck1, ck2 = calc_14bit_checksum(ck_val)

    hdr = [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x00,
    ]
    return hdr + packed_7 + [ck1, ck2, 0xF7]


def build_eeprom_save_sysex(preset_id: int, state: PedalState) -> List[int]:
    """
    Gera mensagem SysEx para gravação na EEPROM da pedaleira (Comando 0x69, 44 bytes).
    
    Fórmula do Checksum:
      offset = preset_id * 21 + 2
      ck = (230 - sum(fields) - offset) % 256
    """
    fields = [
        int(state.amp_on),
        int(state.mod_on),
        int(state.dly_on),
        int(state.rev_on),
        int(state.gate),
        int(state.type),
        int(state.gain),
        int(state.treble),
        int(state.middle),
        int(state.bass),
        int(state.volume),
        int(state.mod_fx),
        int(state.mod_speed),
        int(state.dly_mix),
        int(state.dly_time),
        int(state.rev_decay),
        int(state.rev_mix),
        int(state.cab),
        255, 0, 0,
    ]
    offset = calc_eeprom_offset(preset_id)
    b9 = offset & 0x7F
    b10 = (offset >> 7) & 0x7F

    packed_7 = pack_7bit(fields, 24)

    s_fields = sum(fields)
    ck = (230 - s_fields - offset) % 256
    ck1, ck2 = calc_14bit_checksum(ck)

    hdr = [
        0xF0, 0x00, 0x32, 0x09, 0x69, 0x01, 0x00, 0x00, 0x02,
        b9, b10, 0x00, 0x00, 0x50, 0x02, 0x00, 0x00,
    ]
    return hdr + packed_7 + [ck1, ck2, 0xF7]


def build_eeprom_flush_sysex() -> List[int]:
    """
    Gera mensagem SysEx de flush / commit na memória flash da pedaleira (Comando 0x41).
    """
    return [
        0xF0, 0x00, 0x32, 0x09, 0x41, 0x00, 0x00, 0x00, 0x02,
        0x00, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0B,
        0x00, 0xF7,
    ]


def parse_sysex(data: List[int]) -> Optional[dict]:
    """
    Analisa um pacote SysEx recebido da Tank-G e extrai o comando e informações se reconhecido.
    """
    if len(data) < 5 or data[0] != 0xF0 or data[-1] != 0xF7:
        return None
    # Verifica fabricante M-Vave (0x00, 0x32, 0x09)
    if data[1:4] != [0x00, 0x32, 0x09]:
        return None

    cmd = data[4]
    # Troca de preset recebida (0x49, sub-registro 0x1E)
    if cmd == 0x49 and len(data) >= 18 and data[13] == 0x1E:
        preset_id = data[9]
        return {"type": "preset_switch", "preset_id": preset_id}

    # Bypass de módulo recebido (0x49, sub-registro 0x11)
    if cmd == 0x49 and len(data) >= 18 and data[13] == 0x11:
        mod_id = data[9]
        state = data[17]
        return {"type": "module_bypass", "module_id": mod_id, "state": bool(state)}

    return {"type": "raw", "cmd": cmd, "data": data}
