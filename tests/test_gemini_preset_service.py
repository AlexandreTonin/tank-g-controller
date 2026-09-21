"""
Testes automatizados para o GeminiPresetService e PresetValidator (100% offline com mocks).
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from tankg.model.ai_preset import AIPresetResponse
from tankg.model.pedal_state import PedalState
from tankg.services.preset_validator import PresetValidator, OutOfDomainPromptError
from tankg.services.gemini_preset_service import GeminiPresetService, get_active_api_key, save_api_key


def test_validator_valid_tone():
    # Simula resposta válida de timbre para solo estilo Dani California
    ai_data = AIPresetResponse(
        is_audio_tone_request=True,
        preset_name_suggestion="Dani Solo",
        musical_explanation="Fuzz/Drive encorpado com Marshall JCM800 e Tape Delay",
        amp_type=6,
        gain=75,
        treble=70,
        middle=65,
        bass=55,
        volume=60,
        amp_on=True,
        mod_type="chorus",
        mod_val=15,
        mod_speed=40,
        mod_on=False,
        dly_type="tape",
        dly_val=25,
        dly_time=48,
        dly_on=True,
        rev_type="room",
        rev_val=18,
        rev_mix=35,
        rev_on=True,
        gate=25,
        cab=7
    )

    state, name, explanation = PresetValidator.validate_and_build(ai_data)

    assert name == "Dani Solo"
    assert "Fuzz/Drive" in explanation
    assert state.type == 6
    assert state.gain == 75
    assert state.amp_on == 1
    assert state.dly_on == 1
    # Tape delay setor 2: 43 + 25 = 68
    assert state.dly_mix == 68
    assert state.dly_info == ("tape", 25)
    assert state.cab == 7
    assert state.gate == 25


def test_validator_defensive_clamping():
    # Envia valores que ultrapassam os limites físicos do pedal
    ai_data = AIPresetResponse(
        is_audio_tone_request=True,
        preset_name_suggestion="Extreme Clamped",
        musical_explanation="Teste de limites",
        amp_type=99,      # Deve clampar para 9
        gain=250,        # Deve clampar para 100
        treble=0,
        middle=50,
        bass=50,
        volume=100,
        amp_on=True,
        mod_type="chorus",
        mod_val=80,      # Deve clampar para 40
        mod_speed=150,   # Deve clampar para 100
        mod_on=True,
        dly_type="analog",
        dly_val=0,       # Deve clampar para 1
        dly_time=0,
        dly_on=False,
        rev_type="cloud",
        rev_val=50,      # Deve clampar para 40
        rev_mix=120,     # Deve clampar para 100
        rev_on=True,
        gate=150,        # Deve clampar para 100
        cab=15           # Deve clampar para 8
    )

    state, name, _ = PresetValidator.validate_and_build(ai_data)

    assert state.type == 9
    assert state.gain == 100
    assert state.mod_info == ("chorus", 40)
    assert state.mod_speed == 100
    assert state.dly_info == ("analog", 1)
    assert state.rev_info == ("cloud", 40)
    assert state.rev_mix == 100
    assert state.gate == 100
    assert state.cab == 8


def test_validator_out_of_domain_rejection():
    # Prompt fora do escopo rejeitado pela IA
    ai_data = AIPresetResponse(
        is_audio_tone_request=False,
        refusal_reason="Desculpe, sou especialista exclusivamente em timbres para a Tank-G.",
        preset_name_suggestion="N/A",
        musical_explanation=""
    )

    with pytest.raises(OutOfDomainPromptError) as exc_info:
        PresetValidator.validate_and_build(ai_data)

    assert "exclusivamente em timbres" in str(exc_info.value)


def test_gemini_service_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch("tankg.services.gemini_preset_service.load_saved_api_key", return_value=None):
        service = GeminiPresetService()
        with pytest.raises(ValueError) as exc_info:
            service.generate_preset("timbre de rock")
        assert "GEMINI_API_KEY" in str(exc_info.value)


def test_gemini_service_mocked_successful_call():
    mock_payload = {
        "is_audio_tone_request": True,
        "refusal_reason": None,
        "preset_name_suggestion": "Stairway Solo",
        "musical_explanation": "Overdrive com JTM45, médios quentes e reverb de mola",
        "amp_type": 4,
        "gain": 68,
        "treble": 60,
        "middle": 70,
        "bass": 50,
        "volume": 55,
        "amp_on": True,
        "mod_type": "chorus",
        "mod_val": 10,
        "mod_speed": 30,
        "mod_on": False,
        "dly_type": "tape",
        "dly_val": 20,
        "dly_time": 45,
        "dly_on": True,
        "rev_type": "spring",
        "rev_val": 25,
        "rev_mix": 40,
        "rev_on": True,
        "gate": 10,
        "cab": 7
    }

    mock_interaction = MagicMock()
    mock_interaction.output_text = json.dumps(mock_payload)

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction
        mock_client_cls.return_value = mock_client

        service = GeminiPresetService(api_key="test-api-key-123")
        state, name, exp = service.generate_preset("solo de Stairway to Heaven")

        assert name == "Stairway Solo"
        assert state.type == 4
        assert state.gain == 68
        assert state.rev_info == ("spring", 25)
        assert mock_client.interactions.create.called


def test_gemini_service_mocked_out_of_domain():
    mock_payload = {
        "is_audio_tone_request": False,
        "refusal_reason": "Não posso responder sobre culinária, apenas sobre timbres para guitarra.",
        "preset_name_suggestion": "",
        "musical_explanation": ""
    }

    mock_interaction = MagicMock()
    mock_interaction.output_text = json.dumps(mock_payload)

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction
        mock_client_cls.return_value = mock_client

        service = GeminiPresetService(api_key="test-api-key-123")
        with pytest.raises(OutOfDomainPromptError) as exc_info:
            service.generate_preset("qual a melhor receita de bolo?")

        assert "Não posso responder sobre culinária" in str(exc_info.value)
