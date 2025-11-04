# pages/2_📥_Importacao.py
import io
import re as _re
import re
import csv
import hashlib
import sqlite3
import base64
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import streamlit as st

from core.sidebar import render_sidebar
from core.ui import hero, section

# -------------------- Configs do projeto --------------------
st.set_page_config(page_title="Importação", page_icon="📥", layout="wide")

# =======================
# ESTILO / ASSETS
# =======================
ROOT = Path(__file__).resolve().parents[1]
STYLES_PATH = ROOT / "styles" / "style.css"
ASSETS_PATH = ROOT / "assets"

def load_css(path: Path = STYLES_PATH):
    try:
        if path.exists():
            css = path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Falha ao carregar CSS: {e}")

def file_to_b64(path: Path) -> str:
    try:
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception:
        pass
    return ""

def get_logo_b64() -> tuple[str, str]:
    svg_b64 = file_to_b64(ASSETS_PATH / "logo.svg")
    if svg_b64:
        return svg_b64, "image/svg+xml"
    png_b64 = file_to_b64(ASSETS_PATH / "inss_logo.png")
    if png_b64:
        return png_b64, "image/png"
    return "", ""

def inject_header_with_logo(title_text: str = "REPOSITÓRIO DE NOTAS TÉCNICAS DO INSS"):
    try:
        logo_b64, logo_mime = get_logo_b64()
    except Exception:
        logo_b64, logo_mime = "", ""

    css = ["<style>"]
    if logo_b64 and logo_mime:
        css.append(f"""
        [data-testid="stHeader"]::before {{
          content: "";
          position: absolute;
          left: calc(var(--toggle-safe) + 8px);
          top: 50%;
          transform: translateY(-50%);
          width: 130px;
          height: 30px;
          background-image: url("data:{logo_mime};base64,{logo_b64}");
          background-repeat: no-repeat;
          background-size: contain;
          opacity: 1;
          pointer-events: none;
          z-index: 0;
        }}
        """)
    css.append(f"""
    [data-testid="stHeader"]::after {{
      content: "{title_text}";
      position: absolute;
      left: 0; right: 0;
      top: 50%;
      transform: translateY(-50%);
      text-align: center;
      font-weight: 800;
      font-size: 18px;
      color: var(--header-fg);
    }}
    </style>
    """)
    st.markdown("".join(css), unsafe_allow_html=True)

# Carrega CSS global e injeta logo/título
load_css()
inject_header_with_logo("REPOSITÓRIO DE NOTAS TÉCNICAS DO INSS")

# ========================
# Sidebar
# ========================
with st.sidebar:
    render_sidebar()

hero("📥 Importação", "Envie novas Notas, revise os metadados e salve no banco")
section("🗂️ Rascunhos de Notas")

# Caminhos
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH       = PROJECT_ROOT / "data" / "processed" / "notas.db"
TERMS_CSV     = PROJECT_ROOT / "data" / "terms" / "termos_excluir.csv"
PDF_SAVE_DIR  = PROJECT_ROOT / "NOTAS" / "NOTAS_REVISADAS"
PDF_SAVE_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- Utilidades/DB --------------------
def _ensure_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tabela base
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            sha TEXT PRIMARY KEY,
            ano INTEGER,
            arquivo TEXT,
            snippet TEXT,
            caminho_txt TEXT,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Colunas adicionais
    cur.execute("PRAGMA table_info(notas)")
    cols = {row[1] for row in cur.fetchall()}

    if "em_vigor" not in cols:
        cur.execute("ALTER TABLE notas ADD COLUMN em_vigor INTEGER DEFAULT 1")
        cur.execute("UPDATE notas SET em_vigor = 1 WHERE em_vigor IS NULL")

    if "situacao" not in cols:
        cur.execute("ALTER TABLE notas ADD COLUMN situacao TEXT DEFAULT NULL")

    if "justificativa_situacao" not in cols:
        cur.execute("ALTER TABLE notas ADD COLUMN justificativa_situacao TEXT DEFAULT NULL")

    # Índices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notas_ano ON notas(ano)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notas_imported_at ON notas(imported_at)")

    # FTS (recria se necessário)
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='fts_notas'")
    row = cur.fetchone()
    needs_recreate = False
    if row is None:
        needs_recreate = True
    else:
        ddl = (row[0] or "").lower()
        if "content" not in ddl:
            needs_recreate = True

    if needs_recreate:
        cur.execute("DROP TABLE IF EXISTS fts_notas")
        cur.execute("""
            CREATE VIRTUAL TABLE fts_notas USING fts5(
                content,
                sha UNINDEXED,
                tokenize='unicode61'
            )
        """)

    conn.commit()
    conn.close()

def recreate_fts_and_reindex():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS fts_notas")
    cur.execute("""
        CREATE VIRTUAL TABLE fts_notas USING fts5(
            content,
            sha UNINDEXED,
            tokenize='unicode61'
        )
    """)
    rows = cur.execute("SELECT sha, COALESCE(snippet, '') FROM notas").fetchall()
    if rows:
        cur.executemany("INSERT INTO fts_notas (content, sha) VALUES (?, ?)", rows)
    conn.commit()
    conn.close()

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _upsert_note(sha: str, ano: int, arquivo: str, snippet: str, em_vigor: int,
                 situacao: Optional[str] = None, justificativa_situacao: Optional[str] = None,
                 caminho_txt: Optional[str] = None):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notas (sha, ano, arquivo, snippet, em_vigor, situacao, justificativa_situacao, caminho_txt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sha) DO UPDATE SET
            ano = excluded.ano,
            arquivo = excluded.arquivo,
            snippet = excluded.snippet,
            em_vigor = excluded.em_vigor,
            situacao = excluded.situacao,
            justificativa_situacao = excluded.justificativa_situacao,
            caminho_txt = COALESCE(excluded.caminho_txt, notas.caminho_txt),
            imported_at = CURRENT_TIMESTAMP
    """, (sha, ano, arquivo, snippet, em_vigor, situacao, justificativa_situacao, caminho_txt))
    conn.commit()
    conn.close()

def _update_fts(sha: str, content: str):
    conn = _connect()
    cur = conn.cursor()
    # remove antigo
    cur.execute("DELETE FROM fts_notas WHERE sha = ?", (sha,))
    # insere novo
    cur.execute("INSERT INTO fts_notas (content, sha) VALUES (?, ?)", (content or "", sha))
    conn.commit()
    conn.close()

def _compute_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _safe_decode_txt(data: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")

# -------------------- Anonimização --------------------
_PUNCT_TRANS = str.maketrans({c: " " for c in "-_./\\,:;!?'\"()[]{}<>|@#*$%^&+=`~"})

def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")

def _normalize_for_match(s: str) -> str:
    s2 = _strip_accents(s).lower().translate(_PUNCT_TRANS)
    return _re.sub(r"\s+", " ", s2).strip()

def _load_blocklist() -> List[str]:
    terms: List[str] = []
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='termos_excluir'")
            if cur.fetchone():
                cur.execute("SELECT termo FROM termos_excluir WHERE TRIM(termo) <> ''")
                terms = [r[0] for r in cur.fetchall() if r and r[0]]
            conn.close()
    except Exception:
        pass

    if not terms and TERMS_CSV.exists():
        try:
            with open(TERMS_CSV, "r", encoding="utf-8") as f:
                rdr = csv.DictReader(f)
                col = "termo" if "termo" in rdr.fieldnames else rdr.fieldnames[0]
                for row in rdr:
                    val = (row.get(col) or "").strip()
                    if val:
                        terms.append(val)
        except Exception:
            try:
                with open(TERMS_CSV, "r", encoding="utf-8") as f:
                    for line in f:
                        val = line.strip()
                        if val:
                            terms.append(val)
            except Exception:
                pass

    # normaliza e deduplica
    seen = set()
    dedup: List[str] = []
    for t in terms:
        nt = _normalize_for_match(t)
        if nt and nt not in seen:
            seen.add(nt)
            dedup.append(nt)
    return dedup

def _apply_redaction(text: str) -> str:
    if not text:
        return ""
    block_terms = _load_blocklist()
    if not block_terms:
        return text
    # normalizado por palavras, substitui por token
    token = "[REMOVIDO]"
    # Implementação simples: substitui termos inteiros (já normalizados)
    # Estratégia: gerar uma versão normalizada do texto para localizar spans
    def _build_match_spans(text: str, block_terms_norm: List[str]) -> List[Tuple[int, int]]:
        if not text or not block_terms_norm:
            return []
        n1_chars = []
        map_n1_to_orig = []
        for i, ch in enumerate(text):
            base = _strip_accents(ch).lower()
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
        import re as _r
        for term in block_terms_norm:
            if not term:
                continue
            pattern = _r.escape(term)
            regex = _r.compile(rf"(?<!\w){pattern}(?!\w)")
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

    spans = _build_match_spans(text, block_terms)
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

# -------------------- PDF/TXT helpers --------------------
def _extract_text_from_pdf(raw: bytes) -> str:
    try:
        import fitz  # PyMuPDF
        with fitz.open(stream=raw, filetype="pdf") as doc:
            texts = []
            for page in doc:
                texts.append(page.get_text("text") or "")
            return "\n".join(texts)
    except Exception as e:
        return ""

def _make_snippet_for_db(text: str, max_len: int = 400) -> str:
    if not text:
        return ""
    t = " ".join(text.split())
    return t[:max_len]

def _detect_year_from_name(name: str) -> Optional[int]:
    m = re.search(r"(19|20)\d{2}", name)
    try:
        if m:
            y = int(m.group(0))
            if 1900 <= y <= 2100:
                return y
    except Exception:
        pass
    return None

# -------------------- Nome de arquivo (sem duplicados) --------------------
def _sanitize_filename(name: str) -> str:
    invalid = r'<>:"/\\|?*'
    # remove sufixos tipo " (2)" ao final, normaliza espaços
    name = (name or "").strip()
    name = _re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = _re.sub(r"\s{2,}", " ", name)
    # remove extensão, vamos controlar por ext final
    stem = Path(name).stem
    stem = "".join("_" if c in invalid else c for c in stem).strip()
    return stem[:180] or "arquivo"

def _normalize_file_output(name: str, ext: str) -> str:
    """
    Normaliza o 'nome a exibir' para nome final (com extensão),
    removendo sufixos numéricos e espaços extras.
    """
    stem = _sanitize_filename(name)
    return f"{stem}{(ext or '.pdf').lower()}"

def _existing_filenames_set() -> set[str]:
    """
    Conjunto de nomes já existentes no diretório de PDFs e no banco (coluna 'arquivo').
    """
    names = {p.name for p in PDF_SAVE_DIR.glob("*.*")}
    try:
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT arquivo FROM notas WHERE arquivo IS NOT NULL AND TRIM(arquivo)<>''")
        for (fname,) in cur.fetchall():
            names.add(fname)
        conn.close()
    except Exception:
        pass
    return names

def _resolve_name_conflict_numeric(dirpath: Path, stem: str, ext: str) -> Path:
    """
    Mantido por compatibilidade, mas NÃO numera mais.
    A regra agora é bloquear nomes duplicados (em staging e salvamento).
    """
    return dirpath / f"{stem}{ext}"

# -------------------- Staging (uploads) --------------------
def _stage_files(uploaded_files):
    if "pending_imports" not in st.session_state:
        st.session_state["pending_imports"] = {}

    pend: Dict[str, Any] = st.session_state["pending_imports"]

    # Conjunto de nomes já em staging
    def _staged_names() -> set[str]:
        return {
            _normalize_file_output(v["display_name"], v["ext"] or ".pdf")
            for v in pend.values()
        }

    for uf in uploaded_files:
        raw = uf.read()
        if not raw:
            st.warning(f"{uf.name}: arquivo vazio — ignorado.")
            continue

        sha = _compute_sha(raw)
        if sha in pend:
            # já foi enviado nesta sessão
            continue

        if uf.type == "application/pdf" or Path(uf.name).suffix.lower() == ".pdf":
            full_text = _extract_text_from_pdf(raw)
            ext = ".pdf"
        else:
            full_text = _safe_decode_txt(raw)
            ext = Path(uf.name).suffix.lower() or ".txt"

        text_redacted = _apply_redaction(full_text)
        auto_snippet = _make_snippet_for_db(text_redacted, 400)
        ano_auto = _detect_year_from_name(uf.name)
        suggested_display = Path(uf.name).stem

        # ⛔ Bloqueio de duplicados (staging): nome final calculado
        final_candidate = _normalize_file_output(suggested_display, ext)
        existing = _existing_filenames_set()
        staged = _staged_names()
        if final_candidate in existing or final_candidate in staged:
            st.warning(f"O arquivo '{final_candidate}' já existe. Altere o 'Nome a exibir' antes de enviar.")
            continue

        pend[sha] = {
            "original_name": Path(uf.name).name,
            "ext": ext,
            "bytes": raw,
            "text_redacted": text_redacted,
            "snippet": auto_snippet,
            "display_name": suggested_display,
            "status_int": 1,
            "ano": ano_auto,
        }

# -------------------- UI: Upload + Ações --------------------
uploaded_files = st.file_uploader(
    "Selecione PDF(s) ou TXT(s) para preparar (nada será salvo até você confirmar)",
    type=["pdf", "txt"],
    accept_multiple_files=True
)

colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("🔁 Recriar índice FTS (usar em caso de erro no FTS)"):
        _ensure_db()
        recreate_fts_and_reindex()
        st.success("FTS recriado e reindexado a partir de 'notas' (usando snippet como fallback).")

with colB:
    if st.button("🧹 Limpar rascunhos (não afeta o banco)"):
        st.session_state.pop("pending_imports", None)
        st.rerun()

if uploaded_files:
    _stage_files(uploaded_files)

# -------------------- UI: Edição dos rascunhos --------------------
pend = st.session_state.get("pending_imports", {})

STATUS_LABEL_TO_INT = {
    "Vigente": 1,
    "Parcialmente revogada": 1,  # em_vigor continua 1; controle textual via 'situacao'
    "Revogada": 0,
}

if not pend:
    st.info("Envie arquivos para iniciar o preparo e a edição dos metadados antes de salvar no banco.")
else:
    _ensure_db()
    st.caption("Edite os metadados de cada nota abaixo. O nome exibido também será o nome do arquivo salvo no disco.")

    for sha, item in list(pend.items()):
        with st.expander(f"📝 {item['original_name']}", expanded=False):
            c1, c2 = st.columns([2, 1])
            with c1:
                new_name = st.text_input(
                    "Nome a exibir (será salvo como nome do arquivo)",
                    key=f"name_{sha}",
                    value=item["display_name"],
                    help="Ex.: Nota Técnica nº 123/2025 - Tema XYZ"
                )
                resumo = st.text_area(
                    "Resumo (snippet exibido na pesquisa)",
                    key=f"snippet_{sha}",
                    value=item["snippet"],
                    height=140
                )
            with c2:
                ano = st.number_input(
                    "Ano",
                    key=f"ano_{sha}",
                    min_value=1900, max_value=2100,
                    value=int(item["ano"] or datetime.now().year)
                )
                status_label = st.selectbox(
                    "Status",
                    ["Vigente", "Parcialmente revogada", "Revogada"],
                    key=f"status_{sha}",
                    index=0
                )
                if st.button("Remover este rascunho", key=f"remove_{sha}"):
                    pend.pop(sha, None)
                    st.rerun()

            item["display_name"] = new_name
            item["snippet"] = resumo
            item["ano"] = ano
            item["status_int"] = STATUS_LABEL_TO_INT[status_label]
            # Também guardamos situacao textual quando aplicável
            item["situacao"] = status_label
            item["justificativa_situacao"] = ""  # campo livre via Configuração avançada (ou ajuste aqui se quiser)

        st.markdown("---")

    if st.button("💾 Salvar TODOS os rascunhos no banco e refletir na pesquisa"):
        saved, errors = 0, []
        # zera conjunto de vistos para esta execução do botão (defesa dupla)
        st.session_state[".__seen_names__"] = set()

        for sha, item in pend.items():
            try:
                # nome final (sem sufixos, sem duplicação)
                final_file_stem = _sanitize_filename(item["display_name"])
                ext = item["ext"] or ".pdf"
                final_name = _normalize_file_output(final_file_stem, ext)

                # Defesa dupla: checa duplicidade entre os próprios rascunhos e contra disco/DB
                seen = st.session_state[".__seen_names__"]
                existing = _existing_filenames_set()

                if (final_name in seen) or (final_name in existing):
                    raise FileExistsError(f"O arquivo '{final_name}' já existe. Ajuste o 'Nome a exibir'.")

                seen.add(final_name)
                out_path = PDF_SAVE_DIR / final_name

                with open(out_path, "wb") as f:
                    f.write(item["bytes"])

                # grava no banco
                _upsert_note(
                    sha=sha,
                    ano=int(item["ano"] or datetime.now().year),
                    arquivo=out_path.name,
                    snippet=item["snippet"],
                    em_vigor=int(item["status_int"]),
                    situacao=item.get("situacao"),
                    justificativa_situacao=item.get("justificativa_situacao") or None,
                    caminho_txt=None  # se tiver TXT associado, pode preencher aqui
                )

                # indexa no FTS o conteúdo anonimizado
                _update_fts(sha=sha, content=item["text_redacted"])
                saved += 1

            except Exception as e:
                errors.append(f"{item.get('original_name','?')}: {e}")

        # limpa staging depois da tentativa
        st.session_state.pop("pending_imports", None)

        if saved:
            st.success(f"{saved} nota(s) salva(s) no banco e indexadas. Já aparecem na pesquisa.")
        if errors:
            with st.expander("Ocorreram erros durante a gravação", expanded=True):
                for line in errors:
                    st.write("• " + line)
