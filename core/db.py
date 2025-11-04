# core/db.py
import sqlite3
import os
import time
import pandas as pd
from typing import Iterable, Tuple, Optional, Dict, List
from .paths import DB_PATH, ensure_data_dirs

SCHEMA_SQL = """
-- Tabela de termos de sanitização
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    term TEXT NOT NULL,
    norm_term TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(category, norm_term)
);
CREATE INDEX IF NOT EXISTS idx_terms_category ON terms(category);
CREATE INDEX IF NOT EXISTS idx_terms_enabled ON terms(enabled);

-- Tabela de notas importadas
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_name TEXT NOT NULL,
    note_year INTEGER,
    source_path TEXT,          -- caminho/identificador de origem
    source_hash TEXT,          -- hash para deduplicar
    original_text TEXT NOT NULL,
    sanitized_text TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(source_hash)
);
CREATE INDEX IF NOT EXISTS idx_notes_year ON notes(note_year);
CREATE INDEX IF NOT EXISTS idx_notes_name ON notes(note_name);
"""

def _normalize(s: str) -> str:
    import unicodedata, re
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.replace('-', ' ').replace('_', ' ')
    s = ' '.join(s.split())
    s = re.sub(r'\s+', ' ', s)
    return s

def get_conn():
    ensure_data_dirs()
    init_db_if_needed()
    return sqlite3.connect(DB_PATH)

def init_db_if_needed():
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()

# ====== TERMS (já existentes) ======
def import_terms_from_dataframe(df: pd.DataFrame) -> Tuple[int, int]:
    now = int(time.time())
    added = 0
    touched = 0

    lower_cols = {c.lower(): c for c in df.columns}
    long_format = 'categoria' in lower_cols and 'termo' in lower_cols

    records = []
    if long_format:
        cat_col = lower_cols['categoria']
        term_col = lower_cols['termo']
        tmp = df[[cat_col, term_col]].dropna()
        for _, row in tmp.iterrows():
            category = str(row[cat_col]).strip()
            term = str(row[term_col]).strip()
            if category and term:
                records.append((category, term))
    else:
        for col in df.columns:
            category = str(col).strip()
            for v in df[col].dropna().astype(str).tolist():
                term = v.strip()
                if term:
                    records.append((category, term))

    if not records:
        return (0, 0)

    conn = get_conn()
    try:
        with conn:
            for category, term in records:
                norm = _normalize(term)
                if not norm:
                    continue
                cur = conn.execute(
                    """
                    INSERT INTO terms (category, term, norm_term, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, ?)
                    ON CONFLICT(category, norm_term) DO UPDATE SET
                      term=excluded.term,
                      updated_at=excluded.updated_at
                    """,
                    (category, term, norm, now, now)
                )
                if cur.rowcount == 1:
                    added += 1
                else:
                    touched += 1
    finally:
        conn.close()

    return (added, touched)

def get_terms_df(only_enabled: bool = False) -> pd.DataFrame:
    conn = get_conn()
    try:
        q = "SELECT id, category, term, norm_term, enabled, created_at, updated_at FROM terms"
        if only_enabled:
            q += " WHERE enabled = 1"
        q += " ORDER BY category, term"
        return pd.read_sql_query(q, conn)
    finally:
        conn.close()

def update_terms_from_editor(edited_df: pd.DataFrame) -> int:
    now = int(time.time())
    count = 0
    if not {'id','category','term','enabled'}.issubset(set(edited_df.columns)):
        return 0

    conn = get_conn()
    try:
        with conn:
            for _, row in edited_df.iterrows():
                rid = int(row['id'])
                category = str(row['category']).strip()
                term = str(row['term']).strip()
                enabled = 1 if int(row['enabled']) == 1 else 0
                norm = _normalize(term)
                cur = conn.execute(
                    """
                    UPDATE terms
                       SET category=?,
                           term=?,
                           norm_term=?,
                           enabled=?,
                           updated_at=?
                     WHERE id=?
                    """,
                    (category, term, norm, enabled, now, rid)
                )
                count += cur.rowcount
    finally:
        conn.close()
    return count

def delete_terms(ids: Iterable[int]) -> int:
    ids = [int(i) for i in ids]
    if not ids:
        return 0
    conn = get_conn()
    try:
        with conn:
            cur = conn.execute(
                f"DELETE FROM terms WHERE id IN ({','.join('?'*len(ids))})",
                ids
            )
            return cur.rowcount
    finally:
        conn.close()

def fetch_terms_for_sanitization(categories: Optional[Iterable[str]] = None) -> Dict[str, List[str]]:
    conn = get_conn()
    try:
        if categories:
            placeholders = ','.join('?'*len(list(categories)))
            q = f"""
                SELECT category, term FROM terms
                 WHERE enabled=1 AND category IN ({placeholders})
                 ORDER BY category, term
            """
            rows = conn.execute(q, list(categories)).fetchall()
        else:
            q = "SELECT category, term FROM terms WHERE enabled=1 ORDER BY category, term"
            rows = conn.execute(q).fetchall()
        out: Dict[str, List[str]] = {}
        for category, term in rows:
            out.setdefault(category, []).append(term)
        return out
    finally:
        conn.close()

# ====== NOTES (novo) ======
def upsert_note(note_name: str,
                note_year: Optional[int],
                source_path: Optional[str],
                source_hash: str,
                original_text: str,
                sanitized_text: str) -> int:
    """
    Insere (ou ignora se já existir por source_hash) a nota.
    Retorna o id da nota (rowid).
    """
    now = int(time.time())
    conn = get_conn()
    try:
        with conn:
            # Tenta inserir; se já existir, atualiza campos variáveis
            conn.execute("""
                INSERT INTO notes (note_name, note_year, source_path, source_hash, original_text, sanitized_text, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_hash) DO UPDATE SET
                  note_name=excluded.note_name,
                  note_year=excluded.note_year,
                  source_path=excluded.source_path,
                  original_text=excluded.original_text,
                  sanitized_text=excluded.sanitized_text,
                  updated_at=excluded.updated_at
            """, (note_name, note_year, source_path, source_hash, original_text, sanitized_text, now, now))

            # Buscar id
            cur = conn.execute("SELECT id FROM notes WHERE source_hash=?", (source_hash,))
            rid = cur.fetchone()[0]
            return rid
    finally:
        conn.close()
