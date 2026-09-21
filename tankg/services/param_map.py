"""
Mapeamento de parâmetros e empacotamento de bits para a Tank-G.
Converte entre arrays de 8 bits normais e a representação de 7 bits do protocolo MIDI SysEx.
"""

from typing import List


def pack_7bit(fields_8bit: List[int], num_7bit_bytes: int) -> List[int]:
    """
    Empacota uma lista de inteiros de 8 bits em uma sequência de bytes de 7 bits (MIDI safe).
    Utilizado tanto no comando 0x31 (15 bytes de 7-bit) quanto no 0x69 (24 bytes de 7-bit).
    """
    big_val = 0
    for i, val in enumerate(fields_8bit):
        big_val |= (int(val) & 0xFF) << (8 * i)

    return [(big_val >> (7 * i)) & 0x7F for i in range(num_7bit_bytes)]


def unpack_7bit(packed_7bit: List[int], num_8bit_bytes: int) -> List[int]:
    """
    Desempacota uma sequência de bytes de 7 bits em inteiros originais de 8 bits.
    """
    big_val = 0
    for i, b in enumerate(packed_7bit):
        big_val |= (int(b) & 0x7F) << (7 * i)

    return [(big_val >> (8 * i)) & 0xFF for i in range(num_8bit_bytes)]


def calc_eeprom_offset(preset_id: int) -> int:
    """
    Calcula o endereço de offset na memória EEPROM da pedaleira para o preset especificado.
    Fórmula: preset_id * 21 + 2
    """
    if not (0 <= preset_id <= 35):
        raise ValueError(f"Preset ID fora dos limites (0-35): {preset_id}")
    return preset_id * 21 + 2
