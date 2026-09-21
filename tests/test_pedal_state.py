"""
Testes automatizados para o Model PedalState e conversão de setores de efeitos e presets.
"""

import pytest

from tankg.model.pedal_state import PedalState
from tankg.model.preset import parse_preset_name, get_preset_name, list_all_presets


def test_pedal_state_defaults():
    st = PedalState()
    assert st.type == 1
    assert st.gain == 50
    assert st.amp_on == 1
    assert st.gate == 0
    assert st.cab == 1
    assert st.preset == "1A"


def test_mod_sector_conversions():
    st = PedalState()

    # Chorus 1 a 40 -> 0 a 39
    st.set_mod_effect("chorus", 1)
    assert st.mod_fx == 0
    assert st.mod_info == ("chorus", 1)

    st.set_mod_effect("chorus", 40)
    assert st.mod_fx == 39
    assert st.mod_info == ("chorus", 40)

    # Phaser 1 a 40 -> 44 a 83
    st.set_mod_effect("phaser", 1)
    assert st.mod_fx == 44
    assert st.mod_info == ("phaser", 1)

    st.set_mod_effect("phaser", 40)
    assert st.mod_fx == 83
    assert st.mod_info == ("phaser", 40)

    # Tremolo 1 a 40 -> 88 a 127
    st.set_mod_effect("tremolo", 1)
    assert st.mod_fx == 88
    assert st.mod_info == ("tremolo", 1)

    st.set_mod_effect("tremolo", 40)
    assert st.mod_fx == 127
    assert st.mod_info == ("tremolo", 40)


def test_delay_sector_conversions():
    st = PedalState()

    # Analog Delay 1 a 40 -> 0 a 39
    st.set_delay_effect("analog", 1)
    assert st.dly_mix == 0
    assert st.dly_info == ("analog", 1)

    # Tape Delay 1 a 40 -> 44 a 83
    st.set_delay_effect("tape", 20)
    assert st.dly_mix == 63
    assert st.dly_info == ("tape", 20)

    # Dual Delay 1 a 40 -> 88 a 127
    st.set_delay_effect("dual", 40)
    assert st.dly_mix == 127
    assert st.dly_info == ("dual", 40)


def test_reverb_sector_conversions():
    st = PedalState()

    # Room 1 a 40 -> 0 a 39
    st.set_reverb_effect("room", 10)
    assert st.rev_decay == 9
    assert st.rev_info == ("room", 10)

    # Spring 1 a 40 -> 44 a 83
    st.set_reverb_effect("spring", 15)
    assert st.rev_decay == 58
    assert st.rev_info == ("spring", 15)

    # Cloud 1 a 40 -> 88 a 127
    st.set_reverb_effect("cloud", 30)
    assert st.rev_decay == 117
    assert st.rev_info == ("cloud", 30)


def test_preset_names_and_parsing():
    all_presets = list_all_presets()
    assert len(all_presets) == 36

    # Testa 1A (ID 0)
    assert parse_preset_name("1A") == 0
    assert parse_preset_name("1a") == 0
    assert parse_preset_name("1") == 0
    assert get_preset_name(0) == "1A"

    # Testa 3B (ID 9)
    assert parse_preset_name("3B") == 9
    assert parse_preset_name("10") == 9
    assert get_preset_name(9) == "3B"

    # Testa 9D (ID 35)
    assert parse_preset_name("9D") == 35
    assert parse_preset_name("36") == 35
    assert get_preset_name(35) == "9D"


def test_dict_serialization():
    st = PedalState(gain=85, type=6, preset="4C")
    d = st.to_dict()
    assert d["gain"] == 85
    assert d["type"] == 6
    assert d["preset"] == "4C"

    restored = PedalState.from_dict(d)
    assert restored.gain == 85
    assert restored.type == 6
    assert restored.preset == "4C"
