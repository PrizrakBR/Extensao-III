"""
Módulo de banco de dados - SQLite
Prefeitura de Papanduva - SC
Sistema de Controle de Estoque e Agendamento de TI
"""

import sqlite3
import os
import sys
from contextlib import contextmanager
from datetime import datetime


def _pasta_dados():
    """Pasta do banco de dados.
    - Instalado (.exe): %LOCALAPPDATA%\\TI_Papanduva (gravável por qualquer usuário,
      mesmo com o programa em 'Arquivos de Programas').
    - Desenvolvimento (python main.py): pasta do script.
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        pasta = os.path.join(base, "TI_Papanduva")
        os.makedirs(pasta, exist_ok=True)
        return pasta
    return os.path.dirname(os.path.abspath(__file__))


PASTA_DADOS = _pasta_dados()
DB_PATH = os.path.join(PASTA_DADOS, "estoque_ti.db")


TABELAS_OBRIGATORIAS = ("agendamentos", "historico_servicos", "estoque", "movimentacoes")


def validar_backup(caminho):
    """Confere se 'caminho' é um banco SQLite íntegro deste sistema.
    Retorna (agendamentos, historico, pecas, movimentacoes) ou levanta ValueError."""
    if not os.path.isfile(caminho):
        raise ValueError("Arquivo não encontrado.")
    if os.path.abspath(caminho).lower() == os.path.abspath(DB_PATH).lower():
        raise ValueError("Selecione um arquivo de backup, não o banco que o sistema está usando.")
    try:
        uri = "file:" + caminho.replace("\\", "/").replace("?", "%3f").replace("#", "%23") + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.Error:
        raise ValueError("O arquivo não é um banco de dados válido.")
    try:
        try:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("O arquivo de backup está corrompido.")
            tabelas = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        except sqlite3.DatabaseError:
            raise ValueError("O arquivo não é um banco de dados válido.")
        faltando = [t for t in TABELAS_OBRIGATORIAS if t not in tabelas]
        if faltando:
            raise ValueError("Este arquivo não é um backup deste sistema "
                             f"(faltam as tabelas: {', '.join(faltando)}).")
        return tuple(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                     for t in TABELAS_OBRIGATORIAS)
    finally:
        conn.close()


def restaurar_backup(caminho):
    """Substitui TODOS os dados atuais pelos do arquivo de backup.
    Antes, guarda uma cópia do banco atual em <pasta de dados>\\backups_automaticos.
    Retorna (caminho_da_copia_de_seguranca, contagens_restauradas)."""
    contagens = validar_backup(caminho)

    inicializar_banco()  # garante que o banco atual exista para a cópia de segurança
    pasta_seg = os.path.join(PASTA_DADOS, "backups_automaticos")
    os.makedirs(pasta_seg, exist_ok=True)
    copia = os.path.join(
        pasta_seg, f"antes_da_restauracao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db")
    fazer_backup(copia)

    origem = sqlite3.connect("file:" + caminho.replace("\\", "/").replace("?", "%3f").replace("#", "%23")
                             + "?mode=ro", uri=True)
    try:
        destino = sqlite3.connect(DB_PATH)
        try:
            origem.backup(destino)   # troca o conteúdo de forma atômica
        finally:
            destino.close()
    finally:
        origem.close()
    inicializar_banco()
    return copia, contagens


def fazer_backup(destino):
    """Copia o banco inteiro (consistente, mesmo em uso) para o arquivo 'destino'."""
    origem = sqlite3.connect(DB_PATH)
    try:
        copia = sqlite3.connect(destino)
        try:
            origem.backup(copia)
        finally:
            copia.close()
    finally:
        origem.close()


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers de conversão de datas
# ══════════════════════════════════════════════════════════════════════════════

def to_db_date(date_str):
    """Converte DD/MM/AAAA → AAAA-MM-DD (formato interno do banco)."""
    if not date_str:
        return None
    s = str(date_str).strip()
    if '/' in s:
        parts = s.split('/')
        if len(parts) == 3:
            d, m, y = parts
            return f"{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}"
    return s  # já em AAAA-MM-DD ou desconhecido


def to_display_date(date_str):
    """Converte AAAA-MM-DD (ou AAAA-MM-DD HH:MM:SS) → DD/MM/AAAA (ou DD/MM/AAAA HH:MM)."""
    if not date_str:
        return ""
    s = str(date_str).strip()
    # Separa parte de hora se existir
    time_part = ""
    if ' ' in s:
        s, time_part = s.split(' ', 1)
        time_part = " " + time_part[:5]  # ex: " 14:32"
    if '-' in s and len(s) >= 10:
        parts = s[:10].split('-')
        if len(parts) == 3:
            y, m, d = parts
            return f"{d}/{m}/{y}{time_part}"
    return date_str


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def _db_conn(commit=False):
    """Abre conexão SQLite com timeout e garante rollback em erro + close sempre."""
    conn = get_connection()
    try:
        yield conn
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar_banco():
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo          TEXT    NOT NULL,
                descricao       TEXT,
                responsavel     TEXT,
                setor           TEXT,
                data_agendada   TEXT    NOT NULL,
                hora_agendada   TEXT,
                prioridade      TEXT    DEFAULT 'Normal',
                status          TEXT    DEFAULT 'Pendente',
                observacoes     TEXT,
                criado_em       TEXT    DEFAULT (datetime('now','localtime')),
                atualizado_em   TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_servicos (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                agendamento_id      INTEGER,
                titulo              TEXT    NOT NULL,
                descricao           TEXT,
                responsavel         TEXT,
                setor               TEXT,
                data_conclusao      TEXT    NOT NULL,
                solucao             TEXT,
                tempo_gasto_min     INTEGER,
                observacoes         TEXT,
                criado_em           TEXT    DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (agendamento_id) REFERENCES agendamentos(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo          TEXT    UNIQUE,
                nome            TEXT    NOT NULL,
                categoria       TEXT,
                descricao       TEXT,
                fabricante      TEXT,
                modelo          TEXT,
                quantidade      INTEGER DEFAULT 0,
                quantidade_min  INTEGER DEFAULT 1,
                localizacao     TEXT,
                unidade         TEXT    DEFAULT 'un',
                observacoes     TEXT,
                criado_em       TEXT    DEFAULT (datetime('now','localtime')),
                atualizado_em   TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                peca_id         INTEGER NOT NULL,
                tipo            TEXT    NOT NULL,
                quantidade      INTEGER NOT NULL,
                quantidade_anterior INTEGER,
                quantidade_nova INTEGER,
                motivo          TEXT,
                responsavel     TEXT,
                agendamento_id  INTEGER,
                observacoes     TEXT,
                data_mov        TEXT    DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (peca_id)         REFERENCES estoque(id),
                FOREIGN KEY (agendamento_id)  REFERENCES agendamentos(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_estoque (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                peca_id         INTEGER,
                peca_codigo     TEXT,
                peca_nome       TEXT    NOT NULL,
                tipo            TEXT    NOT NULL,
                qtd_anterior    INTEGER,
                qtd_nova        INTEGER,
                motivo          TEXT,
                responsavel     TEXT,
                detalhes        TEXT,
                movimentacao_id INTEGER UNIQUE,
                data_alter      TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)

        # Migra movimentações antigas (ex.: de backups v1.2/v1.3) sem duplicar
        cursor.execute("""
            INSERT OR IGNORE INTO historico_estoque
                (peca_id, peca_codigo, peca_nome, tipo, qtd_anterior, qtd_nova,
                 motivo, responsavel, detalhes, movimentacao_id, data_alter)
            SELECT m.peca_id, e.codigo, e.nome,
                   CASE WHEN m.tipo = 'entrada' THEN 'Entrada' ELSE 'Saída' END,
                   m.quantidade_anterior, m.quantidade_nova,
                   m.motivo, m.responsavel,
                   TRIM(
                       CASE WHEN m.tipo = 'entrada' THEN '+' ELSE '-' END
                       || m.quantidade || ' ' || COALESCE(NULLIF(e.unidade, ''), 'un')
                       || CASE WHEN COALESCE(m.observacoes, '') != ''
                               THEN ' | Obs: ' || m.observacoes ELSE '' END
                   ),
                   m.id, m.data_mov
            FROM movimentacoes m
            JOIN estoque e ON m.peca_id = e.id
            WHERE NOT EXISTS (
                SELECT 1 FROM historico_estoque h WHERE h.movimentacao_id = m.id
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_agendamentos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                agendamento_id  INTEGER,
                titulo          TEXT    NOT NULL,
                tipo            TEXT    NOT NULL,
                status_anterior TEXT,
                status_novo     TEXT,
                motivo          TEXT,
                responsavel     TEXT,
                detalhes        TEXT,
                servico_hist_id INTEGER UNIQUE,
                data_alter      TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)

        # Migra conclusões antigas (de versões anteriores à v1.5) sem duplicar
        cursor.execute("""
            INSERT OR IGNORE INTO historico_agendamentos
                (agendamento_id, titulo, tipo, status_anterior, status_novo,
                 motivo, responsavel, detalhes, servico_hist_id, data_alter)
            SELECT h.agendamento_id, h.titulo, 'Conclusão', 'Pendente', 'Concluído',
                   'Serviço concluído', COALESCE(h.responsavel, ''),
                   TRIM(
                       CASE WHEN COALESCE(h.solucao, '') != ''
                            THEN 'Solução: ' || h.solucao ELSE 'Serviço concluído' END
                       || CASE WHEN h.tempo_gasto_min IS NOT NULL
                               THEN ' | Tempo: ' || h.tempo_gasto_min || ' min' ELSE '' END
                   ),
                   h.id, COALESCE(h.criado_em, h.data_conclusao || ' 00:00:00')
            FROM historico_servicos h
            WHERE NOT EXISTS (
                SELECT 1 FROM historico_agendamentos ha WHERE ha.servico_hist_id = h.id
            )
        """)


# ══════════════════════════════════════════════════════════════════════════════
#  AGENDAMENTOS
# ══════════════════════════════════════════════════════════════════════════════

def _registrar_historico_agendamento(cursor, agendamento_id, titulo, tipo,
                                     status_anterior="", status_novo="",
                                     motivo="", responsavel="", detalhes="",
                                     servico_hist_id=None):
    cursor.execute("""
        INSERT INTO historico_agendamentos
            (agendamento_id, titulo, tipo, status_anterior, status_novo,
             motivo, responsavel, detalhes, servico_hist_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (agendamento_id, titulo, tipo, status_anterior or "", status_novo or "",
          motivo or "", responsavel or "", detalhes or "", servico_hist_id))


def criar_agendamento(titulo, descricao, responsavel, setor,
                      data_agendada, hora_agendada, prioridade, observacoes):
    data_db = to_db_date(data_agendada)
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agendamentos
                (titulo, descricao, responsavel, setor, data_agendada,
                 hora_agendada, prioridade, status, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendente', ?)
        """, (titulo, descricao, responsavel, setor, data_db,
              hora_agendada, prioridade, observacoes))
        new_id = cursor.lastrowid
        partes = [f"Data: {to_display_date(data_db)}"]
        if hora_agendada:
            partes.append(f"Hora: {hora_agendada}")
        if setor:
            partes.append(f"Setor: {setor}")
        if prioridade:
            partes.append(f"Prioridade: {prioridade}")
        if descricao:
            partes.append(f"Descrição: {descricao}")
        if observacoes:
            partes.append(f"Obs.: {observacoes}")
        _registrar_historico_agendamento(
            cursor, new_id, titulo, "Cadastro",
            "", "Pendente", "Agendamento criado", responsavel, " | ".join(partes)
        )
        return new_id


def listar_agendamentos(status=None, data_inicio=None, data_fim=None):
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM agendamentos WHERE 1=1"
        params = []
        if status and status != "Todos":
            query += " AND status = ?"
            params.append(status)
        if data_inicio:
            query += " AND data_agendada >= ?"
            params.append(to_db_date(data_inicio) or data_inicio)
        if data_fim:
            query += " AND data_agendada <= ?"
            params.append(to_db_date(data_fim) or data_fim)
        query += " ORDER BY data_agendada ASC, hora_agendada ASC"
        cursor.execute(query, params)
        return cursor.fetchall()


def listar_agendamentos_atrasados():
    """Agendamentos em aberto (Pendente/Em andamento) cuja data já passou."""
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM agendamentos
            WHERE status IN ('Pendente', 'Em andamento')
              AND data_agendada < date('now','localtime')
            ORDER BY data_agendada ASC, hora_agendada ASC
        """)
        return cursor.fetchall()


def obter_agendamento(id_agendamento):
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agendamentos WHERE id = ?", (id_agendamento,))
        return cursor.fetchone()


def atualizar_agendamento(id_agendamento, titulo, descricao, responsavel, setor,
                          data_agendada, hora_agendada, prioridade, status, observacoes):
    data_db = to_db_date(data_agendada)
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agendamentos WHERE id=?", (id_agendamento,))
        ant = cursor.fetchone()
        cursor.execute("""
            UPDATE agendamentos SET
                titulo=?, descricao=?, responsavel=?, setor=?,
                data_agendada=?, hora_agendada=?, prioridade=?, status=?,
                observacoes=?, atualizado_em=datetime('now','localtime')
            WHERE id=?
        """, (titulo, descricao, responsavel, setor, data_db,
              hora_agendada, prioridade, status, observacoes, id_agendamento))

        if ant:
            campos = [
                ("Título",       ant["titulo"] or "",        titulo or ""),
                ("Descrição",    ant["descricao"] or "",     descricao or ""),
                ("Responsável",  ant["responsavel"] or "",   responsavel or ""),
                ("Setor",        ant["setor"] or "",         setor or ""),
                ("Data",         to_display_date(ant["data_agendada"]), to_display_date(data_db)),
                ("Hora",         ant["hora_agendada"] or "", hora_agendada or ""),
                ("Prioridade",   ant["prioridade"] or "",    prioridade or ""),
                ("Status",       ant["status"] or "",        status or ""),
                ("Observações",  ant["observacoes"] or "",   observacoes or ""),
            ]
            mudancas = [
                f"{rot}: '{v_ant or '—'}' → '{v_nov or '—'}'"
                for rot, v_ant, v_nov in campos if v_ant != v_nov
            ]
            if mudancas:
                status_ant = ant["status"] or ""
                if status_ant == "Concluído" and status != "Concluído":
                    cursor.execute("DELETE FROM historico_servicos WHERE agendamento_id=?", (id_agendamento,))
                    _registrar_historico_agendamento(
                        cursor, id_agendamento, titulo, "Conclusão Desmarcada",
                        status_ant, status, "Alteração de status na edição",
                        responsavel, "; ".join(mudancas)
                    )
                elif status_ant != "Concluído" and status == "Concluído":
                    cursor.execute("""
                        INSERT INTO historico_servicos
                            (agendamento_id, titulo, descricao, responsavel, setor,
                             data_conclusao, solucao, tempo_gasto_min, observacoes)
                        VALUES (?, ?, ?, ?, ?, date('now','localtime'), ?, NULL, ?)
                    """, (id_agendamento, titulo, descricao, responsavel,
                          setor, "Marcado como concluído via edição", observacoes))
                    sh_id = cursor.lastrowid
                    _registrar_historico_agendamento(
                        cursor, id_agendamento, titulo, "Edição",
                        status_ant, status, "Alteração cadastral (concluído na edição)",
                        responsavel, "; ".join(mudancas), servico_hist_id=sh_id
                    )
                else:
                    _registrar_historico_agendamento(
                        cursor, id_agendamento, titulo, "Edição",
                        status_ant, status, "Alteração cadastral",
                        responsavel, "; ".join(mudancas)
                    )


def concluir_agendamento(id_agendamento, solucao, tempo_gasto_min, observacoes):
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agendamentos WHERE id=?", (id_agendamento,))
        ag = cursor.fetchone()
        if ag:
            status_ant = ag["status"] or "Pendente"
            cursor.execute("""
                UPDATE agendamentos SET status='Concluído',
                    atualizado_em=datetime('now','localtime')
                WHERE id=?
            """, (id_agendamento,))
            cursor.execute("""
                INSERT INTO historico_servicos
                    (agendamento_id, titulo, descricao, responsavel, setor,
                     data_conclusao, solucao, tempo_gasto_min, observacoes)
                VALUES (?, ?, ?, ?, ?, date('now','localtime'), ?, ?, ?)
            """, (id_agendamento, ag["titulo"], ag["descricao"], ag["responsavel"],
                  ag["setor"], solucao, tempo_gasto_min, observacoes))
            sh_id = cursor.lastrowid
            partes = []
            if solucao:
                partes.append(f"Solução: {solucao}")
            if tempo_gasto_min is not None:
                partes.append(f"Tempo: {tempo_gasto_min} min")
            if observacoes:
                partes.append(f"Obs.: {observacoes}")
            _registrar_historico_agendamento(
                cursor, id_agendamento, ag["titulo"], "Conclusão",
                status_ant, "Concluído", "Serviço concluído",
                ag["responsavel"] or "",
                " | ".join(partes) if partes else "Serviço marcado como concluído",
                servico_hist_id=sh_id
            )


def desmarcar_conclusao_servico(historico_id, novo_status="Pendente", motivo="", responsavel=""):
    """Desmarca a conclusão de um serviço no histórico, retornando-o aos agendamentos
    e registrando a alteração em historico_agendamentos."""
    if novo_status not in ("Pendente", "Em andamento"):
        novo_status = "Pendente"
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historico_servicos WHERE id=?", (historico_id,))
        h = cursor.fetchone()
        if not h:
            raise ValueError("Registro de serviço concluído não encontrado.")

        ag_id = h["agendamento_id"]
        if ag_id:
            cursor.execute("SELECT id FROM agendamentos WHERE id=?", (ag_id,))
            existe = cursor.fetchone()
        else:
            existe = None

        if existe:
            cursor.execute("""
                UPDATE agendamentos
                SET status=?, atualizado_em=datetime('now','localtime')
                WHERE id=?
            """, (novo_status, ag_id))
        else:
            cursor.execute("""
                INSERT INTO agendamentos
                    (titulo, descricao, responsavel, setor, data_agendada,
                     hora_agendada, prioridade, status, observacoes)
                VALUES (?, ?, ?, ?, ?, '', 'Normal', ?, ?)
            """, (h["titulo"], h["descricao"], h["responsavel"], h["setor"],
                  h["data_conclusao"], novo_status, h["observacoes"]))
            ag_id = cursor.lastrowid

        cursor.execute("DELETE FROM historico_servicos WHERE id=?", (historico_id,))

        partes = [f"Status: 'Concluído' → '{novo_status}'"]
        if motivo:
            partes.append(f"Motivo: {motivo}")
        if h["solucao"]:
            partes.append(f"Solução anterior: {h['solucao']}")
        _registrar_historico_agendamento(
            cursor, ag_id, h["titulo"], "Conclusão Desmarcada",
            "Concluído", novo_status,
            motivo or "Conclusão desmarcada (marcado por engano)",
            responsavel or h["responsavel"] or "",
            " | ".join(partes)
        )
        return ag_id


def excluir_agendamento(id_agendamento):
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agendamentos WHERE id=?", (id_agendamento,))
        ag = cursor.fetchone()
        if ag:
            detalhe = f"Agendamento excluído (Data: {to_display_date(ag['data_agendada'])}"
            if ag["setor"]:
                detalhe += f" | Setor: {ag['setor']}"
            detalhe += f" | Status: {ag['status'] or 'Pendente'})"
            _registrar_historico_agendamento(
                cursor, id_agendamento, ag["titulo"], "Exclusão",
                ag["status"] or "", "", "Agendamento excluído",
                ag["responsavel"] or "", detalhe
            )
        # Solta eventuais FKs antes de excluir para não violar integridade referencial
        conn.execute("UPDATE historico_servicos SET agendamento_id=NULL WHERE agendamento_id=?", (id_agendamento,))
        conn.execute("UPDATE movimentacoes SET agendamento_id=NULL WHERE agendamento_id=?", (id_agendamento,))
        conn.execute("DELETE FROM agendamentos WHERE id=?", (id_agendamento,))


def contar_agendamentos_por_status():
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) as total FROM agendamentos GROUP BY status")
        rows = cursor.fetchall()
        return {r["status"]: r["total"] for r in rows}


# ══════════════════════════════════════════════════════════════════════════════
#  HISTÓRICO DE SERVIÇOS
# ══════════════════════════════════════════════════════════════════════════════

def listar_historico_servicos(data_inicio=None, data_fim=None, busca=None):
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM historico_servicos WHERE 1=1"
        params = []
        if data_inicio:
            params.append(to_db_date(data_inicio) or data_inicio)
            query += " AND data_conclusao >= ?"
        if data_fim:
            params.append(to_db_date(data_fim) or data_fim)
            query += " AND data_conclusao <= ?"
        if busca:
            query += " AND (titulo LIKE ? OR responsavel LIKE ? OR setor LIKE ?)"
            b = f"%{busca}%"
            params.extend([b, b, b])
        query += " ORDER BY data_conclusao DESC, criado_em DESC"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_historico_servico(id_historico):
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historico_servicos WHERE id=?", (id_historico,))
        return cursor.fetchone()


def listar_historico_agendamentos(tipo=None, data_inicio=None, data_fim=None, busca=None):
    """Lista todas as alterações de agendamentos/serviços (Cadastro, Edição, Conclusão, Desmarcada, Exclusão)."""
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM historico_agendamentos WHERE 1=1"
        params = []
        if tipo and tipo != "Todos":
            query += " AND tipo = ?"
            params.append(tipo)
        if data_inicio:
            query += " AND date(data_alter) >= ?"
            params.append(to_db_date(data_inicio) or data_inicio)
        if data_fim:
            query += " AND date(data_alter) <= ?"
            params.append(to_db_date(data_fim) or data_fim)
        if busca:
            query += (" AND (titulo LIKE ? OR motivo LIKE ? "
                      "OR responsavel LIKE ? OR detalhes LIKE ?)")
            b = f"%{busca}%"
            params.extend([b, b, b, b])
        query += " ORDER BY data_alter DESC, id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_alteracao_agendamento(id_alteracao):
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historico_agendamentos WHERE id=?", (id_alteracao,))
        return cursor.fetchone()


# ══════════════════════════════════════════════════════════════════════════════
#  ESTOQUE
# ══════════════════════════════════════════════════════════════════════════════

def _registrar_historico_estoque(cursor, peca_id, peca_codigo, peca_nome, tipo,
                                 qtd_anterior, qtd_nova, motivo="",
                                 responsavel="", detalhes="", movimentacao_id=None):
    cursor.execute("""
        INSERT INTO historico_estoque
            (peca_id, peca_codigo, peca_nome, tipo, qtd_anterior, qtd_nova,
             motivo, responsavel, detalhes, movimentacao_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (peca_id, peca_codigo or None, peca_nome, tipo, qtd_anterior, qtd_nova,
          motivo or "", responsavel or "", detalhes or "", movimentacao_id))


def criar_peca(codigo, nome, categoria, descricao, fabricante, modelo,
               quantidade, quantidade_min, localizacao, unidade, observacoes,
               responsavel=""):
    unidade_limpa = unidade or "un"
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO estoque
                (codigo, nome, categoria, descricao, fabricante, modelo,
                 quantidade, quantidade_min, localizacao, unidade, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo or None, nome, categoria, descricao, fabricante, modelo,
              quantidade, quantidade_min, localizacao, unidade_limpa, observacoes))
        new_id = cursor.lastrowid
        partes = [f"Qtd. inicial: {quantidade} {unidade_limpa}", f"Mínimo: {quantidade_min}"]
        if categoria:
            partes.append(f"Categoria: {categoria}")
        if fabricante:
            partes.append(f"Fabricante: {fabricante}")
        if modelo:
            partes.append(f"Modelo: {modelo}")
        if localizacao:
            partes.append(f"Localização: {localizacao}")
        if observacoes:
            partes.append(f"Obs.: {observacoes}")
        _registrar_historico_estoque(
            cursor, new_id, codigo, nome, "Cadastro",
            0, quantidade, "Cadastro de peça", responsavel, " | ".join(partes)
        )
        return new_id


def listar_estoque(busca=None, categoria=None, apenas_abaixo_minimo=False):
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM estoque WHERE 1=1"
        params = []
        if busca:
            query += " AND (nome LIKE ? OR codigo LIKE ? OR fabricante LIKE ? OR modelo LIKE ?)"
            b = f"%{busca}%"
            params.extend([b, b, b, b])
        if categoria and categoria != "Todas":
            query += " AND categoria = ?"
            params.append(categoria)
        if apenas_abaixo_minimo:
            query += " AND quantidade <= quantidade_min"
        query += " ORDER BY nome ASC"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_peca(id_peca):
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM estoque WHERE id=?", (id_peca,))
        return cursor.fetchone()


def atualizar_peca(id_peca, codigo, nome, categoria, descricao, fabricante,
                   modelo, quantidade_min, localizacao, unidade, observacoes,
                   responsavel=""):
    unidade_limpa = unidade or "un"
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM estoque WHERE id=?", (id_peca,))
        ant = cursor.fetchone()
        cursor.execute("""
            UPDATE estoque SET
                codigo=?, nome=?, categoria=?, descricao=?, fabricante=?,
                modelo=?, quantidade_min=?, localizacao=?, unidade=?,
                observacoes=?, atualizado_em=datetime('now','localtime')
            WHERE id=?
        """, (codigo or None, nome, categoria, descricao, fabricante, modelo,
              quantidade_min, localizacao, unidade_limpa, observacoes, id_peca))

        if ant:
            campos = [
                ("Código",       ant["codigo"] or "",      codigo or ""),
                ("Nome",         ant["nome"] or "",        nome or ""),
                ("Categoria",    ant["categoria"] or "",   categoria or ""),
                ("Fabricante",   ant["fabricante"] or "",  fabricante or ""),
                ("Modelo",       ant["modelo"] or "",      modelo or ""),
                ("Qtd. mínima",  str(ant["quantidade_min"]), str(quantidade_min)),
                ("Localização",  ant["localizacao"] or "", localizacao or ""),
                ("Unidade",      ant["unidade"] or "un",   unidade_limpa),
                ("Observações",  ant["observacoes"] or "", observacoes or ""),
            ]
            mudancas = [
                f"{rot}: '{v_ant or '—'}' → '{v_nov or '—'}'"
                for rot, v_ant, v_nov in campos if v_ant != v_nov
            ]
            if mudancas:
                qtd_atual = ant["quantidade"]
                _registrar_historico_estoque(
                    cursor, id_peca, codigo, nome, "Edição",
                    qtd_atual, qtd_atual, "Alteração cadastral",
                    responsavel, "; ".join(mudancas)
                )


def movimentar_estoque(peca_id, tipo, quantidade, motivo, responsavel,
                       agendamento_id=None, observacoes=None):
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, codigo, unidade, quantidade FROM estoque WHERE id=?", (peca_id,))
        peca = cursor.fetchone()
        if not peca:
            raise ValueError("Peça não encontrada.")
        qtd_anterior = peca["quantidade"]
        if tipo == "entrada":
            qtd_nova = qtd_anterior + quantidade
        else:
            qtd_nova = qtd_anterior - quantidade
            if qtd_nova < 0:
                raise ValueError(f"Estoque insuficiente. Disponível: {qtd_anterior}.")
        cursor.execute("""
            UPDATE estoque SET quantidade=?, atualizado_em=datetime('now','localtime')
            WHERE id=?
        """, (qtd_nova, peca_id))
        cursor.execute("""
            INSERT INTO movimentacoes
                (peca_id, tipo, quantidade, quantidade_anterior, quantidade_nova,
                 motivo, responsavel, agendamento_id, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (peca_id, tipo, quantidade, qtd_anterior, qtd_nova,
              motivo, responsavel, agendamento_id, observacoes))
        mov_id = cursor.lastrowid

        unidade = peca["unidade"] or "un"
        sinal = "+" if tipo == "entrada" else "-"
        detalhe = f"{sinal}{quantidade} {unidade}"
        if observacoes:
            detalhe += f" | Obs.: {observacoes}"
        _registrar_historico_estoque(
            cursor, peca_id, peca["codigo"], peca["nome"],
            "Entrada" if tipo == "entrada" else "Saída",
            qtd_anterior, qtd_nova, motivo, responsavel, detalhe,
            movimentacao_id=mov_id
        )
        return qtd_nova


def excluir_peca(id_peca, responsavel=""):
    with _db_conn(commit=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM estoque WHERE id=?", (id_peca,))
        peca = cursor.fetchone()
        if peca:
            unidade = peca["unidade"] or "un"
            detalhe = (f"Peça removida do estoque "
                       f"(saldo no momento: {peca['quantidade']} {unidade})")
            _registrar_historico_estoque(
                cursor, id_peca, peca["codigo"], peca["nome"], "Exclusão",
                peca["quantidade"], 0, "Exclusão de peça", responsavel, detalhe
            )
        conn.execute("DELETE FROM movimentacoes WHERE peca_id=?", (id_peca,))
        conn.execute("DELETE FROM estoque WHERE id=?", (id_peca,))


def listar_categorias():
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT categoria FROM estoque "
            "WHERE categoria IS NOT NULL AND TRIM(categoria) != '' "
            "ORDER BY categoria"
        )
        rows = cursor.fetchall()
        return [r["categoria"] for r in rows]


def listar_movimentacoes(peca_id=None, tipo=None, data_inicio=None, data_fim=None):
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = """
            SELECT m.*, e.nome as peca_nome, e.codigo as peca_codigo
            FROM movimentacoes m
            JOIN estoque e ON m.peca_id = e.id
            WHERE 1=1
        """
        params = []
        if peca_id:
            query += " AND m.peca_id = ?"
            params.append(peca_id)
        if tipo and tipo != "Todos":
            query += " AND m.tipo = ?"
            params.append(tipo)
        if data_inicio:
            query += " AND date(m.data_mov) >= ?"
            params.append(to_db_date(data_inicio) or data_inicio)
        if data_fim:
            query += " AND date(m.data_mov) <= ?"
            params.append(to_db_date(data_fim) or data_fim)
        query += " ORDER BY m.data_mov DESC"
        cursor.execute(query, params)
        return cursor.fetchall()


def listar_historico_estoque(tipo=None, data_inicio=None, data_fim=None, busca=None):
    """Lista todas as alterações de estoque (Cadastro, Edição, Entrada, Saída, Exclusão)."""
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM historico_estoque WHERE 1=1"
        params = []
        if tipo and tipo != "Todos":
            query += " AND tipo = ?"
            params.append(tipo)
        if data_inicio:
            query += " AND date(data_alter) >= ?"
            params.append(to_db_date(data_inicio) or data_inicio)
        if data_fim:
            query += " AND date(data_alter) <= ?"
            params.append(to_db_date(data_fim) or data_fim)
        if busca:
            query += (" AND (peca_nome LIKE ? OR peca_codigo LIKE ? "
                      "OR motivo LIKE ? OR responsavel LIKE ? OR detalhes LIKE ?)")
            b = f"%{busca}%"
            params.extend([b, b, b, b, b])
        query += " ORDER BY data_alter DESC, id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_alteracao_estoque(id_alteracao):
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historico_estoque WHERE id=?", (id_alteracao,))
        return cursor.fetchone()


def contar_itens_abaixo_minimo():
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM estoque WHERE quantidade <= quantidade_min")
        row = cursor.fetchone()
        return row["total"] if row else 0


def contar_total_pecas():
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM estoque")
        row = cursor.fetchone()
        return row["total"] if row else 0
