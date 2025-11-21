CREATE DATABASE futebol_carros;
USE futebol_carros;

CREATE TABLE jogador (
  id_jogador int NOT NULL AUTO_INCREMENT,
  nome varchar(100) NOT NULL,
  PRIMARY KEY (id_jogador),
  UNIQUE KEY nome (nome)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE partida (
  id_partida int NOT NULL AUTO_INCREMENT,
  duracao time DEFAULT NULL,
  resultado_final varchar(20) DEFAULT NULL,
  data_partida timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_partida)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE participa (
  id_jogador int NOT NULL,
  id_partida int NOT NULL,
  PRIMARY KEY (id_jogador,id_partida),
  KEY id_partida (id_partida),
  CONSTRAINT participa_ibfk_1 FOREIGN KEY (id_jogador) REFERENCES jogador (id_jogador),
  CONSTRAINT participa_ibfk_2 FOREIGN KEY (id_partida) REFERENCES partida (id_partida)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE gol (
  id_gol int NOT NULL AUTO_INCREMENT,
  id_partida int DEFAULT NULL,
  id_jogador int DEFAULT NULL,
  minuto int DEFAULT NULL,
  PRIMARY KEY (id_gol),
  KEY id_partida (id_partida),
  KEY id_jogador (id_jogador),
  CONSTRAINT gol_ibfk_1 FOREIGN KEY (id_partida) REFERENCES partida (id_partida),
  CONSTRAINT gol_ibfk_2 FOREIGN KEY (id_jogador) REFERENCES jogador (id_jogador)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE loginsativos (
  id int NOT NULL AUTO_INCREMENT,
  id_jogador int NOT NULL,
  data_login timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY id_jogador (id_jogador),
  CONSTRAINT loginsativos_ibfk_1 FOREIGN KEY (id_jogador) REFERENCES jogador (id_jogador)
) ENGINE=InnoDB AUTO_INCREMENT=154 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE historicopartida (
  id int NOT NULL AUTO_INCREMENT,
  id_partida int DEFAULT NULL,
  id_jogador int DEFAULT NULL,
  gols_feitos int DEFAULT NULL,
  gols_sofridos int DEFAULT NULL,
  resultado enum('vitoria','empate','derrota') DEFAULT NULL,
  PRIMARY KEY (id),
  KEY id_partida (id_partida),
  KEY id_jogador (id_jogador),
  CONSTRAINT historicopartida_ibfk_1 FOREIGN KEY (id_partida) REFERENCES partida (id_partida),
  CONSTRAINT historicopartida_ibfk_2 FOREIGN KEY (id_jogador) REFERENCES jogador (id_jogador)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE VIEW ViewRanking AS
SELECT
    j.id_jogador,
    j.nome,

    /* Pontos por partida: vitória = 3, empate = 1, derrota = 0 */
    COALESCE(SUM(
        CASE 
            WHEN m.gols > m.gols_op THEN 3
            WHEN m.gols = m.gols_op THEN 1
            ELSE 0
        END
    ), 0) AS pontos,

    /* Contagens */
    COALESCE(SUM(CASE WHEN m.gols > m.gols_op THEN 1 ELSE 0 END), 0) AS vitorias,
    COALESCE(SUM(CASE WHEN m.gols = m.gols_op THEN 1 ELSE 0 END), 0) AS empates,
    COALESCE(SUM(CASE WHEN m.gols < m.gols_op THEN 1 ELSE 0 END), 0) AS derrotas,

    /* Gols */
    COALESCE(SUM(m.gols), 0) AS gols_marcados,
    COALESCE(SUM(m.gols_op), 0) AS gols_sofridos,
    COALESCE(SUM(m.gols - m.gols_op), 0) AS saldo_gols

FROM Jogador j
LEFT JOIN (
    /* Para cada partida e jogador, traga gols do jogador e do oponente */
    SELECT 
        s1.id_partida,
        s1.id_jogador,
        s1.gols AS gols,
        s2.gols AS gols_op
    FROM (
        SELECT 
            pa.id_partida, 
            pa.id_jogador, 
            COUNT(g.id_gol) AS gols
        FROM Participa pa
        LEFT JOIN Gol g
            ON g.id_partida = pa.id_partida
           AND g.id_jogador = pa.id_jogador
        GROUP BY pa.id_partida, pa.id_jogador
    ) s1
    JOIN (
        SELECT 
            pa.id_partida, 
            pa.id_jogador, 
            COUNT(g.id_gol) AS gols
        FROM Participa pa
        LEFT JOIN Gol g
            ON g.id_partida = pa.id_partida
           AND g.id_jogador = pa.id_jogador
        GROUP BY pa.id_partida, pa.id_jogador
    ) s2
        ON s1.id_partida = s2.id_partida
       AND s1.id_jogador <> s2.id_jogador
) m
    ON m.id_jogador = j.id_jogador
GROUP BY 
    j.id_jogador, 
    j.nome
ORDER BY 
    pontos DESC, 
    saldo_gols DESC, 
    vitorias DESC, 
    nome ASC;
    

DELIMITER $$

CREATE PROCEDURE GetRanking()
BEGIN
    SELECT 
        v.nome,
        COALESCE(v.pontos, 0) AS pontos,
        COALESCE(v.vitorias, 0) AS vitorias,
        COALESCE(v.empates, 0) AS empates,
        COALESCE(v.derrotas, 0) AS derrotas,
        COALESCE(v.gols_marcados, 0) AS gols_marcados,
        COALESCE(v.gols_sofridos, 0) AS gols_sofridos,
        COALESCE(v.saldo_gols, 0) AS saldo_gols
    FROM ViewRanking v
    ORDER BY 
        v.pontos DESC, 
        v.saldo_gols DESC, 
        v.vitorias DESC, 
        v.nome ASC;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_encerrar_partida
AFTER UPDATE ON partida
FOR EACH ROW
BEGIN
    IF NEW.resultado_final IS NOT NULL THEN
        -- Pega os gols dos jogadores na partida
        INSERT INTO HistoricoPartida (
            id_partida, 
            id_jogador, 
            gols_feitos, 
            gols_sofridos, 
            resultado
        )
        SELECT 
            p.id_partida,
            p.id_jogador,
            (SELECT COUNT(*) 
             FROM Gol g 
             WHERE g.id_partida = p.id_partida 
               AND g.id_jogador = p.id_jogador) AS gols_feitos,
               
            (SELECT COUNT(*) 
             FROM Gol g 
             WHERE g.id_partida = p.id_partida 
               AND g.id_jogador != p.id_jogador) AS gols_sofridos,
               
            CASE
                WHEN 
                    (SELECT COUNT(*) 
                     FROM Gol g 
                     WHERE g.id_partida = p.id_partida 
                       AND g.id_jogador = p.id_jogador) >
                    (SELECT COUNT(*) 
                     FROM Gol g 
                     WHERE g.id_partida = p.id_partida 
                       AND g.id_jogador != p.id_jogador)
                THEN 'vitoria'
                
                WHEN 
                    (SELECT COUNT(*) 
                     FROM Gol g 
                     WHERE g.id_partida = p.id_partida 
                       AND g.id_jogador = p.id_jogador) =
                    (SELECT COUNT(*) 
                     FROM Gol g 
                     WHERE g.id_partida = p.id_partida 
                       AND g.id_jogador != p.id_jogador)
                THEN 'empate'
                
                ELSE 'derrota'
            END
        FROM Participa p
        WHERE p.id_partida = NEW.id_partida;
    END IF;
END$$

DELIMITER ;

SHOW TRIGGERS;

SELECT * FROM jogador;
SELECT * FROM loginsativos;
SELECT * FROM partida;
SELECT * FROM historicopartida;
SELECT * FROM gol;
