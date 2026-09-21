"""
Implementação da interface de linha de comando (CLI) da Tank-G.
Utiliza os módulos refatorados Model e Services mantendo 100% de retrocompatibilidade.
"""

import sys
from pathlib import Path
from typing import List

import mido

from ..core.constants import AMP_NAMES, CAB_NAMES, MODULES
from ..model.pedal_state import PedalState
from ..model.preset import parse_preset_name, get_preset_name
from ..services.sysex_codec import (
    build_gate_sysex,
    build_cab_sysex,
    build_module_bypass_sysex,
    build_preset_switch_sysex,
    build_preset_param_sysex,
    build_eeprom_save_sysex,
    build_eeprom_flush_sysex,
)

HELP_TEXT = """
Tank-G MIDI SysEx CLI Controller
----------------------------------
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
    python tankg.py raw F0 00 ...       # envia bytes SysEx crus (incluir F0 e F7)
"""


def find_tankg_port() -> str | None:
    outputs = mido.get_output_names()
    for p in outputs:
        if any(term in p.lower() for term in ("tank", "mvave", "cuvave", "m-vave")):
            return p
    for p in outputs:
        if "microsoft" not in p.lower() and ("usb-midi" in p.lower() or "midi" in p.lower()):
            return p
    return None


def send_sysex_cli(port_name: str, data_bytes: List[int]):
    assert data_bytes[0] == 0xF0 and data_bytes[-1] == 0xF7, "SysEx precisa começar com F0 e terminar com F7"
    inner = data_bytes[1:-1]
    msg = mido.Message("sysex", data=inner)
    try:
        with mido.open_output(port_name) as port:
            port.send(msg)
        print(f"Enviado com sucesso para '{port_name}': {' '.join(f'{b:02X}' for b in data_bytes)}")
    except Exception as e:
        print(f"\n[ERRO] Falha ao abrir a porta MIDI '{port_name}': {e}")
        print("Dica: No Windows, a porta MIDI é de acesso exclusivo. Certifique-se de FECHAR:")
        print("  1. O software oficial da M-Vave (m_efcs.exe)")
        print("  2. Qualquer DAW (Reaper, FL Studio, etc.) disputando a porta.\n")


def run_cli(args: List[str] = None):
    if args is None:
        args = sys.argv[1:]

    if not args:
        print(HELP_TEXT)
        return

    cmd = args[0].lower()

    if cmd == "list":
        print("Portas MIDI de SAIDA disponíveis:")
        for name in mido.get_output_names():
            print(f"  - {name}")
        print("\nPortas MIDI de ENTRADA disponíveis:")
        for name in mido.get_input_names():
            print(f"  - {name}")
        return

    state_path = Path.cwd() / "state.json"
    state = PedalState.load_from_file(state_path)

    if cmd == "status":
        print("=== Estado Atual da Tank-G (Salvo localmente) ===")
        print(f"  Amp Type : [{state.type}] {AMP_NAMES.get(state.type, 'Desconhecido')}")
        print(f"  Gain     : {state.gain}")
        print(f"  Treble   : {state.treble}")
        print(f"  Middle   : {state.middle}")
        print(f"  Bass     : {state.bass}")
        print(f"  Volume   : {state.volume}")
        mtype, mval = state.mod_info
        print(f"  MOD FX   : {mtype.capitalize()} (Mix/Depth: {mval}/40) (raw: {state.mod_fx})")
        print(f"  MOD Speed: {state.mod_speed}/100")
        dtype, dval = state.dly_info
        print(f"  DLY MIX  : {dtype.capitalize()} Delay (Mix: {dval}/40) (raw: {state.dly_mix})")
        print(f"  DLY Time : {state.dly_time}/100")
        rtype, rval = state.rev_info
        print(f"  REV Decay: {rtype.capitalize()} Reverb (Decay: {rval}/40) (raw: {state.rev_decay})")
        print(f"  REV Mix  : {state.rev_mix}/100")
        print(f"  Preset   : [{state.preset}]")
        print(f"  IR CAB   : [{state.cab}] {CAB_NAMES.get(state.cab, 'Desconhecido')}")
        print(f"  Gate     : {state.gate}")
        return

    # Comandos informativos que não exigem conexão de hardware
    if cmd == "cab" and len(args) > 1 and args[1].lower() == "list":
        print("Slots de IR CAB disponíveis:")
        for slot, name in CAB_NAMES.items():
            print(f"  [{slot}] {name}")
        return

    if cmd in ("type", "amp-type") and len(args) > 1 and args[1].lower() == "list":
        print("Modelos de Amplificador disponíveis:")
        for slot, name in AMP_NAMES.items():
            print(f"  [{slot}] {name}")
        return

    if (cmd in ("preset", "prst") and len(args) > 1 and args[1].lower() == "list") or (cmd == "preset" and len(args) == 1):
        print("Presets disponíveis na Tank-G (9 Bancos x 4 Slots = 36 Presets):")
        for b in range(1, 10):
            slots = [f"{b}{s} (#{((b-1)*4 + i + 1):02d})" for i, s in enumerate("ABCD")]
            print(f"  Banco {b}: " + "  ".join(slots))
        return

    port_name = find_tankg_port()
    if not port_name:
        print("Não encontrei a porta automaticamente. Rode 'python tankg.py list'")
        return

    print(f"Usando porta: {port_name}")

    if cmd == "gate":
        if len(args) < 2:
            print("Uso: python tankg.py gate <0-100>")
            return
        val = int(args[1])
        state.gate = val
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_gate_sysex(val))

    elif cmd == "cab":
        if len(args) < 2:
            print("Uso: python tankg.py cab <0-8> | python tankg.py cab list")
            return
        if args[1].lower() == "list":
            print("Slots de IR CAB disponíveis:")
            for slot, name in CAB_NAMES.items():
                print(f"  [{slot}] {name}")
            return
        val = int(args[1])
        state.cab = val
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_cab_sysex(val))

    elif cmd in ("type", "amp-type"):
        if len(args) < 2:
            print("Uso: python tankg.py type <1-9> | python tankg.py type list")
            return
        if args[1].lower() == "list":
            print("Modelos de Amplificador disponíveis:")
            for slot, name in AMP_NAMES.items():
                print(f"  [{slot}] {name}")
            return
        val = int(args[1])
        state.type = val
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("gain", "treble", "middle", "mid", "bass", "volume", "vol"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        val = int(args[1])
        field = "middle" if cmd == "mid" else ("volume" if cmd == "vol" else cmd)
        setattr(state, field, val)
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("chorus", "phaser", "tremolo"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        val = int(args[1])
        state.set_mod_effect(cmd, val)
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("speed", "mod-speed"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        val = int(args[1])
        state.mod_speed = val
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("analog", "delay-analog", "dly-analog", "tape", "delay-tape", "dly-tape", "dual", "delay-dual", "dly-dual"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        val = int(args[1])
        dtype = "analog" if "analog" in cmd else ("tape" if "tape" in cmd else "dual")
        state.set_delay_effect(dtype, val)
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("time", "delay-time", "dly-time"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        val = int(args[1])
        state.dly_time = val
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("room", "reverb-room", "rev-room", "spring", "reverb-spring", "rev-spring", "cloud", "reverb-cloud", "rev-cloud"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <1-40>")
            return
        val = int(args[1])
        rtype = "room" if "room" in cmd else ("spring" if "spring" in cmd else "cloud")
        state.set_reverb_effect(rtype, val)
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("rev-mix", "reverb-mix", "rvb-mix"):
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <0-100>")
            return
        val = int(args[1])
        state.rev_mix = val
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_param_sysex(state))

    elif cmd in ("preset", "prst") or (len(cmd) == 2 and cmd[0].isdigit() and cmd[1] in "abcd"):
        target = cmd if (len(cmd) == 2 and cmd[0].isdigit() and cmd[1] in "abcd") else (args[1] if len(args) > 1 else "")
        if not target:
            print("Uso: python tankg.py preset <1A-9D | 1-36> | python tankg.py preset list")
            return
        if target.lower() == "list":
            print("Presets disponíveis na Tank-G (9 Bancos x 4 Slots = 36 Presets):")
            for b in range(1, 10):
                slots = [f"{b}{s} (#{((b-1)*4 + i + 1):02d})" for i, s in enumerate("ABCD")]
                print(f"  Banco {b}: " + "  ".join(slots))
            return
        preset_id = parse_preset_name(target)
        preset_name = get_preset_name(preset_id)
        state.preset = preset_name
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_preset_switch_sysex(preset_id))

    elif cmd in ("save", "salvar"):
        target = args[1] if len(args) > 1 else state.preset
        preset_id = parse_preset_name(target)
        preset_name = get_preset_name(preset_id)
        state.preset = preset_name
        state.save_to_file(state_path)
        print(f"Gravando estado atual na EEPROM do Preset [{preset_name}] (#{preset_id + 1}/36)...")
        send_sysex_cli(port_name, build_eeprom_save_sysex(preset_id, state))
        send_sysex_cli(port_name, build_eeprom_flush_sysex())
        send_sysex_cli(port_name, build_preset_switch_sysex(preset_id))
        print(f"Preset [{preset_name}] salvo com sucesso na pedaleira!")

    elif cmd in MODULES:
        if len(args) < 2:
            print(f"Uso: python tankg.py {cmd} <on|off>")
            return
        on = args[1].lower() in ("on", "1")
        setattr(state, f"{cmd}_on", 1 if on else 0)
        state.save_to_file(state_path)
        send_sysex_cli(port_name, build_module_bypass_sysex(cmd, on))

    elif cmd == "raw":
        hex_bytes = [int(b, 16) for b in args[1:]]
        send_sysex_cli(port_name, hex_bytes)

    else:
        print(HELP_TEXT)
