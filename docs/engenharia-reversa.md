# Engenharia Reversa do Protocolo USB/MIDI da M-Vave Tank-G

> Anotações da engenharia reversa, na ordem em que cada parte do protocolo foi decifrada.
> As capturas do Wireshark citadas aqui estão na pasta [`captures/`](../captures). Para o resumo do protocolo, veja o [README](../README.md#protocolo-midi-sysex).

## Objetivo

Interceptar e decodificar os comandos que o software oficial da Mvave envia para a
pedaleira **Tank-G** via USB-C, para conseguir controlar parâmetros específicos
(gain, volume, mid, noise gate, etc.) programaticamente, sem depender do app oficial.

## Ambiente

- SO usado para captura: **Windows** (decisão tomada porque o app oficial da Mvave só roda em Windows)
- Ferramentas: **Wireshark + USBPcap**
- Linguagem alvo para o script de controle: **Python** (`mido` + `python-rtmidi`)

---

## Repositórios de referência encontrados no GitHub

1. **[mvave-tankg-ble](https://github.com/hudsonbrendon/mvave-tankg-ble)** (autor: Hudson Brendon)
   - Biblioteca Python para controlar a Tank-G via **Bluetooth LE**
   - A pedaleira fala BLE-MIDI: troca de presets via _Program Change_ MIDI, canal 0
   - CLI: `mvave-tankg scan`, `mvave-tankg preset 12`
   - Limitação conhecida: só troca presets (1-36); não lê LED, bateria, ou parâmetros
     de efeito porque o protocolo proprietário Cuvave (serviço BLE `0xAE40`) não foi
     reverso-engenheirado
   - Licença MIT

2. **[ha-mvave-tankg](https://github.com/hudsonbrendon/ha-mvave-tankg)** (mesmo autor)
   - Integração para Home Assistant construída sobre a lib acima

---

## Processo de captura (USB, Windows)

### Descoberta do protocolo

1. Testamos primeiro tráfego `USBAUDIO` (VOLUME_CONTROL, MUTE_CONTROL) — identificado
   como tráfego padrão da classe USB Audio (volume da interface de som embutida),
   **não relacionado** ao controle de parâmetros do efeito.
2. O tráfego relevante identificado foi **SysEx MIDI** sobre USB (`URB_BULK`, protocolo
   `SYSEX`), em uma interface separada do dispositivo composto.
3. Identificado um padrão de **heartbeat/keep-alive**: pacotes `out` de 27 bytes,
   idênticos, repetidos periodicamente — não carregam dados de parâmetro, apenas
   mantêm a conexão viva.
4. Os pacotes que carregam comandos reais de parâmetro têm tamanhos maiores:
   **43, 55, 59, 75 bytes** (tamanho total do frame USB, incluindo cabeçalho USB-MIDI).

### Estrutura do pacote USB-MIDI

Os dados chegam encapsulados no formato **USB-MIDI Event Packet**: blocos de 4 bytes,
onde o primeiro byte é o **CIN (Code Index Number)** e os 3 seguintes são dados MIDI reais.

- `CIN = 4`: SysEx starts ou continua (3 bytes de dado)
- `CIN = 7`: SysEx termina com 3 bytes (incluindo o `F7` final)

Para extrair a mensagem SysEx pura, é preciso remover o byte de CIN de cada bloco de 4
e concatenar os bytes de dado restantes.

---

## Dados capturados e análise

### Exemplo 1 — Gain (captura inicial)

Payload USB bruto (exemplo de um pacote `out`):

```
0000   1b 00 70 c2 6c 51 03 ba ff ff 00 00 00 00 09 00   ..p.lQ..........
0010   01 02 00 01 00 84 03 10 00 00 00 04 f0 00 32 04   ..............2.
0020   01 08 00 04 00 00 00 07 7f 01 f7                  ...........
```

SysEx extraído (removendo CIN):

```
F0 00 32 01 08 00 00 00 00 7F 01 F7
```

Estrutura hipotética:

```
F0          -> inicio do SysEx
00 32       -> provavel ID do fabricante/dispositivo (Cuvave/Mvave)
01          -> possivel tipo de comando ("set parameter")
08          -> possivel ID do bloco/efeito
00 00 00 00 -> padding ou sub-endereco
7F 01       -> candidato a valor do parametro (7F = 127, maximo em 7 bits MIDI)
F7          -> fim do SysEx
```

### Exemplo 2 — Noise Gate = 100 e Noise Gate = 0 (confirmado)

**Pacote #15 — Noise Gate = 100** (frame de 75 bytes, protocolo SYSEX):

```
0000   1b 00 10 f0 b4 50 03 ba ff ff 00 00 00 00 09 00   .....P..........
0010   00 02 00 01 00 04 03 30 00 00 00 04 f0 00 32 04   .......0......2.
0020   09 31 01 04 00 00 02 04 04 00 00 04 00 61 01 04   .1...........a..
0030   00 00 64 04 06 3c 31 04 35 68 4b 04 25 03 00 04   ..d..<1.5hK.%...
0040   18 18 52 04 20 40 01 07 7b 01 f7                  ..R. @..{..
```

SysEx extraído:

```
F0 00 32 09 31 01 00 00 02 04 00 00 00 61 01 00 00 64 06 3c 31 35 68 4b 25 03 00 18 18 52 20 40 01 7B 01 F7
```

**Pacote #23 — Noise Gate = 0** (frame de 75 bytes):

```
0000   1b 00 10 f0 b4 50 03 ba ff ff 00 00 00 00 09 00   .....P..........
0010   00 02 00 01 00 04 03 30 00 00 00 04 f0 00 32 04   .......0......2.
0020   09 31 01 04 00 00 02 04 04 00 00 04 00 61 01 04   .1...........a..
0030   00 00 00 04 06 3c 31 04 35 68 4b 04 25 03 00 04   .....<1.5hK.%...
0040   18 18 52 04 20 40 01 07 5f 00 f7                  ..R. @.._..
```

SysEx extraído:

```
F0 00 32 09 31 01 00 00 02 04 00 00 00 61 01 00 00 00 06 3c 31 35 68 4b 25 03 00 18 18 52 20 40 01 5F 00 F7
```

### Diferenças encontradas (byte a byte)

| Posição no SysEx                           | Noise Gate = 100 | Noise Gate = 0 | Interpretação                                                                   |
| ------------------------------------------ | ---------------- | -------------- | ------------------------------------------------------------------------------- |
| byte 18 (offset `0x32` no frame USB bruto) | `64`             | `00`           | **Valor do parâmetro** (0x64 = 100 decimal, 0x00 = 0 decimal — bate exatamente) |
| byte 34                                    | `7B`             | `5F`           | Provável checksum/CRC (byte baixo)                                              |
| byte 35                                    | `01`             | `00`           | Provável checksum/CRC (byte alto)                                               |

**Conclusão:** o byte 18 do SysEx (offset `0x32` no frame USB bruto) é o
valor do Noise Gate, codificado direto em decimal de 0-100 (não em escala MIDI 0-127).

### Checksum

Com a captura dos valores intermediários (10, 20, 25, 50) somados a 0 e 100:

| Noise Gate | Byte Parâmetro | Checksum Byte 1 | Checksum Byte 2 | 14-bit MIDI (`ck1 \| (ck2 << 7)`) | Fórmula: `(95 - val) % 256` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | `0x00` (0) | `0x5F` (95) | `0x00` (0) | 95 | `(95 - 0) % 256 = 95` (`5F 00`) |
| **10** | `0x0A` (10) | `0x55` (85) | `0x00` (0) | 85 | `(95 - 10) % 256 = 85` (`55 00`) |
| **20** | `0x14` (20) | `0x4B` (75) | `0x00` (0) | 75 | `(95 - 20) % 256 = 75` (`4B 00`) |
| **25** | `0x19` (25) | `0x46` (70) | `0x00` (0) | 70 | `(95 - 25) % 256 = 70` (`46 00`) |
| **50** | `0x32` (50) | `0x2D` (45) | `0x00` (0) | 45 | `(95 - 50) % 256 = 45` (`2D 00`) |
| **100** | `0x64` (100) | `0x7B` (123) | `0x01` (1) | 251 (`0xFB`) | `(95 - 100) % 256 = 251` (`7B 01`) |

#### Algoritmo do Checksum
1. O valor base do checksum é inversamente proporcional ao valor do parâmetro:
   `ck = (95 - valor) % 256`
2. Como o protocolo MIDI exige que os bytes de dados SysEx não usem o bit mais significativo (valores `<= 127`), o resultado de 8 bits é empacotado no formato padrão de **14-bit MIDI** (dois blocos de 7 bits):
   ```python
   ck = (95 - valor) % 256
   ck_byte1 = ck & 0x7F        # LSB 7 bits
   ck_byte2 = (ck >> 7) & 0x7F # MSB 7 bits
   ```
3. A nível de mensagem inteira, o checksum mantém constante a soma dos bytes de dados módulo 256:
   `(sum(data_bytes) + ck) % 256 == 154 (0x9A)`

---

## Primeiro script de testes (histórico)

Arquivo: `tankg_control.py`. Protótipo usado no início da pesquisa, antes de o checksum ser decifrado. Foi substituído pelo pacote `tankg` e não faz parte do repositório.

Funcionalidades:

- `list`: lista portas MIDI de entrada/saída disponíveis no sistema
- `replay gate0` / `replay gate100`: reenvia os comandos SysEx exatos capturados e
  confirmados (valores 0 e 100 do noise gate)
- `raw <bytes hex>`: envia uma mensagem SysEx arbitrária (para testes manuais)
- Detecção automática da porta MIDI da Tank-G por nome (`tank`, `mvave`, `cuvave`)
- Usa `mido` + `python-rtmidi`, que cuidam automaticamente do encoding USB-MIDI
  (não é necessário montar os blocos de 4 bytes com CIN manualmente — só passar a
  mensagem SysEx pura)

```python
"""
Tank-G MIDI SysEx control script
----------------------------------
Requisitos:
    pip install mido python-rtmidi

Uso:
    python tankg_control.py list          # lista portas MIDI disponíveis
    python tankg_control.py replay gate0  # reenvia o comando conhecido "noise gate = 0"
    python tankg_control.py replay gate100
    python tankg_control.py raw F0 00 32 09 ...   # envia bytes SysEx crus (incluir F0 e F7)

IMPORTANTE:
    - Rode isso com o software oficial da Mvave FECHADO, para não haver conflito
      disputando a mesma porta MIDI.
    - Os comandos abaixo foram extraídos de captura USB real (Wireshark) e
      confirmados por comparação de dois valores (gate=0 e gate=100).
    - O checksum final (últimos 2 bytes antes do F7) ainda não foi decifrado
      para valores arbitrários -- por isso, por enquanto, só os valores
      capturados (0 e 100) são "seguros" para reenviar tal como estão.
"""

import sys
import mido

KNOWN_COMMANDS = {
    "gate0": [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x00, 0x06, 0x3c,
        0x31, 0x35, 0x68, 0x4b, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, 0x40, 0x01, 0x5f, 0x00, 0xF7,
    ],
    "gate100": [
        0xF0, 0x00, 0x32, 0x09, 0x31, 0x01, 0x00, 0x00, 0x02, 0x04,
        0x00, 0x00, 0x00, 0x61, 0x01, 0x00, 0x00, 0x64, 0x06, 0x3c,
        0x31, 0x35, 0x68, 0x4b, 0x25, 0x03, 0x00, 0x18, 0x18, 0x52,
        0x20, 0x40, 0x01, 0x7b, 0x01, 0xF7,
    ],
}


def list_ports():
    print("Portas MIDI de SAIDA disponiveis:")
    for name in mido.get_output_names():
        print(f"  - {name}")
    print()
    print("Portas MIDI de ENTRADA disponiveis:")
    for name in mido.get_input_names():
        print(f"  - {name}")


def find_tankg_port():
    candidates = [p for p in mido.get_output_names() if "tank" in p.lower() or "mvave" in p.lower() or "cuvave" in p.lower()]
    if candidates:
        return candidates[0]
    return None


def send_sysex(port_name, data_bytes):
    assert data_bytes[0] == 0xF0 and data_bytes[-1] == 0xF7, "SysEx precisa comecar com F0 e terminar com F7"
    inner = data_bytes[1:-1]
    msg = mido.Message("sysex", data=inner)
    with mido.open_output(port_name) as port:
        port.send(msg)
    print(f"Enviado para '{port_name}': {' '.join(f'{b:02X}' for b in data_bytes)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "list":
        list_ports()
        return

    port_name = find_tankg_port()
    if not port_name:
        print("Nao encontrei a porta automaticamente. Rode 'python tankg_control.py list'")
        print("e escolha manualmente editando a variavel PORT_NAME abaixo no script.")
        return

    print(f"Usando porta: {port_name}")

    if cmd == "replay":
        key = sys.argv[2] if len(sys.argv) > 2 else None
        if key not in KNOWN_COMMANDS:
            print(f"Comando desconhecido '{key}'. Opcoes: {list(KNOWN_COMMANDS.keys())}")
            return
        send_sysex(port_name, KNOWN_COMMANDS[key])

    elif cmd == "raw":
        hex_bytes = [int(b, 16) for b in sys.argv[2:]]
        send_sysex(port_name, hex_bytes)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
```

---

## Comandos de Ativação / Bypass de Efeitos (Comando `0x49`)

Capturas realizadas desativando (OFF) os módulos na ordem: **AMP, MOD, DLY, REV**.

### Mensagens SysEx extraídas

```text
AMP OFF: F0 00 32 09 49 00 00 00 02 00 00 00 00 11 00 00 00 00 54 03 F7
AMP ON : F0 00 32 09 49 00 00 00 02 00 00 00 00 11 00 00 00 01 52 03 F7

MOD OFF: F0 00 32 09 49 00 00 00 02 01 00 00 00 11 00 00 00 00 52 03 F7
MOD ON : F0 00 32 09 49 00 00 00 02 01 00 00 00 11 00 00 00 01 50 03 F7

DLY OFF: F0 00 32 09 49 00 00 00 02 02 00 00 00 11 00 00 00 00 50 03 F7
DLY ON : F0 00 32 09 49 00 00 00 02 02 00 00 00 11 00 00 00 01 4E 03 F7

REV OFF: F0 00 32 09 49 00 00 00 02 03 00 00 00 11 00 00 00 00 4E 03 F7
REV ON : F0 00 32 09 49 00 00 00 02 03 00 00 00 11 00 00 00 01 4C 03 F7
```

### Estrutura do comando e Fórmula do Checksum

| Índice | Byte | Descrição |
| :--- | :--- | :--- |
| 0 | `F0` | Início do SysEx MIDI |
| 1 - 2 | `00 32` | Fabricante (M-Vave / Cuvave) |
| 3 | `09` | ID do modelo (Tank-G) |
| 4 | `49` | **Tipo de Comando: Módulo Toggle / Bypass** |
| 5 - 8 | `00 00 00 02` | Sub-cabeçalho |
| **9** | **`mod_id`** | **ID do Módulo:** `00` = AMP, `01` = MOD, `02` = DLY, `03` = REV |
| 10 - 12 | `00 00 00` | Padding |
| 13 | `11` | Sub-endereço / registrador de estado |
| 14 - 16 | `00 00 00` | Padding |
| **17** | **`state`** | **Estado:** `00` = Desativado (OFF / Bypass), `01` = Ativado (ON) |
| **18** | **`ck1`** | **`0x54 - (2 * mod_id) - (2 * state)`** |
| **19** | **`ck2`** | **`0x03`** (constante) |
| 20 | `F7` | Fim do SysEx MIDI |

---

## Seleção de IR CAB (Slots 0 a 8)

Capturas realizadas alternando os gabinetes nos slots **0, 1, 4 e 8**.

### Mensagens SysEx extraídas

```text
CAB 0 (Bypass)        : F0 00 32 09 31 01 00 00 02 04 00 00 00 61 01 00 00 00 06 3C 31 35 68 4B 25 03 00 18 18 52 20 00 00 62 00 F7
CAB 1 (VHT Deliverance): F0 00 32 09 31 01 00 00 02 04 00 00 00 61 01 00 00 00 06 3C 31 35 68 4B 25 03 00 18 18 52 20 40 00 61 00 F7
CAB 4 (Mesa Boogie)   : F0 00 32 09 31 01 00 00 02 04 00 00 00 61 01 00 00 00 06 3C 31 35 68 4B 25 03 00 18 18 52 20 00 02 5E 00 F7
CAB 8 (Diezel V30)    : F0 00 32 09 31 01 00 00 02 04 00 00 00 61 01 00 00 00 06 3C 31 35 68 4B 25 03 00 18 18 52 20 00 04 5A 00 F7
```

### Anatomia e Codificação

1. **Codificação do Slot (Índices 31 e 32):**
   O slot (0 a 8) é deslocado em 6 bits para a esquerda e empacotado no formato 14-bit MIDI:
   ```python
   val_14 = cab_num << 6
   b31 = val_14 & 0x7F        # LSB 7 bits
   b32 = (val_14 >> 7) & 0x7F # MSB 7 bits
   ```
2. **Fórmula do Checksum (Índices 33 e 34):**
   ```python
   ck1 = 98 - cab_num  # 0x62 - cab_num
   ck2 = 0x00
   ```

### Tabela Completa dos 9 Slots (0 a 8)

| Slot | Modelo / Gabinete | Byte 31 | Byte 32 | Checksum (Bytes 33, 34) |
| :---: | :--- | :---: | :---: | :---: |
| **0** | CAB Desligado (Bypass) | `0x00` | `0x00` | `62 00` |
| **1** | VHT Deliverance (4x12) | `0x40` | `0x00` | `61 00` |
| **2** | Sperimental (4x12) | `0x00` | `0x01` | `60 00` |
| **3** | Electrovoice (2x10) | `0x40` | `0x01` | `5F 00` |
| **4** | Mesa Boogie (4x12) | `0x00` | `0x02` | `5E 00` |
| **5** | Fender Champ (1x8) | `0x40` | `0x02` | `5D 00` |
| **6** | Fender Pro Junior (1x10) | `0x00` | `0x03` | `5C 00` |
| **7** | Marshall 1960 V30 (4x12) | `0x40` | `0x03` | `5B 00` |
| **8** | Diezel V30 (4x12) | `0x00` | `0x04` | `5A 00` |

---

## Parâmetros do Módulo de AMP

Análise das 12 capturas com extração direta do arquivo de captura `module_amp.pcapng` alterando:
- **Type**: 9 ➔ 5 ➔ 1
- **Gain**: 100 ➔ 50 ➔ 0
- **Treble**: 100 ➔ 50 ➔ 0
- **Middle**: 100 ➔ 50 ➔ 0
- **Bass**: 100 ➔ 50 ➔ 0
- **Volume**: 100 ➔ 50 ➔ 0

### Codificação: 6 campos de 8 bits em sequência

Os 6 parâmetros do amplificador são armazenados como **6 inteiros de 8 bits** (`48 bits` no total), onde cada parâmetro de 0 a 100 é multiplicado por 2 (escala de 0.5% de resolução):

`val48 = [(type - 1) * 2] | [2 * gain] | [2 * treble] | [2 * middle] | [2 * bass] | [2 * volume]` (8 bits por campo, concatenados)

Em seguida, esse valor de 48 bits é fatiado em **sete blocos de 7 bits** (MIDI 7-bit bytes) nos índices 18 a 24 do SysEx:

```python
val48 = 0
val48 |= ((amp_type - 1) * 2) << 0   # bits  0..7
val48 |= (gain * 2)           << 8   # bits  8..15
val48 |= (treble * 2)         << 16  # bits 16..23
val48 |= (middle * 2)         << 24  # bits 24..31
val48 |= (bass * 2)           << 32  # bits 32..39
val48 |= (volume * 2)         << 40  # bits 40..47

packed_7 = [(val48 >> (7 * i)) & 0x7F for i in range(7)]  # bytes 18 a 24
```

---

## Parâmetros do Módulo de MODULAÇÃO

Análise das 7 capturas do arquivo `module_mod.pcapng` alterando:
- **MOD FX** (Chorus, Phaser, Tremolo nos 3 setores): valores 19, 43, 63, 84, 107
- **MOD SPEED**: 0 ➔ 50 ➔ 100

### Mapa completo de campos do preset

A Tank-G mapeia todos os parâmetros do preset em uma cadeia contínua de campos de 8 bits multiplicados por 2:

| Campo | Parâmetro | Faixa de Valores | Valor Armazenado (8 bits) |
| :---: | :--- | :---: | :--- |
| `0` | **Amp Type** | 1 a 9 | `(type - 1) * 2` |
| `1` | **Amp Gain** | 0 a 100 | `gain * 2` |
| `2` | **Amp Treble** | 0 a 100 | `treble * 2` |
| `3` | **Amp Middle** | 0 a 100 | `middle * 2` |
| `4` | **Amp Bass** | 0 a 100 | `bass * 2` |
| `5` | **Amp Volume** | 0 a 100 | `volume * 2` |
| `6` | **MOD FX** | 0 a 127 | `mod_fx * 2`<br>• **Setor 1: Chorus (1–40)**: `mod_fx = val - 1` (bruto: `0..39`)<br>• *Transição*: `40..43` (4 valores)<br>• **Setor 2: Phaser (1–40)**: `mod_fx = 43 + val` (bruto: `44..83`)<br>• *Transição*: `84..87` (4 valores)<br>• **Setor 3: Tremolo (1–40)**: `mod_fx = 87 + val` (bruto: `88..127`) |
| `7` | **MOD Speed** | 0 a 100 | `mod_speed * 2` |
| `8` | **DLY MIX** | 0 a 127 | `dly_mix * 2`<br>• **Setor 1: Analog Delay (1–40)**: `dly_mix = val - 1` (bruto: `0..39`)<br>• *Transição*: `40..43` (4 valores)<br>• **Setor 2: Tape Delay (1–40)**: `dly_mix = 43 + val` (bruto: `44..83`)<br>• *Transição*: `84..87` (4 valores)<br>• **Setor 3: Dual Delay (1–40)**: `dly_mix = 87 + val` (bruto: `88..127`) |
| `9` | **DLY Time** | 0 a 100 | `dly_time * 2` |
| `10` | **RVB DECAY** | 0 a 127 | `rev_decay * 2`<br>• **Setor 1: Room Reverb (1–40)**: `rev_decay = val - 1` (bruto: `0..39`)<br>• *Transição*: `40..43` (4 valores)<br>• **Setor 2: Spring Reverb (1–40)**: `rev_decay = 43 + val` (bruto: `44..83`)<br>• *Transição*: `84..87` (4 valores)<br>• **Setor 3: Cloud Reverb (1–40)**: `rev_decay = 87 + val` (bruto: `88..127`) |
| `11` | **RVB MIX** | 0 a 100 | `rev_mix * 2` |
| `12` | **Constante** | — | `0x0E` (14 decimal) |

### Checksum do preset (confere nos 33 pacotes capturados)

```python
ck = (211 - type - gain - treble - middle - bass - volume
      - mod_fx - mod_speed - dly_mix - dly_time - rev_decay - rev_mix) % 256
ck1 = ck & 0x7F
ck2 = (ck >> 7) & 0x7F
```

---

## Parâmetros do Módulo de DELAY

Análise das 7 capturas do arquivo `module_dly.pcapng` alterando:
- **DLY MIX** (Analog, Tape, Dual nos 3 setores): valores 19, 41, 63, 84, 107
- **DLY TIME**: 0 ➔ 50 ➔ 100

### Mapeamento do DLY MIX e DLY TIME

O DLY MIX usa os mesmos setores do MOD FX:
- **Setor 1 (Analog Delay):** `dly_mix = val - 1` (bruto `0..39` ➔ 40 valores).
- *Transição / Dead zone:* `40..43` (4 valores).
- **Setor 2 (Tape Delay):** `dly_mix = 43 + val` (bruto `44..83` ➔ 40 valores).
- *Transição / Dead zone:* `84..87` (4 valores).
- **Setor 3 (Dual Delay):** `dly_mix = 87 + val` (bruto `88..127` ➔ 40 valores até o teto de 7 bits `0x7F`).
- **DLY TIME:** `0..100` armazenado como `dly_time * 2` no campo 9.

---

## Parâmetros do Módulo de REVERB

Análise das 7 capturas do arquivo `module_rev.pcapng` alterando:
- **RVB DECAY** (Room, Spring, Cloud nos 3 setores): valores 19, 40, 63, 84, 107
- **RVB MIX**: 0 ➔ 50 ➔ 100

### Mapeamento do RVB DECAY e RVB MIX

- **Setor 1 (Room Reverb):** `rev_decay = val - 1` (bruto `0..39` ➔ 40 valores).
- *Transição / Dead zone:* `40..43` (4 valores).
- **Setor 2 (Spring Reverb):** `rev_decay = 43 + val` (bruto `44..83` ➔ 40 valores).
- *Transição / Dead zone:* `84..87` (4 valores).
- **Setor 3 (Cloud Reverb):** `rev_decay = 87 + val` (bruto `88..127` ➔ 40 valores até o teto de 7 bits `0x7F`).
- **RVB MIX:** `0..100` armazenado como `rev_mix * 2` no campo 11.

---

## Troca de Presets e Bancos (1A a 9D — 36 Presets)

Análise das 7 capturas do arquivo `slot-and-bank-switch.pcapng` trocando presets em sequência:
- Banco 3: 3A ➔ 3B ➔ 3C ➔ 3D
- Banco 4: 4A ➔ 4B ➔ 4C ➔ 4D

### Estrutura do Comando SysEx (21 bytes)

```text
F0 00 32 09 49 00 00 00 02 [preset_id] 00 00 00 1E 00 00 00 01 [ck1] [ck2] F7
```

- **ID do Preset:** `preset_id = (bank - 1) * 4 + slot_index` (faixa: `0` a `35`)
  - Banco 1: `1A = 0`, `1B = 1`, `1C = 2`, `1D = 3`
  - Banco 2: `2A = 4`, `2B = 5`, `2C = 6`, `2D = 7`
  - Banco 3: `3A = 8`, `3B = 9`, `3C = 10`, `3D = 11`
  - Banco 4: `4A = 12`, `4B = 13`, `4C = 14`, `4D = 15`
  - ...
  - Banco 9: `9A = 32`, `9B = 33`, `9C = 34`, `9D = 35`
- **Sub-endereço / Registrador:** `0x1E` (30 decimal)
- **Fórmula do Checksum:**
  ```python
  ck = (50 - 2 * preset_id) % 256
  ck1 = ck & 0x7F
  ck2 = (ck >> 7) & 0x7F
  ```

---

## Gravação de Presets na Memória EEPROM (Comando `0x69`)

Análise das capturas `save-preset-1a.pcapng`, `save-preset-3c.pcapng` e `save-preset.pcapng`:

### 1. Formato do Pacote SysEx (44 bytes)
```text
F0 00 32 09 69 01 00 00 02 [b9] [b10] 00 00 50 02 00 00 [24 bytes fatiados em 7-bit] [ck1] [ck2] F7
```

### 2. Endereçamento na Memória EEPROM
Cada preset ocupa exatamente 21 bytes. O endereço inicial é:
```python
offset = preset_id * 21 + 2
b9 = offset & 0x7F
b10 = (offset >> 7) & 0x7F
```

- **1A** (`preset_id = 0`): `offset = 2` → `b9 = 0x02`, `b10 = 0x00`
- **3B** (`preset_id = 9`): `offset = 191` → `b9 = 0x3F`, `b10 = 0x01`
- **3C** (`preset_id = 10`): `offset = 212` → `b9 = 0x54`, `b10 = 0x01`

### 3. Estrutura dos 21 Bytes de Dados do Preset
1. `fields[0..3]`: Estados dos módulos (`AMP`, `MOD`, `DLY`, `REV` - `0` ou `1`)
2. `fields[4]`: **Noise Gate** (`0..100`)
3. `fields[5]`: **Amp Type** (`1..9`)
4. `fields[6..10]`: **Gain**, **Treble**, **Middle**, **Bass**, **Volume** (`0..100`)
5. `fields[11..12]`: **MOD FX** (`0..127`) e **MOD Speed** (`0..100`)
6. `fields[13..14]`: **DLY Mix** (`0..127`) e **DLY Time** (`0..100`)
7. `fields[15..16]`: **REV Decay** (`0..127`) e **REV Mix** (`0..100`)
8. `fields[17]`: **IR CAB** (`0..8`)
9. `fields[18..20]`: Constantes (`255, 0, 0`)

### 4. Checksum (confere em todas as capturas de gravação)
```python
ck = (230 - sum(fields[0:21]) - offset) % 256
ck1 = ck & 0x7F
ck2 = (ck >> 7) & 0x7F
```

### 5. Sequência Completa de Gravação
1. **Comando `0x69` (Write EEPROM):** envia os 21 bytes para o endereço calculado.
2. **Comando `0x41` (Flush):** confirma e consolida a gravação (`F0 00 32 09 41 00 00 00 02 00 00 00 00 0F 00 00 00 0B 00 F7`).
3. **Comando `0x49` (Select):** seleciona o preset gravado para ativação imediata.

---

## Status

Todos os itens planejados no início da pesquisa foram concluídos:

- [x] Checksum do noise gate decifrado e generalizado para todos os parâmetros do preset (`0x31`)
- [x] Bypass de módulos (`0x49` / `0x11`), IR CAB, troca de presets (`0x49` / `0x1E`)
- [x] Gravação permanente na EEPROM (`0x69` → `0x41` → `0x49`)
- [x] Geração dinâmica de SysEx para qualquer valor, implementada em [`tankg/services/sysex_codec.py`](../tankg/services/sysex_codec.py)

Ainda em aberto: ler as respostas do pedal (`mido.open_input`) para confirmar que cada comando foi aceito.
