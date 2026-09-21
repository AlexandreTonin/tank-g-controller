"""
Estado completo dos parâmetros da pedaleira M-Vave Tank-G.
Dataclass puro sem dependência de Qt ou MIDI.
"""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Tuple

from ..core.constants import DEFAULT_STATE_DICT, AMP_NAMES, CAB_NAMES


@dataclass
class PedalState:
    # Amplificador (AMP)
    type: int = 1        # 1 a 9 (Modelo de Amp)
    gain: int = 50       # 0 a 100
    treble: int = 50     # 0 a 100
    middle: int = 50     # 0 a 100
    bass: int = 50       # 0 a 100
    volume: int = 50     # 0 a 100
    amp_on: int = 1      # 1 = Ativo, 0 = Bypass

    # Modulação (MOD)
    mod_fx: int = 20     # Raw: 0..127 (Chorus: 0..39, Phaser: 44..83, Tremolo: 88..127)
    mod_speed: int = 50  # 0 a 100
    mod_on: int = 0      # 1 = Ativo, 0 = Bypass

    # Delay (DLY)
    dly_mix: int = 20    # Raw: 0..127 (Analog: 0..39, Tape: 44..83, Dual: 88..127)
    dly_time: int = 50   # 0 a 100
    dly_on: int = 0      # 1 = Ativo, 0 = Bypass

    # Reverb (REV)
    rev_decay: int = 20  # Raw: 0..127 (Room: 0..39, Spring: 44..83, Cloud: 88..127)
    rev_mix: int = 50    # 0 a 100
    rev_on: int = 1      # 1 = Ativo, 0 = Bypass

    # Utilitários (GATE / CAB / PRESET)
    gate: int = 0        # 0 a 100
    cab: int = 1         # 0 a 8 (0 = Bypass, 1..8 = Cabs)
    preset: str = "1A"   # "1A" a "9D"

    # --- Helpers de Modulação (MOD) ---
    @property
    def mod_info(self) -> Tuple[str, int]:
        """Retorna (tipo, nivel_1_a_40). Ex: ('chorus', 21)"""
        fx = self.mod_fx
        if 0 <= fx <= 39:
            return ("chorus", fx + 1)
        elif 44 <= fx <= 83:
            return ("phaser", fx - 43)
        elif 88 <= fx <= 127:
            return ("tremolo", fx - 87)
        return ("chorus", 1)

    def set_mod_effect(self, mod_type: str, level: int):
        """Ajusta o tipo de modulação e o nível (1 a 40)."""
        val = max(1, min(40, int(level)))
        t = mod_type.lower()
        if t == "chorus":
            self.mod_fx = val - 1
        elif t == "phaser":
            self.mod_fx = 43 + val
        elif t == "tremolo":
            self.mod_fx = 87 + val
        else:
            raise ValueError(f"Tipo de modulação desconhecido: '{mod_type}'")

    # --- Helpers de Delay (DLY) ---
    @property
    def dly_info(self) -> Tuple[str, int]:
        """Retorna (tipo, nivel_1_a_40). Ex: ('analog', 21)"""
        mix = self.dly_mix
        if 0 <= mix <= 39:
            return ("analog", mix + 1)
        elif 44 <= mix <= 83:
            return ("tape", mix - 43)
        elif 88 <= mix <= 127:
            return ("dual", mix - 87)
        return ("analog", 1)

    def set_delay_effect(self, dly_type: str, level: int):
        """Ajusta o tipo de delay e o nível de mix (1 a 40)."""
        val = max(1, min(40, int(level)))
        t = dly_type.lower()
        if t in ("analog", "dly-analog"):
            self.dly_mix = val - 1
        elif t in ("tape", "dly-tape"):
            self.dly_mix = 43 + val
        elif t in ("dual", "dly-dual"):
            self.dly_mix = 87 + val
        else:
            raise ValueError(f"Tipo de delay desconhecido: '{dly_type}'")

    # --- Helpers de Reverb (REV) ---
    @property
    def rev_info(self) -> Tuple[str, int]:
        """Retorna (tipo, nivel_1_a_40). Ex: ('room', 21)"""
        decay = self.rev_decay
        if 0 <= decay <= 39:
            return ("room", decay + 1)
        elif 44 <= decay <= 83:
            return ("spring", decay - 43)
        elif 88 <= decay <= 127:
            return ("cloud", decay - 87)
        return ("room", 1)

    def set_reverb_effect(self, rev_type: str, level: int):
        """Ajusta o tipo de reverb e o nível de decay (1 a 40)."""
        val = max(1, min(40, int(level)))
        t = rev_type.lower()
        if t in ("room", "rev-room"):
            self.rev_decay = val - 1
        elif t in ("spring", "rev-spring"):
            self.rev_decay = 43 + val
        elif t in ("cloud", "rev-cloud"):
            self.rev_decay = 87 + val
        else:
            raise ValueError(f"Tipo de reverb desconhecido: '{rev_type}'")

    # --- Descrições Textuais Amigáveis ---
    @property
    def amp_name(self) -> str:
        return AMP_NAMES.get(self.type, f"Amp #{self.type}")

    @property
    def cab_name(self) -> str:
        return CAB_NAMES.get(self.cab, f"Cab #{self.cab}")

    # --- Serialização / Persistência ---
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PedalState":
        merged = {**DEFAULT_STATE_DICT, **(data or {})}
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: merged[k] for k in valid_keys if k in merged}
        return cls(**filtered)

    @classmethod
    def load_from_file(cls, path: Path | str) -> "PedalState":
        p = Path(path)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return cls.from_dict(json.load(f))
            except Exception:
                pass
        return cls()

    def save_to_file(self, path: Path | str):
        p = Path(path)
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception:
            pass
