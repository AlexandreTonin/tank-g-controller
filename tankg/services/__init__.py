"""
Serviços de comunicação MIDI e codec SysEx da Tank-G.
"""

from .param_map import pack_7bit, unpack_7bit, calc_eeprom_offset
from .sysex_codec import (
    calc_14bit_checksum,
    build_gate_sysex,
    build_cab_sysex,
    build_module_bypass_sysex,
    build_preset_switch_sysex,
    build_preset_param_sysex,
    build_eeprom_save_sysex,
    build_eeprom_flush_sysex,
    parse_sysex,
)
from .midi_service import MidiService
from .preset_validator import PresetValidator, OutOfDomainPromptError
from .gemini_preset_service import GeminiPresetService, get_active_api_key, save_api_key

__all__ = [
    "pack_7bit",
    "unpack_7bit",
    "calc_eeprom_offset",
    "calc_14bit_checksum",
    "build_gate_sysex",
    "build_cab_sysex",
    "build_module_bypass_sysex",
    "build_preset_switch_sysex",
    "build_preset_param_sysex",
    "build_eeprom_save_sysex",
    "build_eeprom_flush_sysex",
    "parse_sysex",
    "MidiService",
    "PresetValidator",
    "OutOfDomainPromptError",
    "GeminiPresetService",
    "get_active_api_key",
    "save_api_key",
]
