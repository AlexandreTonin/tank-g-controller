"""
Modelos de dados estruturados para presets gerados por Inteligência Artificial (Gemini API).
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AIPresetResponse(BaseModel):
    is_audio_tone_request: bool = Field(
        description="True se o prompt for uma solicitação válida de timbre/som para guitarra. False se for assunto fora de escopo."
    )
    refusal_reason: Optional[str] = Field(
        default=None,
        description="Explicação educada caso a solicitação não seja sobre timbres ou música."
    )
    preset_name_suggestion: str = Field(
        default="AI Preset",
        description="Nome curto e marcante para o preset (ex: 'Dani Lead', 'JCM Rock', 'Warm Clean')."
    )
    musical_explanation: str = Field(
        default="",
        description="Explicação técnica/musical das decisões tomadas (escolha de amp, EQ, saturação, efeitos e captador sugerido)."
    )

    # Amplificador (AMP)
    amp_type: int = Field(
        default=1,
        description="Modelo de Amp (1 a 9): 1=VOX AC30 Clean, 2='65 Twin Clean, 3=Bogner Shiva OD, 4=JTM45 OD, 5=Plexi 100 Rock, 6=JCM800 Hard Rock, 7=5150 Lead, 8=Powerball Modern, 9=Dual Rectifier Metal"
    )
    gain: int = Field(default=50, description="Ganho de entrada do amplificador (0 a 100)")
    treble: int = Field(default=50, description="Agudos (0 a 100)")
    middle: int = Field(default=50, description="Médios (0 a 100)")
    bass: int = Field(default=50, description="Graves (0 a 100)")
    volume: int = Field(default=50, description="Volume do amplificador (0 a 100)")
    amp_on: bool = Field(default=True, description="True para módulo AMP ativo, False para bypass")

    # Modulação (MOD)
    mod_type: str = Field(default="chorus", description="Tipo de modulação: chorus, phaser ou tremolo")
    mod_val: int = Field(default=20, description="Nível/Mix/Depth da modulação no setor (1 a 40)")
    mod_speed: int = Field(default=50, description="Velocidade da modulação (0 a 100)")
    mod_on: bool = Field(default=False, description="True para módulo MOD ativo, False para bypass")

    # Delay (DLY)
    dly_type: str = Field(default="analog", description="Tipo de delay: analog, tape ou dual")
    dly_val: int = Field(default=20, description="Mix do delay no sinal (1 a 40)")
    dly_time: int = Field(default=50, description="Tempo / repetições do delay (0 a 100)")
    dly_on: bool = Field(default=False, description="True para módulo DELAY ativo, False para bypass")

    # Reverb (REV)
    rev_type: str = Field(default="room", description="Tipo de reverb: room, spring ou cloud")
    rev_val: int = Field(default=20, description="Decay / ambiência do reverb (1 a 40)")
    rev_mix: int = Field(default=50, description="Mistura do reverb no sinal (0 a 100)")
    rev_on: bool = Field(default=True, description="True para módulo REVERB ativo, False para bypass")

    # Dinâmica & Gabinete
    gate: int = Field(default=0, description="Noise Gate (0 a 100). Usar valores moderados/altos para alto ganho")
    cab: int = Field(default=1, description="Simulação de Gabinete IR (0 a 8): 0=Bypass, 1=VHT 4x12, 2=Sperimental 4x12, 3=Electrovoice 2x10, 4=Mesa 4x12, 5=Fender Champ 1x8, 6=Fender Pro Jr 1x10, 7=Marshall 1960 V30 4x12, 8=Diezel V30 4x12")
