"""
Validador defensivo e normalizador de parâmetros de timbres gerados pela IA.
Garante que nenhum valor saia dos limites físicos e do mapa de engenharia reversa da Tank-G.
"""

from typing import Union, Dict, Any, Tuple
from ..model.ai_preset import AIPresetResponse
from ..model.pedal_state import PedalState


class OutOfDomainPromptError(Exception):
    """Exceção levantada quando o prompt do usuário não é sobre timbres/guitarra."""
    def __init__(self, message: str = "Solicitação fora do escopo de timbres para guitarra."):
        super().__init__(message)
        self.message = message


class PresetValidator:
    """
    Validador e clamper rigoroso.
    Converte com segurança a resposta do Gemini em uma instância de PedalState.
    """

    @classmethod
    def validate_and_build(cls, data: Union[AIPresetResponse, Dict[str, Any]]) -> Tuple[PedalState, str, str]:
        """
        Valida a resposta da IA e retorna:
        (pedal_state, preset_name_suggestion, musical_explanation)

        Levanta OutOfDomainPromptError se o prompt foi rejeitado pela IA.
        """
        if isinstance(data, dict):
            # Se for dicionário bruto, valida com o modelo Pydantic
            ai_data = AIPresetResponse(**data)
        else:
            ai_data = data

        # 1. Checagem de Escopo / Domínio
        if not ai_data.is_audio_tone_request:
            refusal = ai_data.refusal_reason or (
                "Desculpe, eu sou um agente de IA especializado exclusivamente na construção de timbres e "
                "presets para a pedaleira M-Vave Tank-G. Por favor, faça um pedido descrevendo o timbre desejado, "
                "música, artista ou estilo musical."
            )
            raise OutOfDomainPromptError(refusal)

        # 2. Clamping Defensivo dos Parâmetros
        t = max(1, min(9, int(ai_data.amp_type)))
        g = max(0, min(100, int(ai_data.gain)))
        tr = max(0, min(100, int(ai_data.treble)))
        m = max(0, min(100, int(ai_data.middle)))
        b = max(0, min(100, int(ai_data.bass)))
        v = max(0, min(100, int(ai_data.volume)))
        amp_on = 1 if ai_data.amp_on else 0

        # Modulação
        m_type = ai_data.mod_type.lower() if ai_data.mod_type in ("chorus", "phaser", "tremolo") else "chorus"
        m_val = max(1, min(40, int(ai_data.mod_val)))
        m_spd = max(0, min(100, int(ai_data.mod_speed)))
        m_on = 1 if ai_data.mod_on else 0

        # Delay
        d_type = ai_data.dly_type.lower() if ai_data.dly_type in ("analog", "tape", "dual") else "analog"
        d_val = max(1, min(40, int(ai_data.dly_val)))
        d_time = max(0, min(100, int(ai_data.dly_time)))
        d_on = 1 if ai_data.dly_on else 0

        # Reverb
        r_type = ai_data.rev_type.lower() if ai_data.rev_type in ("room", "spring", "cloud") else "room"
        r_val = max(1, min(40, int(ai_data.rev_val)))
        r_mix = max(0, min(100, int(ai_data.rev_mix)))
        r_on = 1 if ai_data.rev_on else 0

        # Gate & Cab
        gate = max(0, min(100, int(ai_data.gate)))
        cab = max(0, min(8, int(ai_data.cab)))

        # 3. Constrói o PedalState seguro
        state = PedalState(
            type=t,
            gain=g,
            treble=tr,
            middle=m,
            bass=b,
            volume=v,
            amp_on=amp_on,
            mod_speed=m_spd,
            mod_on=m_on,
            dly_time=d_time,
            dly_on=d_on,
            rev_mix=r_mix,
            rev_on=r_on,
            gate=gate,
            cab=cab,
        )
        state.set_mod_effect(m_type, m_val)
        state.set_delay_effect(d_type, d_val)
        state.set_reverb_effect(r_type, r_val)

        suggestion = (ai_data.preset_name_suggestion or "AI Preset").strip()[:20]
        explanation = ai_data.musical_explanation or "Timbre gerado com sucesso para a Tank-G."

        return state, suggestion, explanation
