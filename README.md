# 🏎️⚽ **TechBall – Sistema completo de Futebol de Carrinhos (Rocket League IRL)**  
### 🔥 Controle por Bluetooth + Website em Python + MySQL + Sensores IR

O **TechBall** é um projeto completo de futebol de carrinhos inspirado em *Rocket League*, desenvolvido como integração entre **Arduino**, **Python (Flask)**, **MySQL**, sensores de **infravermelho** e controle Bluetooth.  
Criado como projeto acadêmico e apresentado na **Feira de Profissões da Universidade**, ele demonstra automação, eletrônica, programação web, banco de dados e interação em tempo real.

---

## 🧠 **Visão Geral do Sistema**

A arena contém:

- 🟠 **Time Laranja** — controlado via Bluetooth  
- 🔵 **Time Azul** — também por Bluetooth  
- ⚽ **Bola física**  
- 🥅 **Dois gols**, cada um equipado com um **sensor infravermelho (IR)**

Quando a bola cruza a linha do gol, o sensor detecta a interrupção do feixe IR e envia o evento ao sistema Python, que atualiza automaticamente o placar no website.

---

## 🔌 **Fluxo Completo do Projeto**

### **1️⃣ Carrinhos**
- Controlados por **Bluetooth HC-06**  
- Programados no Arduino com drivers **L298N** para os motores  
- Cada carrinho representa um time (L Laranja x Azul)

### **2️⃣ Arena e Sensores**
- Cada gol possui um **sensor IR** voltado ao centro  
- Quando a bola passa → feixe é bloqueado → sensor envia sinal ao Arduino  
- Arduino repassa ao Python via porta serial → Python atualiza o placar em tempo real

### **3️⃣ Website (Flask)**
Localizado na pasta **`templates/`** (HTML) e **`static/`** (CSS/JS).  
Ele permite:

- Cadastro de jogadores  
- Início e monitoramento da partida  
- Placar em tempo real com detecção automática de gols  
- Finalização da partida com gravação dos dados no banco

### **4️⃣ Banco de Dados (MySQL)**
O sistema registra:

- 👤 Jogadores cadastrados  
- ⚽ Partidas realizadas  
- 📝 Gols detectados pelos sensores  
- 🏆 Histórico completo para gerar **ranking geral**

Toda a estrutura está em `futebol_carros.sql`.

### **5️⃣ Ranking**
Após cada partida, o sistema salva:

- Jogadores  
- Quantidade de gols  
- Resultado final  
- Data, hora e histórico  

O website exibe depois um **ranking geral** entre todos os jogadores.

---

## 🗂️ **Estrutura do Projeto**

```
📁 Projeto carrinho.arduino/
│
├── static/               # CSS e arquivos visuais
├── templates/            # Interface HTML
│
├── app.py                # Servidor Flask + lógica principal
├── listener_bt.py        # Recepção de dados via Bluetooth
├── carrinho1.py          # Controle carrinho time azul
├── carrinho2.py          # Controle carrinho time laranja
├── futebol_carros.sql    # Banco MySQL
└── venv/                 # Ambiente virtual
```

---

## ⚙️ **Tecnologias Utilizadas**

### **Back-end**
- Python (Flask)
- PySerial (comunicação com Arduino)
- MySQL Connector

### **Front-end**
- HTML5  
- CSS3  
- Templates Flask

### **Hardware**
- Arduino Uno  
- Bluetooth HC-06  
- Motores DC  
- Ponte H L298N  
- Sensores IR para detecção de gols  

---


## 🚀 **Como Executar o Projeto**

### 1️⃣ Instale as dependências
```bash
pip install flask pyserial mysql-connector-python
```

### 2️⃣ Configure o banco MySQL
Importe o arquivo:
```
futebol_carros.sql
```

### 3️⃣ Inicie o listener Bluetooth
```bash
python listener_bt.py
```

### 4️⃣ Abra o servidor Flask
```bash
python app.py
```

### 5️⃣ Acesse no navegador
```
http://localhost:5000
```

---

## 🎯 **Objetivo do Projeto**

Demonstrar a integração entre:

- Automação  
- Robótica  
- Comunicação Bluetooth  
- Desenvolvimento Web  
- Banco de Dados MySQL  

Criando um sistema funcional, gamificado e inovador, inspirado em *Rocket League*.

---


