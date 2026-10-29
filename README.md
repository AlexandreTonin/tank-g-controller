<div align="center">

# M-Vave Tank-G Controller

Controle a pedaleira M-Vave Tank-G pelo computador: interface gráfica, linha de comando e timbres gerados pelo Gemini.

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)
![Gemini](https://img.shields.io/badge/IA-Gemini-8E75B2?logo=googlegemini&logoColor=white)
![Tests](https://img.shields.io/badge/testes-25%20passando-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/github/license/AlexandreTonin/tank-g-controller)

[Funcionalidades](#funcionalidades) •
[Instalação](#instalação-e-execução) •
[CLI](#uso-via-linha-de-comando-cli) •
[Protocolo](#protocolo-midi-sysex) •
[Documentação](#documentação)

</div>

---

Aplicativo desktop em PySide6 e CLI em Python para a pedaleira multiefeitos M-Vave (Cuvave) Tank-G. A comunicação acontece por SysEx sobre USB-MIDI.

O protocolo não tem documentação pública. Capturei o tráfego USB do aplicativo oficial da M-Vave (`M-EFCS`) no Wireshark e decifrei os comandos um a um: parâmetros do preset, bypass de módulos, troca de preset e gravação na EEPROM. Com isso dá para editar e salvar presets sem o software da fabricante, que só roda no Windows.

---

## Arquitetura (MVVM)

O código segue Model-View-ViewModel. O estado do pedal fica em dataclasses sem dependência de Qt, a comunicação MIDI roda em uma thread própria e a interface só conversa com o ViewModel:

```
┌────────────────────────────────────────────────────────┐
│               View (PySide6 / Widgets)                 │
│  - Gemini AI Tone Crafter (Prompt + Sugestões rápidas) │
│  - Janela principal com tema escuro                    │
│  - Knobs com arrasto, roda do mouse e reset no duplo   │
│  - Footswitches com LED de bypass                      │
│  - Grade 9x4 de presets (36 slots)                     │
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

## Funcionalidades

### Timbres gerados por IA (Gemini AI Tone Crafter)

Descreva o som em texto livre, por exemplo *"solo de Dani California"*, *"overdrive cremoso estilo Stevie Ray Vaughan"* ou *"clean estalado com chorus para funk"*. O Gemini devolve amp, equalização, ganho, efeitos e uma sugestão de captador.

- A resposta vem em JSON validado por um schema Pydantic com todos os campos obrigatórios.
- O `PresetValidator` limita cada valor à faixa que o pedal aceita antes de enviar qualquer coisa. Se o modelo devolver `gain: 140`, o pedal recebe `100`.
- Dá para ouvir o timbre no pedal sem gravar, ou salvar direto na EEPROM de um slot.

### Interface gráfica

- Painéis por módulo: AI Tone Crafter, Gate & Cab, Preamp/Amp, Modulation, Delay e Reverb.
- Knobs controlados por arrasto vertical ou roda do mouse; duplo clique volta ao valor padrão.
- Footswitches com LED verde aceso quando o módulo está ativo e apagado em bypass.

### Controle do pedal

- **Presets:** troca entre os 36 presets (9 bancos × 4 slots, de `1A` a `9D`).
- **Gravação na EEPROM:** salva o estado atual em qualquer slot da memória permanente (comando `0x69`).
- **AMP:**
  - 9 modelos de amplificador (VOX AC30, Fender '65 Twin Reverb, Bogner Shiva, Marshall JTM45, Plexi 100, JCM800, EVH 5150, ENGL Powerball, Mesa Dual Rectifier).
  - `gain`, `treble`, `middle`, `bass` e `volume`, de `0` a `100`.
- **MOD:** Chorus, Phaser ou Tremolo, com nível de `1` a `40`; `speed` de `0` a `100`.
- **DLY:** Analog, Tape ou Dual Delay, com nível de `1` a `40`; `delay-time` de `0` a `100`.
- **REV:** Room, Spring ou Cloud Reverb, com nível de `1` a `40`; `reverb-mix` de `0` a `100`.
- **Noise gate:** `0` a `100`; em `0` fica desligado.
- **IR CAB:** slots `0` a `8`, sendo `0` o bypass.
- **Bypass:** liga e desliga `amp`, `mod`, `dly` e `rev` separadamente.

---

## Instalação e execução

### 1. Clonar e instalar

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

### 2. Chave da API Gemini (opcional)

Só o AI Tone Crafter precisa dela. O programa procura a chave nesta ordem: campo na interface, variável de ambiente `GEMINI_API_KEY` e arquivo local `config.json` (fora do Git).

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "sua-chave"
# Linux / macOS
export GEMINI_API_KEY="sua-chave"
```

### 3. Abrir a interface gráfica

Qualquer um destes comandos abre a GUI:
```bash
python main.py
# ou
python tankg.py
# ou
python -m tankg
```

### 4. Rodar os testes

Os testes cobrem checksums, empacotamento de bits, estado do pedal e o validador da IA. Nenhum precisa do pedal conectado:
```bash
pytest -v
```

---

## Uso via linha de comando (CLI)

Com argumentos, `tankg.py` funciona como CLI:

```bash
# Consulta
python tankg.py list             # Lista portas MIDI disponíveis
python tankg.py status           # Exibe o status atual de todos os parâmetros
python tankg.py preset list      # Lista os 36 presets (1A a 9D)
python tankg.py type list        # Lista os 9 modelos de amplificador
python tankg.py cab list         # Lista os slots de IR Cab

# Timbres gerados pelo Gemini
python tankg.py ai "timbre do solo de Stairway to Heaven"
python tankg.py ai "som de Dani California do RHCP" --slot 3B --save
python tankg.py ai "clean aveludado com chorus e reverb espaçoso" --slot 1A --save

# Troca e gravação de presets
python tankg.py preset 3B        # Seleciona o preset 3B (ou número 10)
python tankg.py 3B               # Atalho direto para trocar de preset
python tankg.py save 3B          # Grava configuração atual na EEPROM do preset 3B

# Amplificador
python tankg.py type 6           # Marshall JCM800
python tankg.py gain 85          # Ajusta ganho para 85%
python tankg.py treble 65        # Ajusta agudos
python tankg.py middle 50        # Ajusta médios
python tankg.py bass 60          # Ajusta graves
python tankg.py volume 70        # Ajusta volume

# Efeitos e dinâmica
python tankg.py chorus 25        # Chorus no nível 25/40
python tankg.py delay-tape 30    # Tape Delay no nível 30/40
python tankg.py delay-time 55    # Tempo do Delay
python tankg.py reverb-room 20   # Room Reverb no nível 20/40
python tankg.py gate 40          # Noise Gate em 40%
python tankg.py cab 1            # Gabinete VHT Deliverance (4x12)

# Bypass de módulos
python tankg.py amp off          # Desativa módulo de amplificador
python tankg.py mod on           # Ativa módulo de modulação
```

---

## Protocolo MIDI SysEx

### Cabeçalho
Toda mensagem SysEx da M-Vave começa com:
`F0 00 32 09 ... F7`

### 1. Preset em Tempo Real (Comando `0x31` - 36 bytes)
Cada um dos 12 parâmetros vira um campo de 8 bits com o valor multiplicado por 2. Os campos são concatenados e fatiados em bytes de 7 bits (bytes 18 a 32). O checksum de 14 bits é:
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
Grava os 21 bytes do preset no endereço daquele slot:
```
offset = preset_id * 21 + 2
ck  = (230 - sum(field[0..20]) - offset) % 256
ck1 = ck & 0x7F
ck2 = (ck >> 7) & 0x7F
```
Depois da gravação, o controlador envia um flush (`0x41`) e seleciona o próprio preset (`0x49`) para o pedal recarregar a memória.

---

## Windows: porta MIDI ocupada

No Windows, o driver MIDI (WinMM) só deixa um programa abrir a porta por vez. Antes de conectar:
1. Feche o aplicativo da M-Vave (`m_efcs.exe`).
2. Feche qualquer DAW (Reaper, FL Studio etc.) que esteja usando a porta `USB-Midi 1`.

---

## Documentação

- [Guia de parâmetros e módulos](docs/guia-de-parametros.md): amps, gabinetes, setores de efeito e footswitches.
- [Diário de engenharia reversa](docs/engenharia-reversa.md): como cada comando SysEx foi capturado e decifrado.
- [`captures/`](captures): arquivos `.pcapng` originais, abríveis no Wireshark.

---

## Licença
[MIT](LICENSE).
