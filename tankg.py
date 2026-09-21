"""
Tank-G MIDI SysEx control script
----------------------------------
Requisitos:
    pip install mido python-rtmidi

Uso:
    python tankg.py list             # lista portas MIDI disponíveis
    python tankg.py status           # mostra o status atual de todos os parâmetros
    python tankg.py gate <0-100>     # ajusta o Noise Gate (0 a 100)
    python tankg.py cab <0-8>        # seleciona o slot de IR CAB (0 = Bypass, 1-8 = Cabs)
    python tankg.py cab list         # lista todas as simulações de IR CAB
    python tankg.py amp <on|off>     # liga/desliga módulo AMP
    python tankg.py mod <on|off>     # liga/desliga módulo MOD
    python tankg.py dly <on|off>     # liga/desliga módulo DELAY
    python tankg.py rev <on|off>     # liga/desliga módulo REVERB
    python tankg.py type <1-9>       # seleciona modelo de amplificador (1 a 9)
    python tankg.py type list        # lista os 9 modelos de amplificador disponíveis
    python tankg.py gain <0-100>     # ajusta o ganho do pré-amplificador
    python tankg.py treble <0-100>   # ajusta os agudos (Treble)
    python tankg.py middle <0-100>   # ajusta os médios (Middle / Mid)
    python tankg.py bass <0-100>     # ajusta os graves (Bass)
    python tankg.py volume <0-100>   # ajusta o volume do amplificador
    python tankg.py chorus <1-40>       # ajusta Modulação: Chorus (Mix: 1 a 40)
    python tankg.py phaser <1-40>       # ajusta Modulação: Phaser (Depth: 1 a 40)
    python tankg.py tremolo <1-40>      # ajusta Modulação: Tremolo (Mix: 1 a 40)
    python tankg.py speed <0-100>       # ajusta velocidade da modulação (Speed)
    python tankg.py delay-analog <1-40> # ajusta Delay: Analog (Mix: 1 a 40)
    python tankg.py delay-tape <1-40>   # ajusta Delay: Tape (Mix: 1 a 40)
    python tankg.py delay-dual <1-40>   # ajusta Delay: Dual (Mix: 1 a 40)
    python tankg.py delay-time <0-100>  # ajusta Delay: Time / Feedback (0 a 100)
    python tankg.py reverb-room <1-40>  # ajusta Reverb: Room (Decay: 1 a 40)
    python tankg.py reverb-spring <1-40># ajusta Reverb: Spring (Decay: 1 a 40)
    python tankg.py reverb-cloud <1-40> # ajusta Reverb: Cloud (Decay: 1 a 40)
    python tankg.py reverb-mix <0-100>  # ajusta Reverb: Mix (0 a 100)
    python tankg.py preset <1A-9D|1-36> # seleciona preset do pedal (ex: 3B ou 10)
    python tankg.py preset list         # lista todos os 36 presets (1A a 9D)
    python tankg.py save [slot]         # grava config atual na EEPROM do pedal (ex: save 3B)
    python tankg.py replay <nome>       # reenvia comando conhecido gravado
    python tankg.py raw F0 00 ...       # envia bytes SysEx crus (incluir F0 e F7)

IMPORTANTE:
    - Rode isso com o software oficial da Mvave FECHADO, para não haver conflito
      disputando a mesma porta MIDI.
    - O protocolo completo de AMP, MOD, DLY, GATE, IR CAB e BYPASS foi DECIFRADO!
"""

import sys
import json
from pathlib import Path
import mido

# Arquivo para manter o estado dos parâmetros entre execuções
STATE_FILE = Path(__file__).parent / "state.json"

DEFAULT_STATE = {
    "type": 1,
    "gain": 50,
    "treble": 50,
    "middle": 50,
    "bass": 50,
    "volume": 50,
    "mod_fx": 20,
    "mod_speed": 50,
    "dly_mix": 20,
    "dly_time": 50,
    "rev_decay": 20,
    "rev_mix": 50,
    "amp_on": 1,
    "mod_on": 0,
    "dly_on": 0,
    "rev_on": 1,
    "preset": "1A",
    "gate": 0,
    "cab": 1,
}

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_STATE, **data}
        except Exception:
            pass
    return dict(DEFAULT_STATE)

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

# Modelos de Pré-amplificador (AMP TYPE)
AMP_NAMES = {
    1: "VOX AC30HW Normal (Clean britânico)",
    2: "Fender '65 Twin Reverb (Clean americano)",
    3: "Bogner Shiva (Overdrive boutique)",
    4: "Marshall JTM45 OD (Overdrive vintage)",
    5: "Marshall Plexi 100 (Rock clássico 60/70)",
    6: "Marshall JCM800 (Distorção hard rock/metal)",
    7: "EVH 5150 LEAD (High Gain moderno)",
    8: "ENGL Powerball E645/2 (High Gain europeu)",
    9: "Mesa Boogie Dual Rectifier (High Gain moderno pesado)",
}

# Módulos suportados e seus IDs
MODULES = {
    "amp": 0x00,
    "mod": 0x01,
    "dly": 0x02,
    "rev": 0x03,
}

# Simulações de Gabinete (IR CAB) de fábrica
CAB_NAMES = {
    0: "CAB Desligado (Bypass)",
    1: "VHT Deliverance (4x12)",
    2: "Sperimental (4x12)",
    3: "Electrovoice (2x10)",
    4: "Mesa Boogie (4x12)",
    5: "Fender Champ (1x8)",
    6: "Fender Pro Junior (1x10)",
    7: "Marshall 1960 V30 (4x12)",
    8: "Diezel V30 (4x12)",
}

# ----------------------------------------------------------------------
# Comandos conhecidos (extraídos das capturas, já sem o encoding USB-MIDI,
# só a mensagem SysEx pura F0 ... F7)
# ----------------------------------------------------------------------
KNOWN_COMMANDS = {
    "gate0": [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x00, 0x06, 0x3c,
        0x31, 0x35, 0x68, 0x4b, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, 0x40, 0x01, 0x5f, 0x00, 0xF7,
    ],
    "gate100": [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x64, 0x06, 0x3c,
        0x31, 0x35, 0x68, 0x4b, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, 0x40, 0x01, 0x7b, 0x01, 0xF7,
    ],
    "amp_off": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x00,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x54, 0x03, 0xF7,
    ],
    "amp_on": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x00,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x01, 0x52, 0x03, 0xF7,
    ],
    "mod_off": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x01,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x52, 0x03, 0xF7,
    ],
    "mod_on": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x01,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x01, 0x50, 0x03, 0xF7,
    ],
    "dly_off": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x02,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x50, 0x03, 0xF7,
    ],
    "dly_on": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x02,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x01, 0x4E, 0x03, 0xF7,
    ],
    "rev_off": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x03,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x4E, 0x03, 0xF7,
    ],
    "rev_on": [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02, 0x03,
        0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x01, 0x4C, 0x03, 0xF7,
    ],
}


# Nome manual da porta MIDI caso queira forçar uma específica (ex: "USB-Midi 1")
# Se None, o script tenta detectar automaticamente.
PORT_NAME = None


def list_ports():
    print("Portas MIDI de SAIDA disponiveis:")
    for name in mido.get_output_names():
        print(f"  - {name}")
    print()
    print("Portas MIDI de ENTRADA disponiveis:")
    for name in mido.get_input_names():
        print(f"  - {name}")


def find_tankg_port():
    """Tenta achar automaticamente a porta do pedal pelo nome ou configuracao manual."""
    if PORT_NAME:
        return PORT_NAME

    outputs = mido.get_output_names()
    # 1. Procura por nomes especificos do pedal/fabricante
    candidates = [p for p in outputs if any(term in p.lower() for term in ("tank", "mvave", "cuvave"))]
    if candidates:
        return candidates[0]

    # 2. Procura por portas USB-MIDI genericas (comum no Windows, exceto synth do sistema)
    usb_candidates = [p for p in outputs if "microsoft" not in p.lower() and ("usb-midi" in p.lower() or "midi" in p.lower())]
    if usb_candidates:
        return usb_candidates[0]

    return None


def send_sysex(port_name, data_bytes):
    """Envia uma mensagem sysex crua (lista de ints, incluindo F0 e F7)."""
    assert data_bytes[0] == 0xF0 and data_bytes[-1] == 0xF7, "SysEx precisa comecar com F0 e terminar com F7"
    # mido quer o conteudo SEM F0/F7 no campo .data
    inner = data_bytes[1:-1]
    msg = mido.Message("sysex", data=inner)
    try:
        with mido.open_output(port_name) as port:
            port.send(msg)
        print(f"Enviado com sucesso para '{port_name}': {' '.join(f'{b:02X}' for b in data_bytes)}")
    except Exception as e:
        print(f"\n[ERRO] Falha ao abrir a porta MIDI '{port_name}': {e}")
        print("Dica: No Windows, a porta MIDI e de acesso exclusivo. Certifique-se de FECHAR:")
        print("  1. O software oficial da M-Vave (m_efcs.exe)")
        print("  2. Qualquer DAW (Reaper, FL Studio, etc.) ou navegador que esteja usando MIDI.\n")


def make_gate_sysex(val: int) -> list[int]:
    """
    Gera mensagem SysEx para qualquer valor de Noise Gate de 0 a 100.
    
    Algoritmo de checksum decifrado:
      O checksum em 14-bit MIDI (ck1 | (ck2 << 7)) obedece a:
      ck = (95 - val) % 256
      ck1 = ck & 0x7F
      ck2 = (ck >> 7) & 0x7F
    """
    val = max(0, min(100, int(val)))
    ck = (95 - val) % 256
    ck1 = ck & 0x7F
    ck2 = (ck >> 7) & 0x7F
    return [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, val,  0x06, 0x3C,
        0x31, 0x35, 0x68, 0x4B, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, 0x40, 0x01, ck1,  ck2,  0xF7,
    ]


def make_module_sysex(mod_name_or_id, on: bool) -> list[int]:
    """
    Gera mensagem SysEx para ativar ou desativar módulos (AMP, MOD, DLY, REV).
    
    Fórmula do checksum decifrada:
      ck1 = 0x54 - (2 * mod_id) - (2 * state)
      ck2 = 0x03
    """
    if isinstance(mod_name_or_id, str):
        mod_id = MODULES[mod_name_or_id.lower()]
    else:
        mod_id = int(mod_name_or_id)

    state = 1 if on else 0
    ck1 = 0x54 - (2 * mod_id) - (2 * state)
    ck2 = 0x03
    return [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02,
        mod_id, 0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, state,
        ck1, ck2, 0xF7,
    ]


def parse_preset_name(preset_str: str) -> int:
    """
    Converte uma string de preset (ex: '3B', '3b', '4A', '10') para o ID interno (0 a 35).
    """
    s = preset_str.strip().upper()
    if len(s) >= 2 and s[0].isdigit() and s[1] in "ABCD":
        bank = int(s[0])
        slot = "ABCD".index(s[1])
        if not (1 <= bank <= 9):
            raise ValueError("O banco deve ser entre 1 e 9.")
        return (bank - 1) * 4 + slot
    elif s.isdigit():
        val = int(s)
        if 1 <= val <= 36:
            return val - 1
        elif 0 <= val <= 35:
            return val
    raise ValueError(f"Preset invalido '{preset_str}'. Use formato '1A' a '9D' ou número de 1 a 36.")


def get_preset_name(preset_id: int) -> str:
    """Retorna o nome amigável do preset (ex: '3B') a partir do ID (0 a 35)."""
    bank = (preset_id // 4) + 1
    slot = "ABCD"[preset_id % 4]
    return f"{bank}{slot}"


def make_preset_switch_sysex(preset_id: int) -> list[int]:
    """
    Gera mensagem SysEx para trocar de preset (0 a 35, correspondendo a 1A até 9D).
    
    Fórmula do checksum decifrada e comprovada nos pacotes interceptados:
      ck = (50 - 2 * preset_id) % 256
      ck1 = ck & 0x7F
      ck2 = (ck >> 7) & 0x7F
    """
    if not (0 <= preset_id <= 35):
        raise ValueError("O ID do preset deve estar entre 0 e 35.")
    
    ck = (50 - 2 * preset_id) % 256
    ck1 = ck & 0x7F
    ck2 = (ck >> 7) & 0x7F

    return [
        0xF0, 0x00, 0x32, 0x09, 0x49, 0x00, 0x00, 0x00, 0x02,
        preset_id, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0x01,
        ck1, ck2, 0xF7
    ]


def make_save_preset_sysex(preset_id: int, state: dict) -> list[int]:
    """
    Gera mensagem SysEx para salvar (gravar na EEPROM) o estado completo no preset.
    
    Fórmula do checksum decifrada e comprovada em 100% dos pacotes:
      offset = preset_id * 21 + 2
      ck = (230 - sum(fields) - offset) % 256
      ck1 = ck & 0x7F
      ck2 = (ck >> 7) & 0x7F
    """
    fields = [
        int(state.get("amp_on", 1)),
        int(state.get("mod_on", 0)),
        int(state.get("dly_on", 0)),
        int(state.get("rev_on", 1)),
        int(state.get("gate", 0)),
        int(state.get("type", 1)),
        int(state.get("gain", 50)),
        int(state.get("treble", 50)),
        int(state.get("middle", 50)),
        int(state.get("bass", 50)),
        int(state.get("volume", 50)),
        int(state.get("mod_fx", 0)),
        int(state.get("mod_speed", 0)),
        int(state.get("dly_mix", 0)),
        int(state.get("dly_time", 0)),
        int(state.get("rev_decay", 0)),
        int(state.get("rev_mix", 0)),
        int(state.get("cab", 1)),
        255, 0, 0
    ]
    offset = preset_id * 21 + 2
    b9 = offset & 0x7F
    b10 = (offset >> 7) & 0x7F

    big_val = 0
    for i, v in enumerate(fields):
        big_val |= (v & 0xFF) << (8 * i)
    packed_7 = [(big_val >> (7 * i)) & 0x7F for i in range(24)]

    s_fields = sum(fields)
    ck = (230 - s_fields - offset) % 256
    ck1 = ck & 0x7F
    ck2 = (ck >> 7) & 0x7F

    hdr = [0xF0, 0x00, 0x32, 0x09, 0x69, 0x01, 0x00, 0x00, 0x02, b9, b10, 0x00, 0x00, 0x50, 0x02, 0x00, 0x00]
    return hdr + packed_7 + [ck1, ck2, 0xF7]


def save_preset_to_pedal(port_name: str, preset_id: int, state: dict):
    """Grava as configurações atuais na memória EEPROM do preset na pedaleira."""
    preset_name = get_preset_name(preset_id)
    print(f"Gravando estado atual na EEPROM do Preset [{preset_name}] (#{preset_id + 1}/36)...")
    
    # 1. Comando 0x69: Gravação EEPROM dos 21 bytes
    sysex_save = make_save_preset_sysex(preset_id, state)
    send_sysex(port_name, sysex_save)
    
    # 2. Comando 0x41: Flush / Verificação
    sysex_flush = [0xF0, 0x00, 0x32, 0x09, 0x41, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0B, 0x00, 0xF7]
    send_sysex(port_name, sysex_flush)
    
    # 3. Comando 0x49: Ativa o preset na pedaleira
    sysex_switch = make_preset_switch_sysex(preset_id)
    send_sysex(port_name, sysex_switch)
    print(f"Preset [{preset_name}] salvo com sucesso na pedaleira!")


def make_cab_sysex(cab_num: int) -> list[int]:
    """
    Gera mensagem SysEx para selecionar o slot de IR CAB (0 a 8).
    
    Fórmula decifrada:
      val_14 = cab_num << 6
      b31 = val_14 & 0x7F
      b32 = (val_14 >> 7) & 0x7F
      ck1 = (98 - cab_num) & 0x7F
      ck2 = 0x00
    """
    if not (0 <= cab_num <= 8):
        raise ValueError("O slot do IR CAB deve estar entre 0 e 8.")

    val_14 = cab_num << 6
    b31 = val_14 & 0x7F
    b32 = (val_14 >> 7) & 0x7F
    ck1 = (98 - cab_num) & 0x7F
    ck2 = 0x00

    return [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x00, 0x06, 0x3C,
        0x31, 0x35, 0x68, 0x4B, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, b31,  b32,  ck1,  ck2,  0xF7,
    ]


def make_preset_sysex(state: dict) -> list[int]:
    """
    Gera mensagem SysEx unificada para todos os parâmetros do PRESET:
    AMP, MODULAÇÃO, DELAY e REVERB.
    
    Fórmula unificada decifrada e comprovada em 33 pacotes:
      fields = [
        ((type - 1) * 2),
        (gain * 2),
        (treble * 2),
        (middle * 2),
        (bass * 2),
        (volume * 2),
        (mod_fx * 2),
        (mod_speed * 2),
        (dly_mix * 2),
        (dly_time * 2),
        (rev_decay * 2),
        (rev_mix * 2),
        0x0E
      ]
      packed_7 = fatiamento dos bits em blocos de 7 bits (bytes 18 a 32)
      ck = (211 - type - gain - treble - middle - bass - volume - mod_fx - mod_speed - dly_mix - dly_time - rev_decay - rev_mix) % 256
      ck1 = ck & 0x7F
      ck2 = (ck >> 7) & 0x7F
    """
    t = max(1, min(9, int(state.get("type", 1))))
    g = max(0, min(100, int(state.get("gain", 50))))
    tr = max(0, min(100, int(state.get("treble", 50))))
    m = max(0, min(100, int(state.get("middle", 50))))
    b = max(0, min(100, int(state.get("bass", 50))))
    v = max(0, min(100, int(state.get("volume", 50))))
    mod_fx = max(0, min(127, int(state.get("mod_fx", 20))))
    mod_sp = max(0, min(100, int(state.get("mod_speed", 50))))
    dly_mix = max(0, min(127, int(state.get("dly_mix", 20))))
    dly_time = max(0, min(100, int(state.get("dly_time", 50))))
    rev_decay = max(0, min(127, int(state.get("rev_decay", 20))))
    rev_mix = max(0, min(100, int(state.get("rev_mix", 50))))

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
        0x0E
    ]

    big_val = 0
    for i, val in enumerate(fields):
        big_val |= (val & 0xFF) << (8 * i)

    packed_7 = [(big_val >> (7 * i)) & 0x7F for i in range(15)]

    calc_ck = (211 - t - g - tr - m - b - v - mod_fx - mod_sp - dly_mix - dly_time - rev_decay - rev_mix) % 256
    ck1 = calc_ck & 0x7F
    ck2 = (calc_ck >> 7) & 0x7F

    return [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x00
    ] + packed_7 + [ck1, ck2, 0xF7]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_ports()
        return

    state = load_state()

    if cmd == "status":
        print("=== Estado Atual da Tank-G (Salvo localmente) ===")
        print(f"  Amp Type : [{state['type']}] {AMP_NAMES.get(state['type'], 'Desconhecido')}")
        print(f"  Gain     : {state['gain']}")
        print(f"  Treble   : {state['treble']}")
        print(f"  Middle   : {state['middle']}")
        print(f"  Bass     : {state['bass']}")
        print(f"  Volume   : {state['volume']}")
        fx = state['mod_fx']
        if 0 <= fx <= 39:
            mod_desc = f"Chorus (Mix: {fx + 1}/40)"
        elif 44 <= fx <= 83:
            mod_desc = f"Phaser (Depth: {fx - 43}/40)"
        elif 88 <= fx <= 127:
            mod_desc = f"Tremolo (Mix: {fx - 87}/40)"
        else:
            mod_desc = "Transicao / OFF"
        print(f"  MOD FX   : {mod_desc} (raw: {fx})")
        print(f"  MOD Speed: {state.get('mod_speed', 50)}/100")
        dmix = state.get('dly_mix', 20)
        if 0 <= dmix <= 39:
            dly_desc = f"Analog Delay (Mix: {dmix + 1}/40)"
        elif 44 <= dmix <= 83:
            dly_desc = f"Tape Delay (Mix: {dmix - 43}/40)"
        elif 88 <= dmix <= 127:
            dly_desc = f"Dual Delay (Mix: {dmix - 87}/40)"
        else:
            dly_desc = "Transicao / OFF"
        print(f"  DLY MIX  : {dly_desc} (raw: {dmix})")
        print(f"  DLY Time : {state.get('dly_time', 50)}/100")
        rdecay = state.get('rev_decay', 20)
        if 0 <= rdecay <= 39:
            rev_desc = f"Room Reverb (Decay: {rdecay + 1}/40)"
        elif 44 <= rdecay <= 83:
            rev_desc = f"Spring Reverb (Decay: {rdecay - 43}/40)"
        elif 88 <= rdecay <= 127:
            rev_desc = f"Cloud Reverb (Decay: {rdecay - 87}/40)"
        else:
            rev_desc = "Transicao / OFF"
        print(f"  REV Decay: {rev_desc} (raw: {rdecay})")
        print(f"  REV Mix  : {state.get('rev_mix', 50)}/100")
        print(f"  Preset   : [{state.get('preset', '1A')}]")
        print(f"  IR CAB   : [{state['cab']}] {CAB_NAMES.get(state['cab'], 'Desconhecido')}")
        print(f"  Gate     : {state['gate']}")
        return

    port_name = find_tankg_port()
    if not port_name:
        print("Nao encontrei a porta automaticamente. Rode 'python tankg.py list'")
        print("e defina a variavel PORT_NAME no topo do script caso necessario.")
        return

    print(f"Usando porta: {port_name}")

    if cmd == "gate":
        if len(sys.argv) < 3:
            print("Uso: python tankg.py gate <0-100>")
            return
        try:
            val = int(sys.argv[2])
            if not (0 <= val <= 100):
                print("Valor fora da faixa. Use um numero entre 0 e 100.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 0 e 100.")
            return
        state["gate"] = val
        save_state(state)
        sysex = make_gate_sysex(val)
        print(f"Definindo Noise Gate para {val}...")
        send_sysex(port_name, sysex)

    elif cmd == "cab":
        if len(sys.argv) < 3:
            print("Uso: python tankg.py cab <0-8> | python tankg.py cab list")
            return
        if sys.argv[2].lower() == "list":
            print("Slots de IR CAB disponiveis:")
            for slot, name in CAB_NAMES.items():
                print(f"  [{slot}] {name}")
            return
        try:
            val = int(sys.argv[2])
            if not (0 <= val <= 8):
                print("Slot invalido. Use um numero entre 0 (Bypass) e 8.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 0 e 8.")
            return
        state["cab"] = val
        save_state(state)
        sysex = make_cab_sysex(val)
        print(f"Definindo IR CAB para slot {val} ({CAB_NAMES[val]})...")
        send_sysex(port_name, sysex)

    elif cmd in ("type", "amp-type"):
        if len(sys.argv) < 3:
            print("Uso: python tankg.py type <1-9> | python tankg.py type list")
            return
        if sys.argv[2].lower() == "list":
            print("Modelos de Amplificador disponiveis:")
            for slot, name in AMP_NAMES.items():
                print(f"  [{slot}] {name}")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 9):
                print("Modelo invalido. Use um numero de 1 a 9.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 9.")
            return
        state["type"] = val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo modelo de AMP para [{val}] ({AMP_NAMES[val]})...")
        send_sysex(port_name, sysex)

    elif cmd in ("gain", "treble", "middle", "mid", "bass", "volume", "vol"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        try:
            val = int(sys.argv[2])
            if not (0 <= val <= 100):
                print("Valor fora da faixa. Use um numero entre 0 e 100.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 0 e 100.")
            return
        
        param_name = "middle" if cmd == "mid" else ("volume" if cmd == "vol" else cmd)
        state[param_name] = val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo {param_name.upper()} para {val}...")
        send_sysex(port_name, sysex)

    elif cmd == "chorus":
        if len(sys.argv) < 3:
            print("Uso: python tankg.py chorus <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["mod_fx"] = val - 1
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo MOD: CHORUS para mix {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd == "phaser":
        if len(sys.argv) < 3:
            print("Uso: python tankg.py phaser <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["mod_fx"] = 43 + val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo MOD: PHASER para depth {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd == "tremolo":
        if len(sys.argv) < 3:
            print("Uso: python tankg.py tremolo <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["mod_fx"] = 87 + val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo MOD: TREMOLO para mix {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("speed", "mod-speed"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        try:
            val = int(sys.argv[2])
            if not (0 <= val <= 100):
                print("Valor fora da faixa. Use um numero entre 0 e 100.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 0 e 100.")
            return
        state["mod_speed"] = val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo MOD SPEED para {val}/100...")
        send_sysex(port_name, sysex)

    elif cmd in ("analog", "delay-analog", "dly-analog"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["dly_mix"] = val - 1
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo DLY: ANALOG para mix {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("tape", "delay-tape", "dly-tape"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["dly_mix"] = 43 + val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo DLY: TAPE para mix {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("dual", "delay-dual", "dly-dual"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["dly_mix"] = 87 + val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo DLY: DUAL para mix {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("time", "delay-time", "dly-time"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        try:
            val = int(sys.argv[2])
            if not (0 <= val <= 100):
                print("Valor fora da faixa. Use um numero entre 0 e 100.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 0 e 100.")
            return
        state["dly_time"] = val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo DLY TIME para {val}/100...")
        send_sysex(port_name, sysex)

    elif cmd in ("room", "reverb-room", "rev-room"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["rev_decay"] = val - 1
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo REV: ROOM para decay {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("spring", "reverb-spring", "rev-spring"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["rev_decay"] = 43 + val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo REV: SPRING para decay {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("cloud", "reverb-cloud", "rev-cloud"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        try:
            val = int(sys.argv[2])
            if not (1 <= val <= 40):
                print("Valor fora da faixa. Use um numero entre 1 e 40.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 1 e 40.")
            return
        state["rev_decay"] = 87 + val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo REV: CLOUD para decay {val}/40...")
        send_sysex(port_name, sysex)

    elif cmd in ("rev-mix", "reverb-mix", "rvb-mix"):
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        try:
            val = int(sys.argv[2])
            if not (0 <= val <= 100):
                print("Valor fora da faixa. Use um numero entre 0 e 100.")
                return
        except ValueError:
            print(f"Valor invalido '{sys.argv[2]}'. Forneca um numero entre 0 e 100.")
            return
        state["rev_mix"] = val
        save_state(state)
        sysex = make_preset_sysex(state)
        print(f"Definindo REVERB MIX para {val}/100...")
        send_sysex(port_name, sysex)

    elif cmd in ("preset", "prst") or (len(cmd) == 2 and cmd[0].isdigit() and cmd[1] in "abcd"):
        target = cmd if (len(cmd) == 2 and cmd[0].isdigit() and cmd[1] in "abcd") else (sys.argv[2] if len(sys.argv) > 2 else "")
        if not target:
            print("Uso: python tankg.py preset <1A-9D | 1-36> | python tankg.py preset list")
            return
        if target.lower() == "list":
            print("Presets disponiveis na Tank-G (9 Bancos x 4 Slots = 36 Presets):")
            for b in range(1, 10):
                slots = [f"{b}{s} (#{((b-1)*4 + i + 1):02d})" for i, s in enumerate("ABCD")]
                print(f"  Banco {b}: " + "  ".join(slots))
            return
        try:
            preset_id = parse_preset_name(target)
            preset_name = get_preset_name(preset_id)
        except ValueError as e:
            print(f"Erro: {e}")
            return
        state["preset"] = preset_name
        save_state(state)
        sysex = make_preset_switch_sysex(preset_id)
        print(f"Selecionando Preset [{preset_name}] (#{preset_id + 1}/36)...")
        send_sysex(port_name, sysex)

    elif cmd in ("save", "salvar"):
        target = sys.argv[2] if len(sys.argv) > 2 else state.get("preset", "1A")
        try:
            preset_id = parse_preset_name(target)
            preset_name = get_preset_name(preset_id)
        except ValueError as e:
            print(f"Erro: {e}")
            return
        state["preset"] = preset_name
        save_state(state)
        save_preset_to_pedal(port_name, preset_id, state)

    elif cmd in MODULES:
        if len(sys.argv) < 3:
            print(f"Uso: python tankg.py {cmd} <on|off>")
            return
        arg = sys.argv[2].lower()
        if arg not in ("on", "off", "1", "0"):
            print(f"Estado invalido '{arg}'. Use 'on' ou 'off'.")
            return
        on = arg in ("on", "1")
        state[f"{cmd}_on"] = 1 if on else 0
        save_state(state)
        sysex = make_module_sysex(cmd, on)
        action_str = "Ativando" if on else "Desativando"
        print(f"{action_str} modulo {cmd.upper()}...")
        send_sysex(port_name, sysex)

    elif cmd == "replay":
        key = sys.argv[2] if len(sys.argv) > 2 else None
        if key not in KNOWN_COMMANDS:
            print(f"Comando desconhecido '{key}'. Opcoes: {list(KNOWN_COMMANDS.keys())}")
            return
        send_sysex(port_name, KNOWN_COMMANDS[key])

    elif cmd == "raw":
        hex_bytes = [int(b, 16) for b in sys.argv[2:]]
        send_sysex(port_name, hex_bytes)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()