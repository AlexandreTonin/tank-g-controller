"""
Testes automatizados do codec SysEx da Tank-G (offline, sem necessidade de hardware conectado).
Valida fórmulas de checksum e empacotamento de bits contra capturas reais do Wireshark.
"""

import pytest

from tankg.model.pedal_state import PedalState
from tankg.model.preset import parse_preset_name, get_preset_name
from tankg.services.param_map import pack_7bit, unpack_7bit, calc_eeprom_offset
from tankg.services.sysex_codec import (
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


def test_14bit_checksum_math():
    # Teste de divisão 14-bit
    ck1, ck2 = calc_14bit_checksum(95)
    assert ck1 == 95
    assert ck2 == 0

    # 251 = 0xFB = 0b11111011 -> ck1 = 0x7B (123), ck2 = 0x01 (1)
    ck1, ck2 = calc_14bit_checksum(251)
    assert ck1 == 0x7B
    assert ck2 == 0x01


def test_gate_sysex_golden_matches():
    # Gate 0
    pkt0 = build_gate_sysex(0)
    assert len(pkt0) == 36
    assert pkt0[0] == 0xF0 and pkt0[-1] == 0xF7
    assert pkt0[17] == 0       # Valor
    assert pkt0[33] == 0x5F    # Checksum 1
    assert pkt0[34] == 0x00    # Checksum 2

    # Gate 100
    pkt100 = build_gate_sysex(100)
    assert len(pkt100) == 36
    assert pkt100[17] == 100   # Valor
    assert pkt100[33] == 0x7B   # Checksum 1
    assert pkt100[34] == 0x01   # Checksum 2


def test_module_bypass_golden_matches():
    # AMP OFF (mod_id 0, st 0) -> ck1 = 0x54, ck2 = 0x03
    p_amp_off = build_module_bypass_sysex("amp", False)
    assert p_amp_off[9] == 0x00
    assert p_amp_off[17] == 0x00
    assert p_amp_off[18] == 0x54
    assert p_amp_off[19] == 0x03

    # AMP ON (mod_id 0, st 1) -> ck1 = 0x52, ck2 = 0x03
    p_amp_on = build_module_bypass_sysex("amp", True)
    assert p_amp_on[17] == 0x01
    assert p_amp_on[18] == 0x52

    # MOD ON (mod_id 1, st 1) -> ck1 = 0x50, ck2 = 0x03
    p_mod_on = build_module_bypass_sysex("mod", True)
    assert p_mod_on[9] == 0x01
    assert p_mod_on[18] == 0x50

    # DLY ON (mod_id 2, st 1) -> ck1 = 0x4E, ck2 = 0x03
    p_dly_on = build_module_bypass_sysex("dly", True)
    assert p_dly_on[9] == 0x02
    assert p_dly_on[18] == 0x4E

    # REV ON (mod_id 3, st 1) -> ck1 = 0x4C, ck2 = 0x03
    p_rev_on = build_module_bypass_sysex("rev", True)
    assert p_rev_on[9] == 0x03
    assert p_rev_on[18] == 0x4C


def test_preset_switch_sysex():
    # Preset 1A (ID 0) -> ck = 50 -> ck1 = 50 (0x32), ck2 = 0
    p1a = build_preset_switch_sysex(0)
    assert p1a[9] == 0
    assert p1a[18] == 0x32
    assert p1a[19] == 0x00

    # Preset 3B (ID 9) -> ck = 50 - 18 = 32 (0x20)
    p3b = build_preset_switch_sysex(9)
    assert p3b[9] == 9
    assert p3b[18] == 0x20
    assert p3b[19] == 0x00

    # Preset 3C (ID 10) -> ck = 50 - 20 = 30 (0x1E)
    p3c = build_preset_switch_sysex(10)
    assert p3c[9] == 10
    assert p3c[18] == 0x1E
    assert p3c[19] == 0x00


def test_cab_sysex():
    # Cab 0 (Bypass) -> ck1 = 98 (0x62)
    c0 = build_cab_sysex(0)
    assert c0[33] == 0x62
    assert c0[34] == 0x00

    # Cab 1 (VHT Deliverance) -> ck1 = 97 (0x61)
    c1 = build_cab_sysex(1)
    assert c1[33] == 0x61
    assert c1[34] == 0x00

    # Cab 8 (Diezel) -> ck1 = 90 (0x5A)
    c8 = build_cab_sysex(8)
    assert c8[33] == 0x5A
    assert c8[34] == 0x00


def test_eeprom_offset_calculation():
    # Preset 1A (ID 0) -> offset 2
    assert calc_eeprom_offset(0) == 2
    # Preset 3B (ID 9) -> offset 9 * 21 + 2 = 191
    assert calc_eeprom_offset(9) == 191
    # Preset 3C (ID 10) -> offset 10 * 21 + 2 = 212
    assert calc_eeprom_offset(10) == 212


def test_eeprom_save_sysex_length_and_structure():
    state = PedalState()
    pkt = build_eeprom_save_sysex(9, state)
    assert len(pkt) == 44
    assert pkt[0] == 0xF0
    assert pkt[4] == 0x69   # Comando gravação EEPROM
    assert pkt[-1] == 0xF7


def test_preset_realtime_param_sysex():
    state = PedalState(
        type=1, gain=50, treble=50, middle=50, bass=50, volume=50,
        mod_fx=20, mod_speed=50, dly_mix=20, dly_time=50, rev_decay=20, rev_mix=50
    )
    pkt = build_preset_param_sysex(state)
    assert len(pkt) == 36
    assert pkt[0] == 0xF0
    assert pkt[4] == 0x31   # Comando preset tempo real
    assert pkt[-1] == 0xF7

    # Testa checksum
    # params_sum = 1 + 50*5 + 20 + 50 + 20 + 50 + 20 + 50 = 461
    # ck = (211 - 461) % 256 = (-250) % 256 = 6
    ck1 = pkt[-3]
    ck2 = pkt[-2]
    total_ck = ck1 | (ck2 << 7)
    assert total_ck == 6


def test_bit_packing_roundtrip():
    # Testa integridade da conversão 8-bit <-> 7-bit MIDI
    original = [1, 50, 75, 100, 20, 80, 127, 255]
    packed = pack_7bit(original, 10)
    unpacked = unpack_7bit(packed, len(original))
    assert unpacked == original


def test_parse_sysex_incoming():
    # Mensagem de troca de preset recebida (ex: 3B -> ID 9)
    p3b = build_preset_switch_sysex(9)
    res = parse_sysex(p3b)
    assert res is not None
    assert res["type"] == "preset_switch"
    assert res["preset_id"] == 9

    # Mensagem de bypass recebida (ex: MOD ON)
    pmod = build_module_bypass_sysex("mod", True)
    res_mod = parse_sysex(pmod)
    assert res_mod is not None
    assert res_mod["type"] == "module_bypass"
    assert res_mod["module_id"] == 1
    assert res_mod["state"] is True
