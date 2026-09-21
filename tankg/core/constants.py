"""
Definições de constantes, modelos de amplificador, IR Cabs e mapeamento de setores da Tank-G.
"""

# Modelos de Pré-amplificador (AMP TYPE 1 a 9)
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

# Nomes curtos para exibição limpa em UIs compactas
AMP_SHORT_NAMES = {
    1: "AC30 Clean",
    2: "'65 Twin",
    3: "Shiva OD",
    4: "JTM45 OD",
    5: "Plexi 100",
    6: "JCM800",
    7: "5150 Lead",
    8: "Powerball",
    9: "Rectifier",
}

# Módulos com chave de Bypass (Comando 0x49, sub-registro 0x11)
MODULES = {
    "amp": 0x00,
    "mod": 0x01,
    "dly": 0x02,
    "rev": 0x03,
}

MODULE_NAMES = {v: k for k, v in MODULES.items()}

# Simulações de Gabinete (IR CAB) de fábrica (0 = Bypass, 1 a 8 = Cabs)
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

# Setores de Efeitos (Sub-divisão do knob físico em 3 zonas de 1 a 40)
# Cada setor ocupa:
#   Setor 1: raw 0 a 39    (val 1 a 40 -> raw = val - 1)
#   Setor 2: raw 44 a 83   (val 1 a 40 -> raw = 43 + val)
#   Setor 3: raw 88 a 127  (val 1 a 40 -> raw = 87 + val)

MOD_SECTORS = {
    "chorus": {"label": "Chorus", "param_name": "Mix", "offset": -1, "min_raw": 0, "max_raw": 39},
    "phaser": {"label": "Phaser", "param_name": "Depth", "offset": 43, "min_raw": 44, "max_raw": 83},
    "tremolo": {"label": "Tremolo", "param_name": "Mix", "offset": 87, "min_raw": 88, "max_raw": 127},
}

DLY_SECTORS = {
    "analog": {"label": "Analog Delay", "param_name": "Mix", "offset": -1, "min_raw": 0, "max_raw": 39},
    "tape": {"label": "Tape Delay", "param_name": "Mix", "offset": 43, "min_raw": 44, "max_raw": 83},
    "dual": {"label": "Dual Delay", "param_name": "Mix", "offset": 87, "min_raw": 88, "max_raw": 127},
}

REV_SECTORS = {
    "room": {"label": "Room Reverb", "param_name": "Decay", "offset": -1, "min_raw": 0, "max_raw": 39},
    "spring": {"label": "Spring Reverb", "param_name": "Decay", "offset": 43, "min_raw": 44, "max_raw": 83},
    "cloud": {"label": "Cloud Reverb", "param_name": "Decay", "offset": 87, "min_raw": 88, "max_raw": 127},
}

DEFAULT_STATE_DICT = {
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
