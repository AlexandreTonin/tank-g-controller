"""
Manipulação de Presets da Tank-G (9 Bancos x 4 Slots = 36 Presets).
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Preset:
    id: int          # 0 a 35
    name: str        # "1A" a "9D"
    bank: int        # 1 a 9
    slot: str        # "A", "B", "C", "D"
    index_1based: int # 1 a 36

    @classmethod
    def from_id(cls, preset_id: int) -> "Preset":
        if not (0 <= preset_id <= 35):
            raise ValueError(f"ID do preset deve estar entre 0 e 35. Recebido: {preset_id}")
        bank = (preset_id // 4) + 1
        slot = "ABCD"[preset_id % 4]
        name = f"{bank}{slot}"
        return cls(
            id=preset_id,
            name=name,
            bank=bank,
            slot=slot,
            index_1based=preset_id + 1
        )

    @classmethod
    def from_str(cls, text: str) -> "Preset":
        preset_id = parse_preset_name(text)
        return cls.from_id(preset_id)


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
    raise ValueError(f"Preset inválido '{preset_str}'. Use formato '1A' a '9D' ou número de 1 a 36.")


def get_preset_name(preset_id: int) -> str:
    """Retorna o nome amigável do preset (ex: '3B') a partir do ID (0 a 35)."""
    if not (0 <= preset_id <= 35):
        raise ValueError(f"ID do preset deve estar entre 0 e 35. Recebido: {preset_id}")
    bank = (preset_id // 4) + 1
    slot = "ABCD"[preset_id % 4]
    return f"{bank}{slot}"


def list_all_presets() -> List[Preset]:
    """Retorna a lista completa com todos os 36 presets."""
    return [Preset.from_id(i) for i in range(36)]
