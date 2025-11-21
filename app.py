from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.secret_key = "segredo_forte_aqui"  # 🔒 mantenha seguro em produção

# ----------------------------------------------------------------------
# 🔹 CONEXÃO COM O BANCO
# ----------------------------------------------------------------------
def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="lamball",  # ajuste conforme o seu ambiente
            database="futebol_carros"
        )
    except Error as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        raise

# ----------------------------------------------------------------------
# 🔹 DESATIVA CACHE DO NAVEGADOR
# ----------------------------------------------------------------------
@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# ----------------------------------------------------------------------
# 🔹 LOGIN / CADASTRO
# ----------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        acao = request.form.get("acao")

        # 🧍‍♂️ Login duplo
        if acao == "login_duplo":
            jogador1 = request.form.get("jogador1", "").strip()
            jogador2 = request.form.get("jogador2", "").strip()

            if not jogador1 or not jogador2:
                flash("⚠️ Informe os nomes dos dois jogadores.", "erro")
                return redirect(url_for("login"))

            db = get_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute("SELECT * FROM Jogador WHERE nome IN (%s, %s)", (jogador1, jogador2))
            jogadores = cursor.fetchall()

            if len(jogadores) != 2:
                flash("⚠️ Um ou ambos os jogadores não foram encontrados. Cadastre-os primeiro.", "erro")
                cursor.close(); db.close()
                return redirect(url_for("login"))

            # verifica se já há jogadores logados
            cursor.execute("SELECT COUNT(*) AS total FROM LoginsAtivos")
            if cursor.fetchone()["total"] > 0:
                flash("⚠️ Já existem jogadores logados. Aguarde terminar a partida.", "erro")
                cursor.close(); db.close()
                return redirect(url_for("login"))

            for j in jogadores:
                cursor.execute("INSERT IGNORE INTO LoginsAtivos (id_jogador) VALUES (%s)", (j["id_jogador"],))

            db.commit()
            cursor.close(); db.close()

            # salva sessão
            session["jogador_id"] = jogadores[0]["id_jogador"]
            session["jogador_nome"] = jogadores[0]["nome"]

            return redirect(url_for("nova_partida"))

        # 🧾 Cadastro
        elif acao == "cadastrar":
            nome = request.form.get("nome", "").strip()
            if not nome:
                flash("⚠️ Informe um nome válido.", "erro")
                return redirect(url_for("login"))

            db = get_connection()
            cursor = db.cursor()
            try:
                cursor.execute("INSERT INTO Jogador (nome) VALUES (%s)", (nome,))
                db.commit()
                flash("✅ Jogador cadastrado com sucesso!", "sucesso")
            except Error as e:
                if e.errno == 1062:
                    flash("⚠️ Esse jogador já existe.", "erro")
                else:
                    flash(f"❌ Erro: {e}", "erro")
            finally:
                cursor.close(); db.close()

            return redirect(url_for("login"))

    return render_template("login.html")

# ----------------------------------------------------------------------
# 🔹 NOVA PARTIDA
# ----------------------------------------------------------------------
@app.route("/nova_partida")
def nova_partida():
    if "jogador_id" not in session:
        return redirect(url_for("login"))

    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT j.id_jogador, j.nome
        FROM LoginsAtivos l
        JOIN Jogador j ON j.id_jogador = l.id_jogador
    """)
    jogadores = cursor.fetchall()
    cursor.close(); db.close()

    if len(jogadores) != 2:
        flash("⚠️ É necessário ter exatamente 2 jogadores logados para iniciar.", "erro")
        return redirect(url_for("login"))

    return render_template("nova_partida.html", jogadores=jogadores)

# ----------------------------------------------------------------------
# 🔹 INICIAR PARTIDA (marca como ativa)
# ----------------------------------------------------------------------
@app.route("/iniciar_partida", methods=["POST"])
def iniciar_partida():
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    # jogadores logados
    cursor.execute("""
        SELECT DISTINCT j.id_jogador, j.nome
        FROM LoginsAtivos l
        JOIN Jogador j ON j.id_jogador = l.id_jogador
    """)
    jogadores = cursor.fetchall()

    if len(jogadores) != 2:
        cursor.close(); db.close()
        flash("⚠️ É necessário 2 jogadores logados para iniciar.", "erro")
        return redirect(url_for("login"))

    # desativa qualquer partida antiga e cria a nova
    cursor.execute("UPDATE Partida SET ativa = 0 WHERE ativa = 1")
    cursor.execute("INSERT INTO Partida (data_partida, ativa) VALUES (NOW(), 1)")
    id_partida = cursor.lastrowid

    # vincula os dois jogadores
    cursor.executemany(
        "INSERT INTO Participa (id_partida, id_jogador) VALUES (%s, %s)",
        [(id_partida, j["id_jogador"]) for j in jogadores]
    )
    db.commit()
    cursor.close(); db.close()

    # 🔹 volta para a tela de login (apenas limpa a sessão; NÃO mexe em LoginsAtivos)
    session.clear()
    flash("🚀 Partida iniciada! O placar será atualizado no outro monitor.", "sucesso")
    return redirect(url_for("login"))

# ----------------------------------------------------------------------
# 🔹 PÁGINA DA PARTIDA
# ----------------------------------------------------------------------
@app.route("/partida/<int:id_partida>")
def partida(id_partida):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    # checa se está ativa
    cursor.execute("SELECT ativa FROM Partida WHERE id_partida = %s", (id_partida,))
    row = cursor.fetchone()
    ativa = bool(row["ativa"]) if row else False

    # pega (ou não) jogadores
    cursor.execute("""
        SELECT j.id_jogador, j.nome
        FROM Participa p
        JOIN Jogador j ON j.id_jogador = p.id_jogador
        WHERE p.id_partida = %s
    """, (id_partida,))
    jogadores = cursor.fetchall()
    cursor.close(); db.close()

    if len(jogadores) != 2:
        jogadores = [{"nome": "null"}, {"nome": "null"}]

    return render_template(
        "partida.html",
        id_partida=id_partida,
        jogadores=jogadores,
        partida_ativa=ativa
    )


# ----------------------------------------------------------------------
# 🔹 REGISTRAR GOL VIA HTML
# ----------------------------------------------------------------------
@app.route("/registrar_gol/<int:id_jogador>/<int:id_partida>", methods=["POST"])
def registrar_gol(id_jogador, id_partida):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO Gol (id_partida, id_jogador) VALUES (%s, %s)", (id_partida, id_jogador))
    db.commit()
    cursor.close(); db.close()
    return Response(status=204)

# ----------------------------------------------------------------------
# 🔹 REGISTRAR GOL VIA ARDUINO
# ----------------------------------------------------------------------
@app.route("/api/registrar_gol_arduino", methods=["POST"])
def registrar_gol_arduino():
    data = request.get_json()
    id_partida = data.get("id_partida")
    id_jogador = data.get("id_jogador")

    if not id_partida or not id_jogador:
        return jsonify({"erro": "Faltando dados"}), 400

    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT data_partida, ativa FROM Partida WHERE id_partida = %s", (id_partida,))
        partida = cursor.fetchone()

        if not partida:
            return jsonify({"erro": "Partida não encontrada"}), 404
        if not partida["ativa"]:
            return jsonify({"erro": "Partida encerrada"}), 403

        duracao = datetime.now() - partida["data_partida"]
        minuto = max(0, int(duracao.total_seconds() // 60))

        cursor.execute("""
            INSERT INTO Gol (id_partida, id_jogador, minuto)
            VALUES (%s, %s, %s)
        """, (id_partida, id_jogador, minuto))
        db.commit()
        cursor.close(); db.close()

        print(f"⚽ Gol registrado: jogador {id_jogador}, partida {id_partida}, minuto {minuto}")
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"❌ Erro ao registrar gol: {e}")
        return jsonify({"erro": str(e)}), 500

# ----------------------------------------------------------------------
# 🔹 ENCERRAR PARTIDA
# ----------------------------------------------------------------------
@app.route("/encerrar_partida/<int:id_partida>", methods=["POST"])
def encerrar_partida(id_partida):
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT j.nome, COUNT(g.id_gol) AS gols
        FROM Gol g
        JOIN Jogador j ON j.id_jogador = g.id_jogador
        WHERE g.id_partida = %s
        GROUP BY j.id_jogador
    """, (id_partida,))
    resultados = cursor.fetchall()

    resultado_final = " x ".join([f"{r['nome']} {r['gols']}" for r in resultados]) if resultados else "Sem gols"

    cursor.execute("SELECT data_partida FROM Partida WHERE id_partida = %s", (id_partida,))
    inicio = cursor.fetchone()["data_partida"]

    fim = datetime.now()
    duracao = fim - inicio
    duracao_str = str(duracao).split(".")[0]

    cursor.execute("""
        UPDATE Partida
        SET resultado_final = %s, duracao = %s, ativa = 0
        WHERE id_partida = %s
    """, (resultado_final, duracao_str, id_partida))
    db.commit()

    cursor.execute("DELETE FROM LoginsAtivos")
    db.commit()
    cursor.close(); db.close()

    session.clear()
    print(f"🏁 Partida {id_partida} encerrada com resultado: {resultado_final}")
    return Response(status=204)

# ----------------------------------------------------------------------
# 🔹 PLACAR PÚBLICO (usa partida.html)
# ----------------------------------------------------------------------
@app.route("/placar")
def partida_publica():
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id_partida FROM Partida WHERE ativa = 1 ORDER BY id_partida DESC LIMIT 1")
    partida = cursor.fetchone()
    cursor.close(); db.close()

    if not partida:
        # sem partida: nomes "null", id_partida=0 e partida_ativa=False
        jogadores = [{"nome": "null"}, {"nome": "null"}]
        return render_template("partida.html",
                               id_partida=0,
                               jogadores=jogadores,
                               partida_ativa=False)

    # com partida ativa, envia para a rota que renderiza com os nomes reais
    return redirect(url_for("partida", id_partida=partida["id_partida"]))


# ----------------------------------------------------------------------
# 🔹 PARTIDA ATIVA
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 🔹 API: PARTIDA ATIVA (usada pelo placar)
# ----------------------------------------------------------------------
@app.route("/api/partida_ativa", methods=["GET"])
def api_partida_ativa():
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # verifica se há partida ativa
        cursor.execute("SELECT id_partida FROM Partida WHERE ativa = 1 ORDER BY id_partida DESC LIMIT 1")
        partida = cursor.fetchone()

        if not partida:
            cursor.close(); db.close()
            return jsonify({"ativa": False})

        id_partida = partida["id_partida"]

        # busca os jogadores da partida ativa
        cursor.execute("""
            SELECT j.id_jogador, j.nome
            FROM Participa p
            JOIN Jogador j ON j.id_jogador = p.id_jogador
            WHERE p.id_partida = %s
        """, (id_partida,))
        jogadores = cursor.fetchall()

        cursor.close(); db.close()

        return jsonify({
            "ativa": True,
            "id_partida": id_partida,
            "jogadores": jogadores
        })

    except Exception as e:
        print(f"❌ Erro em /api/partida_ativa: {e}")
        return jsonify({"ativa": False, "erro": str(e)}), 500




# ----------------------------------------------------------------------
# 🔹 RANKING
# ----------------------------------------------------------------------
@app.route("/ranking")
def ranking():
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    ranking = []

    try:
        cursor.callproc("GetRanking")
        for result in cursor.stored_results():
            ranking = result.fetchall()

        if not ranking:
            cursor.execute("""
                SELECT nome, (vitorias*3 + empates) AS pontos,
                       vitorias, empates, derrotas, 
                       gols_marcados, gols_sofridos, saldo_gols
                FROM ViewRanking
                ORDER BY pontos DESC, saldo_gols DESC, vitorias DESC, nome ASC
            """)
            ranking = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro MySQL: {err}")
        cursor.execute("""
            SELECT nome, (vitorias*3 + empates) AS pontos,
                   vitorias, empates, derrotas, 
                   gols_marcados, gols_sofridos, saldo_gols
            FROM ViewRanking
            ORDER BY pontos DESC, saldo_gols DESC, vitorias DESC, nome ASC
        """)
        ranking = cursor.fetchall()
    finally:
        cursor.close()
        db.close()

    return render_template("ranking.html", ranking=ranking)

# ----------------------------------------------------------------------
# 🔹 API STATUS (tempo real)
# ----------------------------------------------------------------------
@app.route("/api/status_partida/<int:id_partida>", methods=["GET"])
def status_partida(id_partida):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT j.nome, COUNT(g.id_gol) AS gols
            FROM Participa p
            JOIN Jogador j ON j.id_jogador = p.id_jogador
            LEFT JOIN Gol g ON g.id_jogador = j.id_jogador AND g.id_partida = p.id_partida
            WHERE p.id_partida = %s
            GROUP BY j.nome
        """, (id_partida,))
        placar = cursor.fetchall()
        cursor.close(); db.close()
        return jsonify(placar), 200
    except Exception as e:
        print(f"❌ Erro em /api/status_partida: {e}")
        return jsonify({"erro": str(e)}), 500

# ----------------------------------------------------------------------
# 🔹 LOGOUT
# ----------------------------------------------------------------------
@app.route("/logout", methods=["GET", "POST"])
def logout():
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM LoginsAtivos")
    db.commit()
    cursor.close(); db.close()
    session.clear()
    if request.method == "POST":
        return Response(status=204)
    flash("Todos os jogadores foram deslogados.", "sucesso")
    return redirect(url_for("login"))

# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
