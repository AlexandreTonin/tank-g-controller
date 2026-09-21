# Guia Técnico de Parâmetros e Módulos — M-Vave Tank-G

Este documento reúne todas as especificações técnicas, slots de amplificadores, gabinetes (IR CAB), módulos de efeito, setores de ajuste e funções dos footswitches para uso tanto no hardware quanto no aplicativo (M-EFCS).

---

## 1. Módulo AMP (Modelos de Pré-amplificador)

A Tank-G conta com 9 slots de amplificador pré-definidos:

| Slot | Modelo de Referência | Estilo / Categoria Sonora |
| :---: | :--- | :--- |
| **1** | VOX AC30HW Normal | Clean britânico, brilhante e articulado |
| **2** | Fender '65 Twin Reverb | Clean americano, encorpado, headroom alto |
| **3** | Bogner Shiva | Overdrive boutique, médio quente e macio |
| **4** | Marshall JTM45 OD | Overdrive vintage, dinâmico e clássico |
| **5** | Marshall Plexi 100 | Overdrive/Crunch saturado, rock anos 60/70 |
| **6** | Marshall JCM800 | Distorção clássica do hard rock e heavy metal |
| **7** | EVH 5150 LEAD | High Gain moderno, agressivo, harmônicos fáceis |
| **8** | ENGL Powerball E645/2 | High Gain moderno europeu, foco em peso e precisão |
| **9** | Mesa Boogie Dual Rectifier | Distorção moderna pesada, graves cheios |

### Parâmetros do AMP:
* **TYPE:** 1 a 9
* **GAIN:** 1 a 100
* **TREBLE:** 1 a 100
* **MIDDLE:** 1 a 100
* **BASS:** 1 a 100
* **VOLUME:** 1 a 100

---

## 2. Módulo IR CAB (Simulações de Gabinete)

A pedaleira conta com 8 slots de IR de fábrica (e a opção 0 para desativar):

| Slot | Simulação de Gabinete | Configuração de Falantes |
| :---: | :--- | :---: |
| **0** | CAB IR Desligado | Nenhum (Bypass) |
| **1** | VHT Deliverance | 4x12 |
| **2** | Sperimental | 4x12 |
| **3** | Electrovoice | 2x10 |
| **4** | Mesa Boogie | 4x12 |
| **5** | Fender Champ | 1x8 |
| **6** | Fender Pro Junior | 1x10 |
| **7** | Marshall 1960 V30 | 4x12 |
| **8** | Diezel V30 | 4x12 |

*Nota: Pelo aplicativo/computador, é possível carregar IRs de terceiros (arquivos `.wav`) em qualquer um dos 8 slots.*

---

## 3. Módulos de Efeito e Dinâmica

### 3.1. NOISE GATE
* **GATE:** 1 a 100 (No hardware: todo para a esquerda desliga o módulo).

---

### 3.2. MOD (Modulação)
O controle **MOD FX** é dividido em 3 processos contínuos (setores). Nas transições entre os setores, o efeito é desligado.

* **MOD FX (Setores 1 a 40):**
  * **Setor 1 (1–40):** **Chorus** (ajusta o parâmetro MIX do Chorus).
  * **Transição:** Efeito OFF.
  * **Setor 2 (1–40):** **Phaser** (ajusta o parâmetro DEPTH do Phaser).
  * **Transição:** Efeito OFF.
  * **Setor 3 (1–40):** **Tremolo** (ajusta o parâmetro MIX do Tremolo).
* **MOD SPEED:** 1 a 100 (velocidade da oscilação da modulação).

---

### 3.3. DLY (Delay)
O controle **DLY MIX** seleciona o algoritmo através de 3 setores contínuos e ajusta o nível de mistura (Mix). Nas transições, o efeito fica em bypass.

* **DLY MIX (Setores 1 a 40):**
  * **Setor 1 (1–40):** **Analog Delay** (repetições mais escuras e quentes).
  * **Transição:** Efeito OFF.
  * **Setor 2 (1–40):** **Tape Delay** (eco de fita com saturação sutil).
  * **Transição:** Efeito OFF.
  * **Setor 3 (1–40):** **Dual Delay** (linhas duplas de atraso estéreo/rítmico).
* **DLY TIME:** 1 a 100 (tempo de repetição / feedback).

---

### 3.4. REV (Reverb)
O controle **RVB DECAY** seleciona o algoritmo de reverb através de 3 setores e define o tempo de decaimento (cauda). Nas transições, o módulo é desligado.

* **RVB DECAY (Setores 1 a 40):**
  * **Setor 1 (1–40):** **Room Reverb** (reflexão curta de sala).
  * **Transição:** Efeito OFF.
  * **Setor 2 (1–40):** **Spring Reverb** (reverb clássico de mola vintage).
  * **Transição:** Efeito OFF.
  * **Setor 3 (1–40):** **Cloud Reverb** (reverb atmosférico, difuso e longo).
* **RVB MIX:** 1 a 100 (proporção de sinal limpo e sinal molhado).

---

## 4. Pedais (Footswitches) e Modos de Operação

A Tank-G possui 4 interruptores de pé principais (**A, B, C, D**). 

A troca entre **Modo PRESET** e **Modo LIVE** é feita pressionando simultaneamente os pedais **B + C**.

### 4.1. Modo PRESET (Navegação de Memórias)
O sistema possui 9 bancos, cada um com 4 presets (totalizando 36 slots).
* **Footswitch A:** Seleciona o preset **A** do banco atual.
* **Footswitch B:** Seleciona o preset **B** do banco atual.
* **Footswitch C:** Seleciona o preset **C** do banco atual.
* **Footswitch D:** Seleciona o preset **D** do banco atual.
* **Troca de Bancos (Bank - / Bank +):** Feita através das combinações de footswitch designadas ou via aplicativo.

### 4.2. Modo LIVE (Controle Individual de Blocos)
No modo manual, os botões ligam e desligam blocos da cadeia de sinal:
* **Footswitch A:** Liga / Desliga o bloco **REVERB**.
* **Footswitch B:** Liga / Desliga o bloco **DELAY**.
* **Footswitch C:** Liga / Desliga o bloco **MOD** (Modulação).
* **Footswitch D:** Liga / Desliga o bloco **AMP** (Pré-amplificador).

### 4.3. Funções Especiais dos Footswitches
* **Afinador (TUNER):** Segurar **B + C por 2 segundos**. A saída da guitarra é mutada. Toque em B + C novamente para sair.
* **Bluetooth (BT):** Segurar **B + C por 3 segundos** para ativar ou desativar a conexão sem fio.