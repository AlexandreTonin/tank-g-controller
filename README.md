# M-Vave Tank-G Controller (`tank-g-controller`)

Controlador via linha de comando (CLI) em Python para a pedaleira multi-efeitos **M-Vave (Cuvave) Tank-G** via USB-MIDI SysEx.

Este projeto é fruto de **engenharia reversa completa** do protocolo de comunicação USB-MIDI do aplicativo oficial da M-Vave (`M-EFCS`), permitindo controlar, ajustar e salvar parâmetros do pedal programaticamente sem depender do software oficial.

---

## 🎸 Funcionalidades Suportadas

- **Seleção e Troca de Presets (36 Presets):**
  - Navegação entre todos os 9 Bancos e 4 Slots (**1A a 9D**).
- **Gravação Persistente na EEPROM:**
  - Salva o som atual diretamente na memória permanente do pedal (`save`).
- **Módulo de Pré-amplificador (AMP):**
  - 9 Modelos de amplificadores clássicos (VOX AC30, Twin Reverb, Bogner, Plexi, JCM800, 5150, Powerball, Dual Rectifier).
  - Ajustes de equalização: `gain`, `treble`, `middle`, `bass` e `volume` (`0 a 100`).
- **Módulo de Modulação (MOD):**
  - Seleção contínua entre **Chorus**, **Phaser** e **Tremolo** (`1 a 40`).
  - Velocidade da modulação: `speed` (`0 a 100`).
- **Módulo de Delay (DLY):**
  - Seleção contínua entre **Analog Delay**, **Tape Delay** e **Dual Delay** (`1 a 40`).
  - Tempo / Feedback: `delay-time` (`0 a 100`).
- **Módulo de Reverb (REV):**
  - Seleção contínua entre **Room Reverb**, **Spring Reverb** e **Cloud Reverb** (`1 a 40`).
  - Proporção da mistura: `reverb-mix` (`0 a 100`).
- **Módulo de Dinâmica & Gabinetes:**
  - **Noise Gate:** `0 a 100` (desativa todo para a esquerda).
  - **Simulações de Gabinete (IR CAB):** Slots `0 a 8` (0 = Bypass, 1 a 8 = Gabinetes).
- **Ativação / Desativação de Módulos (Bypass):**
  - Liga ou desliga individualmente os blocos: `amp`, `mod`, `dly` e `rev`.
- **Persistência de Estado Local:**
  - Mantém o estado atual em `state.json` para que o ajuste de um único botão não resete as outras configurações.

---

## 🛠️ Requisitos e Instalação

### Requisitos:
- Python 3.10 ou superior
- Cabo USB-C conectando a Tank-G ao computador

### Instalação:

1. Clone o repositório:
```bash
git clone https://github.com/AlexandreTonin/tank-g-controller.git
cd tank-g-controller
```

2. Crie e ative um ambiente virtual:
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

> **⚠️ IMPORTANTE (Windows):**  
> A API MIDI do Windows (WinMM) exige acesso exclusivo à porta MIDI. Certifique-se de **fechar o software oficial (`m_efcs.exe`)**, DAWs ou navegadores com acesso MIDI antes de rodar os comandos do script.

---

## 💻 Guia de Uso da Linha de Comando (CLI)

### Status e Portas
```bash
# Listar portas MIDI disponíveis no sistema
python tankg.py list

# Exibir o status de todos os parâmetros atualmente salvos
python tankg.py status
```

### Presets e Bancos
```bash
# Listar todos os 36 presets disponíveis
python tankg.py preset list

# Trocar de preset por nome (banco + letra)
python tankg.py preset 3B
python tankg.py 3b             # atalho direto
python tankg.py 4a

# Trocar de preset por número sequencial (1 a 36)
python tankg.py preset 10      # seleciona o 3B

# Gravar a configuração atual na memória EEPROM do pedal
python tankg.py save 3B        # salva no slot 3B
python tankg.py save           # salva no slot atual
```

### Ativação e Bypass de Efeitos
```bash
python tankg.py amp on         # liga o pré-amplificador
python tankg.py amp off        # desliga (bypass) o pré-amplificador
python tankg.py mod on         # liga o bloco de modulação
python tankg.py dly off        # desliga o delay
python tankg.py rev on         # liga o reverb
```

### Pré-amplificador (AMP)
```bash
# Listar modelos de amplificador
python tankg.py type list

# Escolher modelo de amplificador (1 a 9)
python tankg.py type 1         # VOX AC30HW
python tankg.py type 7         # EVH 5150 LEAD

# Ajustar equalização e ganho (0 a 100)
python tankg.py gain 75
python tankg.py treble 50
python tankg.py middle 45
python tankg.py bass 60
python tankg.py volume 80
```

### Modulação (MOD)
```bash
# Selecionar efeito e intensidade (1 a 40)
python tankg.py chorus 20      # Chorus (Mix: 20/40)
python tankg.py phaser 35      # Phaser (Depth: 35/40)
python tankg.py tremolo 15     # Tremolo (Mix: 15/40)

# Velocidade da oscilação (0 a 100)
python tankg.py speed 65
```

### Delay (DLY)
```bash
# Selecionar algoritmo e intensidade (1 a 40)
python tankg.py delay-analog 20 # Analog Delay (Mix: 20/40)
python tankg.py delay-tape 25   # Tape Delay (Mix: 25/40)
python tankg.py delay-dual 15   # Dual Delay (Mix: 15/40)

# Tempo de atraso / repetições (0 a 100)
python tankg.py delay-time 50
```

### Reverb (REV)
```bash
# Selecionar algoritmo e cauda (1 a 40)
python tankg.py reverb-room 20   # Room Reverb (Decay: 20/40)
python tankg.py reverb-spring 25 # Spring Reverb (Decay: 25/40)
python tankg.py reverb-cloud 30  # Cloud Reverb (Decay: 30/40)

# Quantidade de mistura de Reverb (0 a 100)
python tankg.py reverb-mix 45
```

### Noise Gate e Simulações de Gabinete (IR CAB)
```bash
# Ajustar o Noise Gate (0 a 100)
python tankg.py gate 35

# Listar gabinetes disponíveis
python tankg.py cab list

# Selecionar gabinete (0 a 8)
python tankg.py cab 1          # VHT Deliverance (4x12)
python tankg.py cab 4          # Mesa Boogie (4x12)
python tankg.py cab 0          # Desliga o IR CAB (Bypass)
```

---

## 🔬 Arquitetura do Protocolo SysEx

Toda a documentação técnica da engenharia reversa com capturas e fórmulas matemáticas está registrada em [context.md](context.md).

### Resumo dos Comandos SysEx da Tank-G:
| Comando | Tamanho | Função | Estrutura Básica |
| :---: | :---: | :--- | :--- |
| `0x31` | 36 bytes | **Ajuste em Tempo Real** | Bitstream de 13 campos empacotado em 15 blocos de 7 bits MIDI |
| `0x49` | 21 bytes | **Bypass e Troca de Presets** | Comando de registradores (`0x11` para bypass, `0x1E` para presets) |
| `0x69` | 44 bytes | **Gravação EEPROM do Preset** | Escreve os 21 bytes do preset no offset `preset_id * 21 + 2` |

### Fórmulas Mestre dos Checksums:
- **Preset em Tempo Real (Comando `0x31`):**
  $$\mathbf{ck} = (211 - \sum \text{parâmetros}) \pmod{256}$$
- **Troca de Preset (Comando `0x49`):**
  $$\mathbf{ck} = (50 - 2 \times \text{preset\_id}) \pmod{256}$$
- **Gravação na EEPROM (Comando `0x69`):**
  $$\mathbf{ck} = (230 - \sum \text{campos} - \text{offset}) \pmod{256}$$

---

## 📄 Licença

Este projeto é disponibilizado para fins educacionais e de interoperabilidade livre.
