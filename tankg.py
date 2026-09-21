"""
Tank-G MIDI SysEx CLI & Script Entry Point
------------------------------------------
Fornece 100% de compatibilidade retroativa com a interface de linha de comando
e scripts que importavam funções diretamente de tankg.py.

Uso:
    python tankg.py                  # Inicia a interface gráfica PySide6
    python tankg.py list             # Lista portas MIDI disponíveis
    python tankg.py status           # Mostra o status atual de todos os parâmetros
    python tankg.py preset 3B        # Seleciona preset 3B
    python tankg.py save 3B          # Grava parâmetros atuais na EEPROM
    ... (todos os comandos CLI anteriores continuam funcionando)
"""

import sys
from pathlib import Path

from tankg.core.constants import AMP_NAMES, CAB_NAMES, MODULES, DEFAULT_STATE_DICT as DEFAULT_STATE
from tankg.model.pedal_state import PedalState
from tankg.model.preset import parse_preset_name, get_preset_name
from tankg.services.sysex_codec import (
    build_gate_sysex as make_gate_sysex,
    build_cab_sysex as make_cab_sysex,
    build_module_bypass_sysex as make_module_sysex,
    build_preset_switch_sysex as make_preset_switch_sysex,
    build_preset_param_sysex,
    build_eeprom_save_sysex,
    build_eeprom_flush_sysex,
)
from tankg.cli.cli_app import run_cli, find_tankg_port, send_sysex_cli as send_sysex


def load_state() -> dict:
    return PedalState.load_from_file(Path.cwd() / "state.json").to_dict()


def save_state(state_dict: dict):
    PedalState.from_dict(state_dict).save_to_file(Path.cwd() / "state.json")


def make_preset_sysex(state: dict) -> list[int]:
    pedal_state = PedalState.from_dict(state)
    return build_preset_param_sysex(pedal_state)


def make_save_preset_sysex(preset_id: int, state: dict) -> list[int]:
    pedal_state = PedalState.from_dict(state)
    return build_eeprom_save_sysex(preset_id, pedal_state)


def save_preset_to_pedal(port_name: str, preset_id: int, state: dict):
    preset_name = get_preset_name(preset_id)
    print(f"Gravando estado atual na EEPROM do Preset [{preset_name}] (#{preset_id + 1}/36)...")
    sysex_save = make_save_preset_sysex(preset_id, state)
    send_sysex(port_name, sysex_save)
    send_sysex(port_name, build_eeprom_flush_sysex())
    send_sysex(port_name, make_preset_switch_sysex(preset_id))
    print(f"Preset [{preset_name}] salvo com sucesso na pedaleira!")


def list_ports():
    run_cli(["list"])


def main():
    if len(sys.argv) > 1:
        run_cli(sys.argv[1:])
    else:
        # Se executado sem argumentos, abre a GUI moderna
        from main import main as run_gui
        run_gui()


if __name__ == "__main__":
    main()