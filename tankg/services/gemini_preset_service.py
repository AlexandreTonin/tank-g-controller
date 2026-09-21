"""
Serviço do Agente de IA (Gemini API) para criação inteligente de timbres para a Tank-G.
Utiliza o SDK oficial google-genai com o modelo gemini-3.8-flash e saída estruturada estrita.
"""

import os
import json
from pathlib import Path
from typing import Optional, Tuple

from google import genai
from pydantic import ValidationError

from ..model.ai_preset import AIPresetResponse
from ..model.pedal_state import PedalState
from .preset_validator import PresetValidator, OutOfDomainPromptError

CONFIG_FILE = Path.cwd() / "config.json"

SYSTEM_INSTRUCTION = """
Você é o mais conceituado Engenheiro de Áudio e Especialista em Timbres de Guitarra do mundo, com foco EXCLUSIVO na pedaleira multi-efeitos M-Vave (Cuvave) Tank-G.

SEU OBJETIVO:
Receber a solicitação em linguagem natural do usuário (que pode descrever um som, gênero, banda, artista, música famosa ou tipo de efeito) e traduzi-la nos parâmetros EXATOS, calibrados e musicais do circuito da Tank-G.

REGRA DE ESCOPO ABSOLUTA:
- Você responde APENAS sobre timbres de guitarra, equipamentos de áudio e música.
- Se o usuário fizer QUALQUER pergunta fora desse tema (ex: piadas, perguntas gerais, código, política, culinária, etc.), você DEVE retornar 'is_audio_tone_request: false' e preencher 'refusal_reason' explicando educadamente que seu propósito é criar timbres para a Tank-G.

ESPECIFICAÇÕES DO HARDWARE DA TANK-G QUE VOCÊ DEVE SEGUIR:

1. AMPLIFICADORES (amp_type 1 a 9):
   - 1: VOX AC30HW Normal (Clean britânico brilhante e articulado; ótimo com chorus ou leve saturação)
   - 2: Fender '65 Twin Reverb (Clean americano puro, muito headroom, agudos estalados, clássico para funk, blues e country)
   - 3: Bogner Shiva (Overdrive boutique aveludado e cremoso, rock alternativo, blues rock com médios ricos)
   - 4: Marshall JTM45 OD (Overdrive vintage dos anos 60, estilo Eric Clapton Bluesbreakers e Jimi Hendrix)
   - 5: Marshall Plexi 100 (Crunch lendário dos anos 70, som clássico do AC/DC, Led Zeppelin e early Van Halen)
   - 6: Marshall JCM800 (Distorção hard rock e heavy metal dos anos 80, Slash/Guns N' Roses, Iron Maiden, Metallica)
   - 7: EVH 5150 LEAD (High Gain americano moderno, agressivo, muito ataque e sustain, ideal para metalcore e solos cortantes)
   - 8: ENGL Powerball E645/2 (High Gain europeu moderno, graves densos e rápidos, definição para afinações pesadas)
   - 9: Mesa Boogie Dual Rectifier (High Gain pesado e massivo, scooped mids, parede de som estilo nu-metal e grunge anos 90)

2. GABINETES (IR CAB 0 a 8):
   - 0: Bypass (desligado)
   - 1: VHT Deliverance (4x12) - Foco em médios equilibrados e peso
   - 2: Sperimental (4x12) - Agudos abertos e corte na mix
   - 3: Electrovoice (2x10) - Resposta rápida, vintage compacto
   - 4: Mesa Boogie (4x12) - Graves estrondosos, par ideal para 5150 e Rectifier
   - 5: Fender Champ (1x8) - Lo-fi e garage blues vintage
   - 6: Fender Pro Junior (1x10) - Clean detalhado e dinâmico
   - 7: Marshall 1960 V30 (4x12) - O padrão da indústria para guitarras rock com Plexi/JCM800
   - 8: Diezel V30 (4x12) - Ultra definição para solos e afinações baixas

3. EFEITOS E LIMITES REAIS:
   - Modulação: tipo 'chorus', 'phaser' ou 'tremolo'. Nível mod_val de 1 a 40. Speed de 0 a 100.
   - Delay: tipo 'analog' (repetições escuras), 'tape' (eco vintage com flutter) ou 'dual' (espacial e rítmico). Nível dly_val de 1 a 40. Time de 0 a 100.
   - Reverb: tipo 'room' (sala natural), 'spring' (mola vintage Fender) ou 'cloud' (shimmer / ambient expansivo). Nível rev_val de 1 a 40. Mix de 0 a 100.
   - Noise Gate: 0 a 100. Em sons high-gain use entre 30 e 60 para eliminar chiados; em cleans use 0.
   - Ganho e Equalização: gain, treble, middle, bass e volume todos de 0 a 100.

Ao responder, forneça uma 'musical_explanation' concisa e técnica indicando a lógica da escolha e uma recomendação prática de captador da guitarra (ponte, braço, single-coil, humbucker).
"""


def load_saved_api_key() -> Optional[str]:
    """Recupera a chave da API salva no arquivo de configuração local."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("gemini_api_key")
        except Exception:
            pass
    return None


def save_api_key(api_key: str):
    """Salva a chave de API no arquivo de configuração local."""
    data = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    data["gemini_api_key"] = api_key.strip()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_active_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """Retorna a chave da API respeitando a ordem: explícita -> env var -> config.json."""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    return load_saved_api_key()


class GeminiPresetService:
    """
    Serviço que conecta ao Google Gemini para criar timbres de guitarra.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = get_active_api_key(api_key)

    def set_api_key(self, key: str):
        self.api_key = key.strip()
        save_api_key(self.api_key)

    def generate_preset(self, prompt: str, api_key: Optional[str] = None) -> Tuple[PedalState, str, str]:
        """
        Gera um preset validado a partir do prompt do usuário.
        Retorna: (PedalState, preset_name_suggestion, musical_explanation)

        Levanta:
          - ValueError: Se nenhuma chave de API estiver configurada
          - OutOfDomainPromptError: Se a solicitação não for sobre timbres
          - RuntimeError: Em caso de falha de conexão ou erro no Gemini
        """
        active_key = get_active_api_key(api_key or self.api_key)
        if not active_key:
            raise ValueError(
                "Chave de API do Gemini não configurada.\n"
                "Defina a variável de ambiente GEMINI_API_KEY ou configure-a na interface gráfica."
            )

        client = genai.Client(api_key=active_key)

        try:
            interaction = client.interactions.create(
                model="gemini-3.8-flash",
                input=f"Crie um timbre da pedaleira Tank-G para o seguinte pedido:\n\n{prompt}",
                system_instruction=SYSTEM_INSTRUCTION,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": AIPresetResponse.model_json_schema(),
                },
            )

            raw_text = interaction.output_text
            if not raw_text:
                raise RuntimeError("O modelo Gemini retornou uma resposta vazia.")

            ai_data = AIPresetResponse.model_validate_json(raw_text)
            return PresetValidator.validate_and_build(ai_data)

        except OutOfDomainPromptError:
            raise
        except ValidationError as e:
            raise RuntimeError(f"A resposta da IA não respeitou o formato esperado: {e}")
        except Exception as e:
            raise RuntimeError(f"Erro na comunicação com a API Gemini: {e}")
