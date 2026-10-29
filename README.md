<div align="center">

# 🎸 M-Vave Tank-G Controller

**Controle total da pedaleira M-Vave Tank-G pelo computador, com GUI, CLI e criação de timbres por IA.**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)
![Gemini](https://img.shields.io/badge/IA-Gemini-8E75B2?logo=googlegemini&logoColor=white)
![Tests](https://img.shields.io/badge/testes-25%20passando-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/github/license/AlexandreTonin/tank-g-controller)

[Funcionalidades](#-funcionalidades-suportadas) •
[Instalação](#️-instalação-e-execução) •
[CLI](#-uso-via-linha-de-comando-cli) •
[Protocolo](#-protocolo-midi-sysex-decifrado) •
[Documentação](#-documentação)

</div>

---

Controlador desktop moderno em **PySide6 (Qt Widgets)** e interface via linha de comando (CLI) em Python para a pedaleira multi-efeitos **M-Vave (Cuvave) Tank-G** via USB-MIDI SysEx.

Este projeto é fruto de **engenharia reversa completa** do protocolo de comunicação USB-MIDI do aplicativo oficial da M-Vave (`M-EFCS`), permitindo controlar, ajustar e salvar parâmetros do pedal programaticamente e visualmente sem depender do software proprietário.

---

## 🏗️ Arquitetura do Software (MVVM)

O projeto foi inteiramente refatorado para o padrão arquitetural **Model-View-ViewModel (MVVM)**, desacoplando o modelo de dados puro, o processamento de áudio/hardware e a camada gráfica:

```
┌────────────────────────────────────────────────────────┐
│               View (PySide6 / Widgets)                 │
│  - Gemini AI Tone Crafter (Prompt + Sugestões rápidas) │
│  - Janela Dark Theme moderna com controles táteis      │
│  - Knobs vetoriais com leitura precisa e reset duplo   │
│  - Footswitches metálicos com LED indicador de bypass  │
│  - Matriz visual 9x4 de presets (36 slots)             │
└───────────────────────────▲────────────────────────────┘
                            │ Qt Signals & Slots
                            │ (Data Binding Bidirecional)
┌───────────────────────────▼────────────────────────────┐
│              ViewModel (ControlViewModel)              │
│  - Orquestra IA, debouncing e supressão de eco         │
│  - Thread assíncrona para chamadas ao Gemini           │
│  - Gravação EEPROM em 3 passos (0x69 -> 0x41 -> 0x49)  │
└─────────────┬────────────────────────────┬─────────────┘
              │ usa                        │ comanda I/O
┌─────────────▼──────────────┐ ┌───────────▼─────────────┐
│   Model (PedalState)       │ │  MidiService (QThread)  │
│ - Dataclass Python puro    │ │ - Conexão não-bloqueante│
│ - AIPresetResponse Schema  │ │ - Auto-reconexão        │
│ - Conversão de setores FX  │ │ - Tratamento WinMM Lock │
└────────────────────────────┘ └───────────┬─────────────┘
                                           │
                               ┌───────────▼─────────────┐
                               │   Camada de Serviços    │
                               │ - GeminiPresetService   │
                               │ - PresetValidator/Clamp │
                               │ - SysExCodec (Checksum) │
                               └─────────────────────────┘
```

### Estrutura de Pastas
```
tank-g-controller/
├── tankg/                        # Pacote Python principal
│   ├── core/                     # Constantes, modelos de amp, cabs e módulos
│   ├── model/                    # Dataclasses puras (PedalState, Preset, AIPresetResponse)
│   ├── services/                 # GeminiPresetService, PresetValidator, SysExCodec, MidiService
│   ├── viewmodel/                # ControlViewModel (estado reativo, IA worker, debounce)
│   ├── view/                     # PySide6 Widgets (AITonePanel, RotaryKnob, MainWindow)
│   └── cli/                      # Interface de terminal (CLI com comando ai)
├── tests/                        # 25 testes automatizados com pytest (offline)
├── docs/                         # Guia de parâmetros e diário da engenharia reversa
├── captures/                     # Capturas USB (Wireshark/USBPcap) usadas na engenharia reversa
├── main.py                       # Ponto de entrada direto para a GUI
├── tankg.py                      # Wrapper com compatibilidade retroativa para CLI e GUI
└── requirements.txt              # Dependências (mido, python-rtmidi, PySide6, google-genai, pydantic, pytest)
```

---

## 🎸 Funcionalidades Suportadas

- **✨ Gemini AI Tone Crafter (Feature Principal):**
  - Crie presets a partir de linguagem natural livre (ex: *"Timbre do solo de Dani California"*, *"Overdrive cremoso estilo Stevie Ray Vaughan"*, *"Clean estalado com chorus para funk"*).
  - O agente interpreta a intenção tonal, recomenda captadores da guitarra e escolhe exatamente o amplificador, equalização, ganho e efeitos compatíveis com a pedaleira.
  - Saída 100% estruturada via JSON Schema rígido (Pydantic).
  - Validador defensivo que nunca confia cegamente na IA, clampeando e normalizando os valores nos limites mecânicos do pedal.
  - Teste imediato em tempo real no pedal sem sobrescrever a memória permanente ou gravação direta na EEPROM do slot desejado.
- **Interface Gráfica Completa (PySide6):**
  - Painéis modulares com código de cores: **AI TONE CRAFTER**, **GATE & CAB**, **PREAMP / AMP**, **MODULATION**, **DELAY** e **REVERB**.
  - Knobs rotativos vetoriais com controle por arrasto vertical, roda do mouse e duplo clique para reset.
  - Footswitches com LEDs verdes acesos para módulos ativos e apagados em bypass.
- **Seleção e Troca de Presets (36 Presets):**
  - Navegação instantânea pelos 9 Bancos e 4 Slots (**1A a 9D**).
- **Gravação Persistente na EEPROM:**
  - Salva o preset atual ou qualquer preset de destino diretamente na memória permanente do pedal (`0x69`).
- **Módulo de Pré-amplificador (AMP):**
  - 9 Modelos de amplificadores clássicos (VOX AC30, Fender '65 Twin Reverb, Bogner Shiva, Marshall JTM45, Plexi 100, JCM800, EVH 5150, ENGL Powerball, Mesa Dual Rectifier).
  - Ajustes de equalização: `gain`, `treble`, `middle`, `bass` e `volume` (`0 a 100`).
- **Módulo de Modulação (MOD):**
  - Seleção entre **Chorus**, **Phaser** e **Tremolo** (`1 a 40`).
  - Velocidade da modulação: `speed` (`0 a 100`).
- **Módulo de Delay (DLY):**
  - Seleção entre **Analog Delay**, **Tape Delay** e **Dual Delay** (`1 a 40`).
  - Tempo / Feedback: `delay-time` (`0 a 100`).
- **Módulo de Reverb (REV):**
  - Seleção entre **Room Reverb**, **Spring Reverb** e **Cloud Reverb** (`1 a 40`).
  - Mistura: `reverb-mix` (`0 a 100`).
- **Módulo de Dinâmica & Gabinetes:**
  - **Noise Gate:** `0 a 100` (desativado em zero).
  - **Simulações de Gabinete (IR CAB):** Slots `0 a 8` (0 = Bypass, 1 a 8 = Gabinetes).
- **Ativação / Desativação de Módulos (Bypass):**
  - Liga ou desliga individualmente os blocos: `amp`, `mod`, `dly` e `rev`.

---

## 🛠️ Instalação e Execução

### 1. Clonar e Configurar Ambiente

```bash
git clone https://github.com/AlexandreTonin/tank-g-controller.git
cd tank-g-controller

# Criar e ativar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows (PowerShell)
source .venv/bin/activate         # Linux / macOS

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar a Chave da API Gemini (opcional, só para o AI Tone Crafter)

A chave é procurada nesta ordem: valor informado na interface, variável de ambiente `GEMINI_API_KEY` e, por fim, o arquivo local `config.json` (ignorado pelo Git).

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "sua-chave"
# Linux / macOS
export GEMINI_API_KEY="sua-chave"
```

### 3. Abrir a Interface Gráfica (GUI)

Execute qualquer um dos comandos abaixo:
```bash
python main.py
# ou
python tankg.py
# ou
python -m tankg
```

### 4. Executar a Suíte de Testes Automatizados

O projeto inclui testes de unidade cobrindo todas as fórmulas matemáticas e codecs de bits sem precisar do pedal conectado:
```bash
pytest -v
```

---

## 💻 Uso via Linha de Comando (CLI)

O arquivo `tankg.py` mantém compatibilidade total com automações e uso via terminal:

```bash
# Diagnóstico e Consulta
python tankg.py list             # Lista portas MIDI disponíveis
python tankg.py status           # Exibe o status atual de todos os parâmetros
python tankg.py preset list      # Lista os 36 presets (1A a 9D)
python tankg.py type list        # Lista os 9 modelos de amplificador
python tankg.py cab list         # Lista os slots de IR Cab

# Criação de Timbres com Inteligência Artificial (Gemini API)
python tankg.py ai "timbre do solo de Stairway to Heaven"
python tankg.py ai "som de Dani California do RHCP" --slot 3B --save
python tankg.py ai "clean aveludado com chorus e reverb espaçoso" --slot 1A --save

# Troca e Gravação de Presets
python tankg.py preset 3B        # Seleciona o preset 3B (ou número 10)
python tankg.py 3B               # Atalho direto para trocar de preset
python tankg.py save 3B          # Grava configuração atual na EEPROM do preset 3B

# Controle do Amplificador
python tankg.py type 6           # Marshall JCM800
python tankg.py gain 85          # Ajusta ganho para 85%
python tankg.py treble 65        # Ajusta agudos
python tankg.py middle 50        # Ajusta médios
python tankg.py bass 60          # Ajusta graves
python tankg.py volume 70        # Ajusta volume

# Efeitos e Dinâmica
python tankg.py chorus 25        # Chorus no nível 25/40
python tankg.py delay-tape 30    # Tape Delay no nível 30/40
python tankg.py delay-time 55    # Tempo do Delay
python tankg.py reverb-room 20   # Room Reverb no nível 20/40
python tankg.py gate 40          # Noise Gate em 40%
python tankg.py cab 1            # Gabinete VHT Deliverance (4x12)

# Bypass de Módulos
python tankg.py amp off          # Desativa módulo de amplificador
python tankg.py mod on           # Ativa módulo de modulação
```

---

## 🔬 Protocolo MIDI SysEx Decifrado

### Identificador de Fabricante
Todas as mensagens SysEx da M-Vave iniciam com o cabeçalho:
`F0 00 32 09 ... F7`

### 1. Preset em Tempo Real (Comando `0x31` - 36 bytes)
Os 12 parâmetros são multiplicados por 2, empacotados em grupos de 7 bits (bytes 18 a 32), e o checksum de 14 bits obedece à fórmula:
```
params_sum = type + gain + treble + middle + bass + volume
           + mod_fx + mod_speed + dly_mix + dly_time + rev_decay + rev_mix
ck  = (211 - params_sum) % 256
ck1 = ck & 0x7F
ck2 = (ck >> 7) & 0x7F
```

### 2. Bypass de Módulos (Comando `0x49`, Sub-registro `0x11`)
- IDs: `AMP = 0`, `MOD = 1`, `DLY = 2`, `REV = 3`
- Estado: `0 = Bypass / Desligado`, `1 = Ativo / Ligado`
```
ck1 = 0x54 - 2 * mod_id - 2 * state
ck2 = 0x03
```

### 3. Troca de Preset (Comando `0x49`, Sub-registro `0x1E`)
Para o ID interno do preset de `0` a `35` (onde `0 = 1A` e `35 = 9D`):
```
ck  = (50 - 2 * preset_id) % 256
ck1 = ck & 0x7F
ck2 = (ck >> 7) & 0x7F
```

### 4. Gravação na Memória EEPROM (Comando `0x69` - 44 bytes)
Grava os 21 bytes de parâmetros no endereço de offset específico daquele preset:
```
offset = preset_id * 21 + 2
ck  = (230 - sum(field[0..20]) - offset) % 256
ck1 = ck & 0x7F
ck2 = (ck >> 7) & 0x7F
```
Logo em seguida, o controlador envia um comando de flush (`0x41`) e a troca para o próprio preset (`0x49`) para que o pedal recarregue a memória flash.

---

## ⚠️ Dica Importante para Windows
No Windows, os drivers de áudio/MIDI (WinMM) operam em modo de **acesso exclusivo**. Para conectar o controlador à Tank-G:
1. Certifique-se de que o software proprietário da M-Vave (`m_efcs.exe`) está **fechado**.
2. Certifique-se de que nenhuma DAW (Reaper, FL Studio, etc.) está travando a porta `USB-Midi 1`.

---

## 📚 Documentação

- [Guia de parâmetros e módulos](docs/guia-de-parametros.md): amps, gabinetes, setores de efeito e footswitches.
- [Diário de engenharia reversa](docs/engenharia-reversa.md): como cada comando SysEx foi capturado e decifrado.
- [`captures/`](captures): arquivos `.pcapng` originais, abríveis no Wireshark.

---

## 📄 Licença
Distribuído sob a licença [MIT](LICENSE). Criado para a comunidade de guitarristas e entusiastas de áudio.
