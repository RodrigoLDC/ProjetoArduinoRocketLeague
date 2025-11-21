import serial
import requests
import time
import mysql.connector
from datetime import datetime

# ======================================================
# 🔹 CONFIGURAÇÕES GERAIS
# ======================================================
PORTA = "COM22"  # ajuste conforme sua porta do HC-06
BAUDRATE = 9600
API_URL = "http://127.0.0.1:5000/api/registrar_gol_arduino"  # endpoint do Flask

# ======================================================
# 🔹 CONEXÃO COM BANCO DE DADOS
# ======================================================
def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="lamball",  # ajuste conforme o seu ambiente
            database="futebol_carros"
        )
    except mysql.connector.Error as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        exit()

# ======================================================
# 🔹 BUSCA PARTIDA ATIVA E JOGADORES
# ======================================================
def get_partida_e_jogadores():
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id_partida, j.id_jogador, j.nome
        FROM Partida p
        JOIN Participa pa ON pa.id_partida = p.id_partida
        JOIN Jogador j ON j.id_jogador = pa.id_jogador
        WHERE p.ativa = 1
    """)

    dados = cursor.fetchall()
    cursor.close()
    db.close()
    return dados

# ======================================================
# 🔹 INICIALIZA BLUETOOTH
# ======================================================
try:
    bt = serial.Serial(PORTA, BAUDRATE, timeout=1)
    time.sleep(2)
    print("✅ Conectado ao módulo Bluetooth HC-06!")
except Exception as e:
    print(f"❌ Erro ao conectar ao Bluetooth: {e}")
    exit()

# ======================================================
# 🔹 FUNÇÃO DE CHECAGEM DE PARTIDA ATIVA
# ======================================================
def aguardar_partida_ativa():
    """Fica verificando a cada 3s até encontrar uma partida ativa"""
    while True:
        dados = get_partida_e_jogadores()
        if len(dados) >= 2:
            print("\n🎮 Partida ativa encontrada!")
            print(f"👥 Jogadores: {dados[0]['nome']} x {dados[1]['nome']}")
            print("📡 Aguardando eventos de gol...\n")
            return dados
        else:
            print("⏳ Nenhuma partida ativa. Aguardando...")
            time.sleep(3)

# ======================================================
# 🔹 LOOP PRINCIPAL
# ======================================================
jogadores_ativos = aguardar_partida_ativa()
partida_atual = jogadores_ativos[0]["id_partida"]

while True:
    try:
        # Se a partida for encerrada, tenta reconectar a cada 3s
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT ativa FROM Partida WHERE id_partida = %s", (partida_atual,))
        status = cursor.fetchone()
        cursor.close()
        db.close()

        if not status or not status["ativa"]:
            print("🏁 Partida encerrada! Aguardando nova...")
            jogadores_ativos = aguardar_partida_ativa()
            partida_atual = jogadores_ativos[0]["id_partida"]
            continue

        # Escuta Bluetooth
        if bt.in_waiting > 0:
            dado = bt.readline().decode("utf-8").strip()
            if not dado:
                continue

            print(f"📲 Recebido do Arduino: {dado}")

            # Identifica o jogador que marcou
            if dado == "GOL_1":
                id_jogador = jogadores_ativos[0]["id_jogador"]
                nome_jogador = jogadores_ativos[0]["nome"]
            elif dado == "GOL_2":
                id_jogador = jogadores_ativos[1]["id_jogador"]
                nome_jogador = jogadores_ativos[1]["nome"]
            else:
                continue  # ignora mensagens desconhecidas

            # Envia ao Flask
            payload = {"id_partida": partida_atual, "id_jogador": id_jogador}
            try:
                resposta = requests.post(API_URL, json=payload, timeout=5)
                if resposta.status_code == 200:
                    print(f"⚽ Gol de {nome_jogador} registrado com sucesso!")
                else:
                    print(f"⚠️ Erro {resposta.status_code}: {resposta.text}")
            except requests.exceptions.RequestException as e:
                print(f"🚫 Falha ao enviar para o Flask: {e}")

        time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Encerrando listener...")
        bt.close()
        break

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        time.sleep(1)
