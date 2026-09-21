"""
Modelos de dados puros para o estado da pedaleira e presets.
"""

from .preset import Preset, parse_preset_name, get_preset_name, list_all_presets
from .pedal_state import PedalState

__all__ = [
    "Preset",
    "parse_preset_name",
    "get_preset_name",
    "list_all_presets",
    "PedalState",
]
