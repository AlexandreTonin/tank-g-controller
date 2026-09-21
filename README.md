# M-Vave Tank-G Controller (`tank-g-controller`)

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
                               │     Camada de Serviços  │
                               │ - GeminiPresetService   │
                               │ - PresetValidator/Clamp │
                               │ - SysExCodec (Checksum) │
                               │ - 25 Testes Automatizados│
                               └─────────────────────────┘
```

### Estrutura de Pastas
```
tankg/
├── tankg/                        # Pacote Python principal
│   ├── core/                     # Constantes, modelos de amp, cabs e módulos
│   ├── model/                    # Dataclasses puras (PedalState, Preset, AIPresetResponse)
│   ├── services/                 # GeminiPresetService, PresetValidator, SysExCodec, MidiService
│   ├── viewmodel/                # ControlViewModel (estado reativo, IA worker, debounce)
│   ├── view/                     # PySide6 Widgets (AITonePanel, RotaryKnob, MainWindow)
│   └── cli/                      # Interface de terminal (CLI com comando ai)
├── tests/                        # 25 testes automatizados com pytest (offline)
├── main.py                       # Ponto de entrada direto para a GUI
├── tankg.py                      # Wrapper com compatibilidade retroativa para CLI e GUI
└── requirements.txt              # Dependências (google-genai, pydantic, PySide6, pytest, mido)
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
  - 9 Modelos de amplificadores clássicos (VOX AC30, Twin Reverb, Bogner, Plexi, JCM800, 5150, Powerball, Dual Rectifier).
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
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### 2. Abrir a Interface Gráfica (GUI)

Execute qualquer um dos comandos abaixo:
```bash
python main.py
# ou
python tankg.py
```

### 3. Executar a Suíte de Testes Automatizados

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
$$\mathbf{params\_sum} = \text{type} + \text{gain} + \text{treble} + \text{middle} + \text{bass} + \text{volume} + \text{mod\_fx} + \text{mod\_speed} + \text{dly\_mix} + \text{dly\_time} + \text{rev\_decay} + \text{rev\_mix}$$
$$\mathbf{ck} = (211 - \mathbf{params\_sum}) \pmod{256}$$
$$\mathbf{ck_1} = \mathbf{ck} \ \& \ 0x7F, \quad \mathbf{ck_2} = (\mathbf{ck} \gg 7) \ \& \ 0x7F$$

### 2. Bypass de Módulos (Comando `0x49`, Sub-registro `0x11`)
- IDs: `AMP = 0`, `MOD = 1`, `DLY = 2`, `REV = 3`
- Estado: `0 = Bypass / Desligado`, `1 = Ativo / Ligado`
$$\mathbf{ck_1} = 0x54 - 2 \times \text{mod\_id} - 2 \times \text{state}, \quad \mathbf{ck_2} = 0x03$$

### 3. Troca de Preset (Comando `0x49`, Sub-registro `0x1E`)
Para o ID interno do preset de `0` a `35` (onde $0 = 1A$ e $35 = 9D$):
$$\mathbf{ck} = (50 - 2 \times \text{preset\_id}) \pmod{256}$$
$$\mathbf{ck_1} = \mathbf{ck} \ \& \ 0x7F, \quad \mathbf{ck_2} = (\mathbf{ck} \gg 7) \ \& \ 0x7F$$

### 4. Gravação na Memória EEPROM (Comando `0x69` - 44 bytes)
Grava os 21 bytes de parâmetros no endereço de offset específico daquele preset:
$$\text{offset} = \text{preset\_id} \times 21 + 2$$
$$\mathbf{ck} = (230 - \sum_{i=0}^{20} \text{field}_i - \text{offset}) \pmod{256}$$
$$\mathbf{ck_1} = \mathbf{ck} \ \& \ 0x7F, \quad \mathbf{ck_2} = (\mathbf{ck} \gg 7) \ \& \ 0x7F$$
Logo em seguida, o controlador envia um comando de flush (`0x41`) e a troca para o próprio preset (`0x49`) para que o pedal recarregue a memória flash.

---

## ⚠️ Dica Importante para Windows
No Windows, os drivers de áudio/MIDI (WinMM) operam em modo de **acesso exclusivo**. Para conectar o controlador à Tank-G:
1. Certifique-se de que o software proprietário da M-Vave (`m_efcs.exe`) está **fechado**.
2. Certifique-se de que nenhuma DAW (Reaper, FL Studio, etc.) está travando a porta `USB-Midi 1`.

---

## 📄 Licença
Distribuído sob a licença MIT. Criado para a comunidade de guitarristas e entusiastas de áudio.
