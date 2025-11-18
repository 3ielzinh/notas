# pages/1_🔎_Pesquisa.py
import os
import re
import sqlite3
import csv
import unicodedata
import base64
from pathlib import Path
from typing import List, Dict, Any, Tuple

import streamlit as st
from core.ui import hero, section
from core.sidebar import render_sidebar

# ---------------------------------
# Configuração base
# ---------------------------------
st.set_page_config(page_title="Pesquisa de Notas", page_icon="🔎", layout="wide")

# Sidebar padrão do projeto
with st.sidebar:
    render_sidebar()

# ---------------------------------
# Caminhos e utilitários de estilo (Atualizado)
# ---------------------------------
ROOT = Path(__file__).resolve().parents[1]
STYLES_PATH = ROOT / "styles" / "style.css"
ASSETS_PATH = ROOT / "assets"

def file_to_b64(path: Path) -> str:
    """Converte um arquivo para string base64."""
    try:
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception:
        pass
    return ""

def load_css(path: Path = STYLES_PATH):
    """Carrega o CSS global do projeto (styles/style.css)."""
    try:
        if path.exists():
            css = path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Falha ao carregar CSS: {e}")

def get_logo_b64() -> tuple[str, str]:
    """Tenta logo.svg; se não houver, usa inss_logo.png. Retorna (b64, mime)."""
    svg_b64 = file_to_b64(ASSETS_PATH / "logo.svg")
    if svg_b64:
        return svg_b64, "image/svg+xml"
    png_b64 = file_to_b64(ASSETS_PATH / "logo.png")
    if png_b64:
        return png_b64, "image/png"
    return "", ""

def inject_custom_header(
    title_text: str = "REPOSITÓRIO DE NOTAS TÉCNICAS - DILAG",
    subtitle_text: str = "Diretoria de Gestão de Pessoas - DGP"
):
    """
    Injeta logo, título e subtítulo no header usando CSS, e também os estilos
    específicos da página de pesquisa (badges, cards, etc.).
    """
    logo_b64, logo_mime = get_logo_b64()

    header_css = f"""
    <style>
        /* --- Injeção do Header --- */
        [data-testid="stHeader"] {{
            /* 1. Injeta a logo como background */
            background-image: url("data:{logo_mime};base64,{logo_b64}");
            background-repeat: no-repeat;
            background-size: 130px; /* Tamanho da logo */
            background-position: calc(var(--toggle-safe) + 8px) center; /* Posição à esquerda */
        }}

        /* 2. Usa ::before para o TÍTULO */
        [data-testid="stHeader"]::before {{
            content: "{title_text}";
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            /* Empurra o título um pouco para cima para dar espaço ao subtítulo */
            transform: translateY(-80%);
            text-align: center;
            font-weight: 800;
            font-size: 22px;
            color: var(--header-fg);
        }}

        /* 3. Usa ::after para o SUBTÍTULO */
        [data-testid="stHeader"]::after {{
            content: "{subtitle_text}";
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            text-align: center;
            font-weight: 400; /* Mais leve */
            font-size: 20px;
            color: rgba(255, 255, 255, 0.85); /* Cor discreta */
        }}

        /* --- Estilos Específicos da Página de Pesquisa --- */
        .badge.parcial {{
            display:inline-block;
            padding:2px 10px;
            border-radius:999px;
            font-weight:700;
            font-size:12px;
            background:#FEF3C7;
            color:#92400E;
            border:1px solid #F59E0B22;
        }}
        .note-card.parcial {{
            border-left:6px solid #F59E0B; /* âmbar */
        }}
        .note-justif {{
            margin-top:8px;
            padding:8px 10px;
            border-radius:10px;
            background:#FFFBEB;
            border:1px solid #FDE68A;
            font-size:13px;
            color:#78350F;
        }}
    </style>
    """
    st.markdown(header_css, unsafe_allow_html=True)

# Carrega o CSS global e injeta o header customizado
load_css()
inject_custom_header()

# O restante do seu arquivo continua inalterado a partir daqui...
DB_PATH = Path("data/processed/notas.db")
PAGE_SIZE = 20

# ============================
# Config de anonimização/remoção
# ============================
BLOCKLIST_CSV = Path("data/terms/termos_excluir.csv")
BLOCK_TOKEN = "[REMOVIDO]"
REMOVE_ON_DISPLAY = True
# ============================

# ---------------- Helpers ----------------
def has_fts5(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)")
        conn.execute("DROP TABLE _fts5_probe")
        return True
    except sqlite3.OperationalError:
        return False

def tokenize_query(q: str) -> List[str]:
    return re.findall(r"\w{2,}", q.lower(), flags=re.UNICODE)[:8]

def build_fts_query_AND_prefix(user_query: str) -> str:
    terms = tokenize_query(user_query)
    if not terms:
        return ""
    safe = [t.replace('"', "") + "*" for t in terms]
    return " AND ".join(safe)

def highlight(text: str, terms: List[str]) -> str:
    if not text or not terms:
        return text or ""
    def repl(m): return f"<mark>{m.group(0)}</mark>"
    out = text
    for t in sorted(set(terms), key=len, reverse=True):
        try:
            out = re.sub(rf"(?i)\b{re.escape(t)}\b", repl, out)
        except re.error:
            pass
    return out

def _cleanup_orfaos(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("DELETE FROM fts_notas WHERE sha NOT IN (SELECT sha FROM notas)")
    n = cur.rowcount if cur.rowcount is not None else 0
    conn.commit()
    return n

def _fts_exists(conn: sqlite3.Connection) -> bool:
    return has_fts5(conn) and conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fts_notas'"
    ).fetchone() is not None

def search_db(user_query: str, limit: int, offset: int, year_filter: Any = None):
    """
    Busca no banco. Se user_query == "__ALL__" -> retorna todas as notas (com opcional filtro de ano).
    Caso contrário, usa FTS/LICE/LIKE conforme disponível. year_filter pode ser None ou um valor (ex.: 2024).
    Retorna: (rows, total, mecanismo)
    """
    if not DB_PATH.exists():
        st.error("Banco de dados não encontrado. Rode o script de indexação (build_db_from_txts.py).")
        return [], 0, "N/A"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    mecanismo = "N/A"
    rows = []
    total = 0

    # Normaliza filtro de ano
    year_val = None
    if year_filter not in (None, "", "Todas", "Todos"):
        try:
            year_val = int(year_filter)
        except Exception:
            year_val = str(year_filter)

    # Caso especial: pedir todas as notas
    if user_query == "__ALL__":
        mecanismo = "ALL"
        if year_val is None:
            sql_rows = """
            SELECT sha, ano, arquivo, snippet, caminho_txt,
                   em_vigor, situacao, justificativa_situacao,
                   0.0 AS score
            FROM notas
            ORDER BY imported_at DESC
            LIMIT ? OFFSET ?
            """
            rows = cur.execute(sql_rows, (limit, offset)).fetchall()
            total = cur.execute("SELECT COUNT(*) FROM notas").fetchone()[0]
        else:
            sql_rows = """
            SELECT sha, ano, arquivo, snippet, caminho_txt,
                   em_vigor, situacao, justificativa_situacao,
                   0.0 AS score
            FROM notas
            WHERE ano = ?
            ORDER BY imported_at DESC
            LIMIT ? OFFSET ?
            """
            rows = cur.execute(sql_rows, (year_val, limit, offset)).fetchall()
            total = cur.execute("SELECT COUNT(*) FROM notas WHERE ano = ?", (year_val,)).fetchone()[0]

        rows = [dict(r) for r in rows] if rows else []
        conn.close()
        return rows, int(total), mecanismo

    # Caso normal: busca por query (FTS / LIKE)
    q_fts = build_fts_query_AND_prefix(user_query)

    fts_ok = False
    try:
        fts_ok = _fts_exists(conn)
    except Exception:
        fts_ok = False

    # --- FTS5 branch ---
    if q_fts and fts_ok:
        mecanismo = "FTS5"
        where_year = "AND n.ano = ? " if year_val is not None else ""
        params_rows = (q_fts, year_val, limit, offset) if year_val is not None else (q_fts, limit, offset)
        sql_rows = f"""
        SELECT n.sha, n.ano, n.arquivo, n.snippet, n.caminho_txt,
               n.em_vigor, n.situacao, n.justificativa_situacao,
               bm25(fts_notas) AS score
        FROM fts_notas
        JOIN notas n ON n.sha = fts_notas.sha
        WHERE fts_notas MATCH ?
        {where_year}
        ORDER BY score ASC
        LIMIT ? OFFSET ?
        """
        try:
            rows = cur.execute(sql_rows, params_rows).fetchall()
        except Exception:
            rows = []

        sql_count = f"""
        SELECT COUNT(*) FROM (
            SELECT 1
            FROM fts_notas
            JOIN notas n ON n.sha = fts_notas.sha
            WHERE fts_notas MATCH ?
            {where_year}
        )
        """
        try:
            total = cur.execute(sql_count, (q_fts, year_val) if year_val is not None else (q_fts,)).fetchone()[0]
        except Exception:
            total = 0

        if total > 0 and not rows:
            removed = _cleanup_orfaos(conn)
            try:
                rows = cur.execute(sql_rows, params_rows).fetchall()
                total = cur.execute(sql_count, (q_fts, year_val) if year_val is not None else (q_fts,)).fetchone()[0]
            except Exception:
                pass
            if removed:
                st.info(f"Índice ajustado automaticamente ({removed} órfão(s) removido(s)).")

        if total == 0:
            mecanismo = "FTS5+LIKE"
            terms = tokenize_query(user_query)
            if terms:
                like_ands = " AND ".join(["snippet LIKE ?"] * len(terms))
                params = [f"%{t}%" for t in terms]
                if year_val is not None:
                    params = [year_val] + params
                    sql_rows2 = f"""
                    SELECT sha, ano, arquivo, snippet, caminho_txt,
                           em_vigor, situacao, justificativa_situacao,
                           0.0 AS score
                    FROM notas
                    WHERE ano = ? AND {like_ands}
                    ORDER BY imported_at DESC
                    LIMIT ? OFFSET ?
                    """
                    rows = cur.execute(sql_rows2, (*params, limit, offset)).fetchall()
                    sql_count2 = f"SELECT COUNT(*) FROM notas WHERE ano = ? AND {like_ands}"
                    total = cur.execute(sql_count2, (*params,)).fetchone()[0]
                else:
                    sql_rows2 = f"""
                    SELECT sha, ano, arquivo, snippet, caminho_txt,
                           em_vigor, situacao, justificativa_situacao,
                           0.0 AS score
                    FROM notas
                    WHERE {like_ands}
                    ORDER BY imported_at DESC
                    LIMIT ? OFFSET ?
                    """
                    rows = cur.execute(sql_rows2, (*params, limit, offset)).fetchall()
                    sql_count2 = f"SELECT COUNT(*) FROM notas WHERE {like_ands}"
                    total = cur.execute(sql_count2, (*params,)).fetchone()[0]

    # --- LIKE branch (no FTS) ---
    if total == 0 and (not q_fts or not fts_ok):
        mecanismo = "LIKE"
        terms = tokenize_query(user_query)
        if terms:
            like_ands = " AND ".join(["snippet LIKE ?"] * len(terms))
            params = [f"%{t}%" for t in terms]
            if year_val is not None:
                params = [year_val] + params
                sql_rows = f"""
                SELECT sha, ano, arquivo, snippet, caminho_txt,
                       em_vigor, situacao, justificativa_situacao,
                       0.0 AS score
                FROM notas
                WHERE ano = ? AND {like_ands}
                ORDER BY imported_at DESC
                LIMIT ? OFFSET ?
                """
                rows = cur.execute(sql_rows, (*params, limit, offset)).fetchall()
                sql_count = f"SELECT COUNT(*) FROM notas WHERE ano = ? AND {like_ands}"
                total = cur.execute(sql_count, (*params,)).fetchone()[0]
            else:
                sql_rows = f"""
                SELECT sha, ano, arquivo, snippet, caminho_txt,
                       em_vigor, situacao, justificativa_situacao,
                       0.0 AS score
                FROM notas
                WHERE {like_ands}
                ORDER BY imported_at DESC
                LIMIT ? OFFSET ?
                """
                rows = cur.execute(sql_rows, (*params, limit, offset)).fetchall()
                sql_count = f"SELECT COUNT(*) FROM notas WHERE {like_ands}"
                total = cur.execute(sql_count, (*params,)).fetchone()[0]
        else:
            rows, total = [], 0

    # Converte para dict (sem consulta extra)
    rows = [dict(r) for r in rows] if rows else []

    conn.close()
    return rows, int(total), mecanismo

def read_txt(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text(encoding="latin-1", errors="ignore")
    except Exception as e:
        return f"[Falha ao abrir TXT: {e}]"

# ---------------- Normalização e anonimização ----------------
_PUNCT_TRANS = str.maketrans({c: " " for c in "-_./\\,:;!?'\"()[]{}<>|@#*$%^&+=`~"})

def strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")

def normalize_for_match(s: str) -> str:
    s2 = strip_accents(s).lower().translate(_PUNCT_TRANS)
    return re.sub(r"\s+", " ", s2).strip()

def load_blocklist() -> List[str]:
    terms: List[str] = []
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='termos_excluir'")
            if cur.fetchone():
                cur.execute("SELECT termo FROM termos_excluir WHERE TRIM(termo) <> ''")
                rows = cur.fetchall()
                terms = [r[0] for r in rows if r and r[0]]
            conn.close()
    except Exception:
        pass
    if not terms and BLOCKLIST_CSV.exists():
        try:
            with open(BLOCKLIST_CSV, "r", encoding="utf-8") as f:
                rdr = csv.DictReader(f)
                col = "termo" if "termo" in rdr.fieldnames else rdr.fieldnames[0]
                for row in rdr:
                    val = (row.get(col) or "").strip()
                    if val:
                        terms.append(val)
        except Exception:
            try:
                with open(BLOCKLIST_CSV, "r", encoding="utf-8") as f:
                    for line in f:
                        val = line.strip()
                        if val:
                            terms.append(val)
            except Exception:
                pass
    seen = set()
    dedup: List[str] = []
    for t in terms:
        nt = normalize_for_match(t)
        if nt and nt not in seen:
            seen.add(nt)
            dedup.append(nt)
    return dedup

def _build_match_spans(text: str, block_terms_norm: List[str]) -> List[Tuple[int, int]]:
    if not text or not block_terms_norm:
        return []
    n1_chars = []
    map_n1_to_orig = []
    for i, ch in enumerate(text):
        base = strip_accents(ch).lower()
        n1 = base if base.isalnum() else " "
        n1_chars.append(n1)
        map_n1_to_orig.append(i)
    n1 = "".join(n1_chars)

    n2_chars = []
    map_n2_to_n1 = []
    prev_space = True
    for i, ch in enumerate(n1):
        if ch.isalnum():
            n2_chars.append(ch)
            map_n2_to_n1.append(i)
            prev_space = False
        else:
            if not prev_space:
                n2_chars.append(" ")
                map_n2_to_n1.append(i)
            prev_space = True
    n2 = "".join(n2_chars).strip()

    spans: List[Tuple[int, int]] = []
    for term in block_terms_norm:
        if not term:
            continue
        pattern = re.escape(term)
        regex = re.compile(rf"(?<!\w){pattern}(?!\w)")
        for m in regex.finditer(n2):
            start_n2, end_n2 = m.span()
            try:
                start_n1 = map_n2_to_n1[start_n2]
                end_n1 = map_n2_to_n1[end_n2 - 1] + 1
            except Exception:
                continue
            start_orig = map_n1_to_orig[start_n1]
            end_orig = map_n1_to_orig[end_n1 - 1] + 1
            spans.append((start_orig, end_orig))

    if not spans:
        return []

    spans.sort()
    merged = [spans[0]]
    for s, e in spans[1:]:
        ls, le = merged[-1]
        if s <= le:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged

def redact_with_blocklist(text: str, block_terms_norm: List[str], token: str = BLOCK_TOKEN) -> str:
    if not text or not block_terms_norm:
        return text or ""
    spans = _build_match_spans(text, block_terms_norm)
    if not spans:
        return text
    out = []
    last = 0
    for s, e in spans:
        out.append(text[last:s])
        out.append(token)
        last = e
    out.append(text[last:])
    return "".join(out)

# =======================
# Título & PDF
# =======================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_ROOT = PROJECT_ROOT / "NOTAS"
PREFERRED_DIR = PDF_ROOT / "NOTAS_REVISADAS"

def _cleanup_filename(fname: str) -> str:
    if not fname:
        return "(sem título)"
    base = Path(str(fname)).name
    base = re.sub(r"\.(pdf|txt|docx?)$", "", base, flags=re.I)
    base = re.sub(r"[_\-]+", " ", base)
    base = re.sub(r"\s{2,}", " ", base).strip()
    base = re.sub(r"^(nota\s+t[eé]cnica\s*n?[ºo]?\s*)", "Nota Técnica ", base, flags=re.I)
    return base or "(sem título)"

def _pick_note_title_from_text(full_text: str) -> str:
    if not full_text:
        return ""
    first = (full_text.strip().splitlines() or [""])[0].strip()
    if 8 <= len(first) <= 180:
        return first
    return ""

def _resolve_pdf_path(ano: Any, arquivo: str | None, caminho_txt: str | None) -> Path | None:
    if caminho_txt:
        ptxt = Path(caminho_txt)
        cand = ptxt.with_suffix(".pdf")
        if cand.exists():
            return cand

    base = Path(arquivo or "").name
    if not base and caminho_txt:
        base = Path(caminho_txt).with_suffix(".pdf").name
    base_pdf = base if base.lower().endswith(".pdf") else (Path(base).with_suffix(".pdf").name if base else "")

    if base_pdf:
        cand_pref = PREFERRED_DIR / base_pdf
        if cand_pref.exists():
            return cand_pref

    year = None
    try:
        year = int(ano) if ano not in (None, "", "Sem ano") else None
    except Exception:
        year = None
    pdf_dir = (PDF_ROOT / f"NOTAS TÉCNICAS {year}") if year else PDF_ROOT

    if base_pdf:
        cand_legacy = pdf_dir / base_pdf
        if cand_legacy.exists():
            return cand_legacy

    try:
        target_stem = Path(base_pdf).stem.lower() if base_pdf else None
        if target_stem:
            if PREFERRED_DIR.exists():
                for f in PREFERRED_DIR.rglob("*.pdf"):
                    if f.name.lower() == base_pdf.lower() or f.stem.lower() == target_stem:
                        return f
            for f in pdf_dir.rglob("*.pdf"):
                if f.name.lower() == base_pdf.lower() or f.stem.lower() == target_stem:
                    return f
    except Exception:
        pass

    return None

# ---------- Visualização inline de PDF (zoom fixo 200%) ----------
def _render_pdf_inline(pdf_path: Path, key_prefix: str):
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        st.warning(f"Falha ao abrir PDF: {e}")
        return

    page_count = len(doc)
    c1, csp = st.columns([1, 5])
    with c1:
        page_idx = st.number_input(
            "Página", min_value=1, max_value=page_count, value=1, step=1,
            key=f"{key_prefix}_page"
        )
    with csp:
        st.write(f"{page_count} página(s) • {pdf_path.name} • Zoom: 200%")

    try:
        zoom = 200
        mat = fitz.Matrix(zoom/100.0, zoom/100.0)
        page = doc[int(page_idx) - 1]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        st.image(pix.tobytes("png"), use_container_width=True)
    except Exception as e:
        st.warning(f"Falha ao renderizar: {e}")
    finally:
        doc.close()

# ============== Resumo contextual do PDF ==============
def _pdf_context_snippet(pdf_path: Path, terms_query: List[str],
                         before_words: int = 100, after_words: int = 100) -> str:
    import fitz, re
    if not pdf_path or not pdf_path.exists():
        return ""
    terms = [t for t in terms_query if t]
    if not terms:
        return ""
    pattern = re.compile("(" + "|".join(re.escape(t) for t in terms) + ")", re.IGNORECASE)

    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            text = page.get_text("text") or ""
            if not text:
                continue
            m = pattern.search(text)
            if not m:
                continue

            tokens = list(re.finditer(r"\w+|\S", text, flags=re.UNICODE))
            start = m.start()
            match_tok_idx = next((i for i, tok in enumerate(tokens) if tok.start() <= start < tok.end()), None)
            if match_tok_idx is None:
                continue

            word_token_idxs = [i for i, tok in enumerate(tokens) if re.match(r"\w+", tok.group(0), flags=re.UNICODE)]
            if re.match(r"\w+", tokens[match_tok_idx].group(0), flags=re.UNICODE):
                word_pos = sum(1 for i in word_token_idxs if i < match_tok_idx)
            else:
                right = next((j for j in word_token_idxs if j >= match_tok_idx), word_token_idxs[-1])
                word_pos = sum(1 for i in word_token_idxs if i < right)

            left_w = max(0, word_pos - before_words)
            right_w = min(len(word_token_idxs) - 1, word_pos + after_words)
            left_tok = word_token_idxs[left_w]
            right_tok = word_token_idxs[right_w]

            snippet = text[tokens[left_tok].start() : tokens[right_tok].end()]
            if tokens[left_tok].start() > 0:
                snippet = "… " + snippet
            if tokens[right_tok].end() < len(text):
                snippet = snippet + " …"
            return snippet
    return ""

def apply_redaction(text: str) -> str:
    if not REMOVE_ON_DISPLAY or not text:
        return text or ""
    return redact_with_blocklist(text, load_blocklist(), BLOCK_TOKEN)

def _build_resumo(pdf_path: Path, db_snippet: str, terms_query: List[str]) -> str:
    resumo_src = ""
    if pdf_path and pdf_path.exists():
        resumo_src = _pdf_context_snippet(pdf_path, terms_query, 100, 100)
    if not resumo_src:
        if db_snippet and db_snippet.strip():
            resumo_src = db_snippet
        else:
            resumo_src = "(sem trecho disponível no PDF para os termos buscados)"
    resumo_clean = apply_redaction(resumo_src)
    return highlight(resumo_clean, terms_query)

# ---------------- UI e lógica principal ----------------
hero("Pesquisa de Notas")


q = st.text_input(
    "Pesquise por palavra-chave...",
    key="q",
    placeholder="ex.: abono permanência 2024"
)

# --- FILTRO: somente por ANO (com opção "Todas") ---
def get_year_options():
    opts = ["Todas"]
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT ano FROM notas ORDER BY ano DESC")
            rows = cur.fetchall()
            for r in rows:
                val = r[0]
                if val is None or str(val).strip() == "":
                    continue
                opts.append(str(val))
            conn.close()
    except Exception:
        pass
    return opts

col_filtros = st.columns([1])
with col_filtros[0]:
    year_opts = get_year_options()
    selected_year = st.selectbox("Ano", year_opts, index=0)

# estado de paginação / busca
if "pesq_offset" not in st.session_state:
    st.session_state.pesq_offset = 0
if "pesq_last_query" not in st.session_state:
    st.session_state.pesq_last_query = ""
if "open_sha" not in st.session_state:
    st.session_state.open_sha = None
if "pesq_submitted" not in st.session_state:
    st.session_state.pesq_submitted = False

def do_search():
    st.session_state.pesq_offset = 0
    st.session_state.pesq_submitted = True
    st.session_state.open_sha = None

st.button("Buscar", type="primary", on_click=do_search, key="btn_buscar")

section("Resultados")

# Quando não submeteu ainda
if not st.session_state.pesq_submitted:
    st.info("Informe termos de pesquisa e clique em Buscar.")
    st.stop()

# Se o usuário quer ver todas as notas do banco e não forneceu query:
if (not q.strip()) and (selected_year == "Todas"):
    # usamos um marcador especial para retornar tudo
    search_term = "__ALL__"
else:
    # seja a query do usuário (pode ser vazia, mas aí search_db tratará)
    search_term = q.strip()

# evita repetir pagina quando query mudou
if q.strip() != st.session_state.pesq_last_query:
    st.session_state.pesq_last_query = q.strip()
    st.session_state.pesq_offset = 0

# chama a busca com filtro de ano (selected_year pode ser "Todas")
rows, total, mecanismo = search_db(search_term, PAGE_SIZE, st.session_state.pesq_offset, year_filter=(None if selected_year in ("Todas", "Todos") else selected_year))

if total == 0:
    st.write("Nenhum resultado encontrado.")
    st.stop()

st.caption(f"{total} resultado(s)")

terms = tokenize_query(q)

def safe_int_year(a):
    try:
        return int(a) if a not in (None, "", "Sem ano") else -1
    except Exception:
        return -1

rows_sorted = sorted(
    rows,
    key=lambda r: (-safe_int_year(r.get("ano")), r.get("score", 0.0))
)

def _badge_and_class(situacao: str | None, em_vigor: Any) -> Tuple[str, str]:
    s = (situacao or "").strip().lower()
    if s.startswith("parcial"):
        return '<span class="badge parcial">PARCIAL</span>', "parcial"
    # Se vier sem situacao, cai no fallback por em_vigor
    if s.startswith("revog"):
        return '<span class="badge revogada">REVOGADA</span>', "revogada"
    # fallback por em_vigor quando situacao não está definida
    if em_vigor in (0, "0", False, "False"):
        return '<span class="badge revogada">REVOGADA</span>', "revogada"
    return '<span class="badge vigente">VIGENTE</span>', "vigente"

def render_item_layout(r: Dict[str, Any], terms_query: List[str]):
    ano = r.get("ano") or ""
    snippet = r.get("snippet") or ""
    caminho_txt = r.get("caminho_txt") or ""
    arquivo = r.get("arquivo") or ""

    full_text = ""
    if caminho_txt and os.path.exists(caminho_txt):
        try:
            full_text = read_txt(caminho_txt)
        except Exception:
            full_text = ""

    titulo_txt = _pick_note_title_from_text(full_text)
    nome = titulo_txt if titulo_txt else _cleanup_filename(arquivo or "(sem nome)")

    pdf_path_for_snippet = _resolve_pdf_path(ano, arquivo, caminho_txt)
    resumo_html = _build_resumo(pdf_path_for_snippet, snippet, terms_query)

    situacao = r.get("situacao")
    em_vigor = r.get("em_vigor", None)
    justificativa = (r.get("justificativa_situacao") or "").strip()
    situacao_badge, card_class = _badge_and_class(situacao, em_vigor)

    # monta linha meta já com observação junto ao badge
    meta_line = f"{ano} • {situacao_badge}"
    if justificativa and (card_class in ("revogada", "parcial")):
        meta_line += f" — <span class='note-justif-inline'>Pela: {justificativa}</span>"

    with st.container():
        st.markdown(
            f"""
            <div class="note-card {card_class}">
              <div class="note-title">{nome}</div>
              <div class="meta-line">{meta_line}</div>
              <div class="note-resumo clamp-2">{resumo_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns([1, 3])
        with cols[0]:
            pdf_path = _resolve_pdf_path(ano, arquivo, caminho_txt)
            if pdf_path and pdf_path.exists():
                try:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "⬇️ Baixar PDF",
                            data=f,
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            key=f"download_pdf_{r['sha']}"
                        )
                except Exception as e:
                    st.warning(f"Falha ao preparar PDF: {e}")
            elif caminho_txt and os.path.exists(caminho_txt):
                try:
                    content = full_text if full_text else read_txt(caminho_txt)
                    filename = Path(caminho_txt).name
                    st.download_button(
                        "⬇️ Download (TXT)",
                        data=content.encode("utf-8", errors="ignore"),
                        file_name=filename,
                        mime="text/plain",
                        key=f"download_txt_{r['sha']}"
                    )
                except Exception as e:
                    st.warning(f"Falha ao preparar download: {e}")
            else:
                st.button("⬇️ Baixar PDF", disabled=True, key=f"download_{r['sha']}_disabled")

        with cols[1]:
            with st.expander("📄 Visualizar documento", expanded=False):
                pdf_path = _resolve_pdf_path(ano, arquivo, caminho_txt)
                if pdf_path and pdf_path.exists():
                    _render_pdf_inline(pdf_path, key_prefix=f"view_{r['sha']}")
                elif caminho_txt and os.path.exists(caminho_txt):
                    display_text = apply_redaction(full_text)
                    if len(display_text) <= 150_000:
                        st.text_area("Texto completo (com remoção aplicada)", display_text, height=420)
                    else:
                        st.warning("Texto muito grande; abra o arquivo no seu editor.")
                else:
                    st.warning("Documento não encontrado no disco.")

# Agrupa por ano e renderiza
buckets: Dict[str, List[Dict[str, Any]]] = {}
for r in rows_sorted:
    ano = str(r.get("ano") or "Sem ano")
    buckets.setdefault(ano, []).append(r)

for ano_key in sorted(buckets.keys(), key=lambda k: -safe_int_year(k)):
    st.subheader(f"Ano {ano_key}")
    for r in buckets[ano_key]:
        with st.container(border=False):
            render_item_layout(r, terms)

# Paginação
prev_col, next_col, page_info = st.columns([1, 1, 2])
with prev_col:
    st.button(
        "⬅️ Anterior",
        disabled=st.session_state.pesq_offset == 0,
        key="btn_prev",
        on_click=lambda: (
            st.session_state.update(pesq_offset=max(0, st.session_state.pesq_offset - PAGE_SIZE)),
            st.rerun()
        )
    )
with next_col:
    st.button(
        "Próxima ➡️",
        disabled=(st.session_state.pesq_offset + PAGE_SIZE) >= total,
        key="btn_next",
        on_click=lambda: (
            st.session_state.update(pesq_offset=st.session_state.pesq_offset + PAGE_SIZE),
            st.rerun()
        )
    )
with page_info:
    pagina_atual = (st.session_state.pesq_offset // PAGE_SIZE) + 1
    total_pag = (total + PAGE_SIZE - 1) // PAGE_SIZE
    st.write(f"Página {pagina_atual} de {total_pag}")
