# pages/3_🛠️_Configuracao_Nota.py
import re
import base64
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Set, Dict

import streamlit as st
from core.ui import hero, section
from core.state import AUTH_STATUS, USER_ROLES
from core.sidebar import render_sidebar

# -------------------- Página / estilo / header --------------------
st.set_page_config(page_title="Configuração da Nota", page_icon="🛠️", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
STYLES_PATH = ROOT / "styles" / "style.css"
ASSETS_PATH = ROOT / "assets"

def load_css(path: Path = STYLES_PATH):
    try:
        if path.exists():
            st.markdown(f"<style>{path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Falha ao carregar CSS: {e}")

def file_to_b64(path: Path) -> str:
    try:
        if path.exists():
            import base64 as _b64
            return _b64.b64encode(path.read_bytes()).decode("utf-8")
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

def inject_header_with_logo(title_text: str):
    try:
        logo_b64, logo_mime = get_logo_b64()
    except Exception:
        logo_b64, logo_mime = "", ""
    css = ["<style>"]
    if logo_b64 and logo_mime:
        css.append(f"""
        [data-testid="stHeader"]::before {{
          content: ""; position: absolute; left: calc(var(--toggle-safe) + 8px); top: 50%;
          transform: translateY(-50%); width:130px; height:30px;
          background-image: url("data:{logo_mime};base64,{logo_b64}");
          background-repeat: no-repeat; background-size: contain; opacity:1; z-index:0;
        }}""")
    css.append(f"""
    [data-testid="stHeader"]::after {{
      content: "{title_text}";
      position:absolute; left:0; right:0; top:50%; transform:translateY(-50%);
      text-align:center; font-weight:800; font-size:18px; color: var(--header-fg);
    }}
    /* Estilo dos "cards" (expanders) e margens dos inputs */
    .stExpander {{ border: 1px solid rgba(0,0,0,.06); border-radius: 16px; }}
    .stExpander > div {{ padding: 12px 14px; }}
    .exp-sub {{ color: var(--text-muted, #6b7280); font-size:13px; margin-top:6px; }}
    .tag {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:700; }}
    .tag.ok {{ background:#DCFCE7; color:#166534; }}
    .tag.warn {{ background:#FEF3C7; color:#92400E; }}
    .tag.danger {{ background:#FEE2E2; color:#991B1B; }}

    /* Margens/realce dos inputs dentro do editor */
    .cfg-form [data-testid="stTextInput"],
    .cfg-form [data-testid="stNumberInput"],
    .cfg-form [data-testid="stSelectbox"],
    .cfg-form [data-testid="stTextArea"] {{ margin-top: 8px; margin-bottom: 12px; }}
    .cfg-form textarea, .cfg-form input {{ background: rgba(0,0,0,0.02); }}
    </style>""")
    st.markdown("".join(css), unsafe_allow_html=True)

load_css()
inject_header_with_logo("REPOSITÓRIO DE NOTAS TÉCNICAS DO INSS")

with st.sidebar:
    render_sidebar()

# -------------------- Auth --------------------
if not st.session_state.get(AUTH_STATUS) or (
    "ANALISTA" not in st.session_state.get(USER_ROLES, []) and
    "ADMIN" not in st.session_state.get(USER_ROLES, [])
):
    st.error("Acesso restrito. Faça login com perfil ANALISTA ou ADMIN.")
    st.stop()

# -------------------- Caminhos / estado --------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH      = PROJECT_ROOT / "data" / "processed" / "notas.db"
PDF_DIR      = PROJECT_ROOT / "NOTAS" / "NOTAS_REVISADAS"

# Estado persistente para busca e card aberto
st.session_state.setdefault("search_q", "")
st.session_state.setdefault("open_card_sha", None)
st.session_state.setdefault("fts_msg", None)  # mensagem pós-reindex

# -------------------- Utilitários FS / DB --------------------
def _sanitize_filename(name: str) -> str:
    import re
    invalid = r'<>:"/\\|?*'
    name = "".join("_" if c in invalid else c for c in name)
    name = name.strip()
    # remove sufixo tipo " (2)" no final
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    # normaliza espaços múltiplos
    name = re.sub(r"\s{2,}", " ", name)
    return name[:180] or "arquivo"

def _resolve_name_conflict_numeric(dirpath: Path, stem: str, ext: str) -> Path:
    # Sem numeração: retorna sempre o mesmo caminho (sobrescreve ao renomear)
    return dirpath / f"{stem}{ext}"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_schema():
    conn = _connect(); cur = conn.cursor()
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
    cols = {r[1]: True for r in cur.execute("PRAGMA table_info(notas)").fetchall()}
    if "em_vigor" not in cols:
        cur.execute("ALTER TABLE notas ADD COLUMN em_vigor INTEGER DEFAULT 1")
        cur.execute("UPDATE notas SET em_vigor = 1 WHERE em_vigor IS NULL")
    if "situacao" not in cols:
        cur.execute("ALTER TABLE notas ADD COLUMN situacao TEXT")
    if "justificativa_situacao" not in cols:
        cur.execute("ALTER TABLE notas ADD COLUMN justificativa_situacao TEXT")
    # FTS
    ddl = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='fts_notas'").fetchone()
    if not ddl or "content" not in (ddl[0] or "").lower():
        cur.execute("DROP TABLE IF EXISTS fts_notas")
        cur.execute("""CREATE VIRTUAL TABLE fts_notas USING fts5(
            content, sha UNINDEXED, tokenize='unicode61'
        )""")
    conn.commit(); conn.close()

_ensure_schema()

def reindex_fts_missing() -> int:
    conn = _connect(); cur = conn.cursor()
    miss = cur.execute("""
        SELECT n.sha, COALESCE(n.snippet, '')
          FROM notas n
         WHERE NOT EXISTS (SELECT 1 FROM fts_notas f WHERE f.sha = n.sha)
    """).fetchall()
    if miss:
        cur.executemany("INSERT INTO fts_notas (content, sha) VALUES (?, ?)",
                        [(r[1], r[0]) for r in miss])
        conn.commit()
    conn.close()
    return len(miss or [])

def carregar_conteudo(sha: str) -> str:
    conn = _connect(); cur = conn.cursor()
    row = cur.execute("SELECT content FROM fts_notas WHERE sha = ? LIMIT 1", (sha,)).fetchone()
    conn.close()
    return (row["content"] if row and row["content"] else "") if row else ""

def salvar_texto(sha: str, texto: str):
    conn = _connect(); cur = conn.cursor()
    cur.execute("DELETE FROM fts_notas WHERE sha = ?", (sha,))
    cur.execute("INSERT INTO fts_notas (content, sha) VALUES (?, ?)", (texto or "", sha))
    snippet = (texto[:400] + ("..." if len(texto) > 400 else "")) if texto else ""
    cur.execute("UPDATE notas SET snippet = ? WHERE sha = ?", (snippet, sha))
    conn.commit(); conn.close()

# ---- Extensão segura (evita .txt.txt…) ----
KNOWN_EXTS = {".pdf", ".txt"}

def _strip_known_ext_from_input(name: str) -> str:
    """Remove .pdf/.txt do final do que o usuário digitou, se houver."""
    n = name.strip()
    lower = n.lower()
    for ext in KNOWN_EXTS:
        if lower.endswith(ext):
            return n[: -len(ext)]
    return n

def salvar_metadados(sha: str, titulo_stem: str, ano: int, situacao: str, justificativa: Optional[str]) -> str:
    # Mapeia situação
    if situacao == "Vigente":
        em_vigor, situ_txt = 1, "Vigente"
    elif situacao == "Parcialmente revogada":
        em_vigor, situ_txt = 1, "Parcialmente revogada"
    else:
        em_vigor, situ_txt = 0, "Revogada"

    # Usa SEMPRE a última extensão atual do arquivo (evita .txt.txt…)
    conn = _connect(); cur = conn.cursor()
    row = cur.execute("SELECT arquivo FROM notas WHERE sha = ?", (sha,)).fetchone()
    old_name = (row["arquivo"] or "") if row else ""
    old_ext = Path(old_name).suffix or ".pdf"   # <<< somente a ÚLTIMA extensão (.pdf ou .txt)

    safe_stem = _sanitize_filename(titulo_stem)
    new_path = _resolve_name_conflict_numeric(PDF_DIR, safe_stem, old_ext)

    try:
        if old_name:
            old_path = PDF_DIR / old_name
            if old_path.exists() and new_path.name != old_path.name:
                old_path.rename(new_path)
            novo_arquivo = new_path.name
        else:
            novo_arquivo = f"{safe_stem}{old_ext}"
    except Exception:
        novo_arquivo = f"{safe_stem}{old_ext}"

    cur.execute("""
        UPDATE notas
           SET arquivo = ?, ano = ?, em_vigor = ?, situacao = ?, justificativa_situacao = ?
         WHERE sha = ?
    """, (novo_arquivo, int(ano), em_vigor, situ_txt, (justificativa or None), sha))
    conn.commit(); conn.close()
    return novo_arquivo

# -------------------- Busca --------------------
def _tokenize(q: str) -> List[str]:
    return re.findall(r"\w{2,}", (q or "").lower(), flags=re.UNICODE)[:8]

def _fts_or_query(q: str) -> str:
    terms = _tokenize(q)
    return " OR ".join([t + "*" for t in terms]) if terms else ""

def buscar(q: str, limit: int = 100) -> List[sqlite3.Row]:
    if not q or len(q.strip()) < 2:
        return []
    conn = _connect(); cur = conn.cursor()
    rows: List[sqlite3.Row] = []
    seen: Set[str] = set()
    qfts = _fts_or_query(q)

    if qfts:
        try:
            rs = cur.execute("""
                SELECT n.sha, n.ano, n.arquivo, n.snippet, n.em_vigor, n.situacao,
                       bm25(fts_notas) AS score
                FROM fts_notas JOIN notas n ON n.sha = fts_notas.sha
                WHERE fts_notas MATCH ?
                ORDER BY score ASC, n.imported_at DESC
                LIMIT ?
            """, (qfts, limit)).fetchall()
            for r in rs: rows.append(r); seen.add(r["sha"])
        except sqlite3.OperationalError:
            pass

    if len(rows) < limit:
        terms = _tokenize(q)
        if terms:
            like_and = " AND ".join(["(n.arquivo LIKE ? OR n.snippet LIKE ?)"] * len(terms))
            params: List[str] = []
            for t in terms: params += [f"%{t}%", f"%{t}%"]
            rs = cur.execute(f"""
                SELECT n.sha, n.ano, n.arquivo, n.snippet, n.em_vigor, n.situacao, 0.0 AS score
                FROM notas n
                WHERE {like_and}
                ORDER BY n.imported_at DESC
                LIMIT ?
            """, (*params, limit*2)).fetchall()
            for r in rs:
                if r["sha"] not in seen:
                    rows.append(r); seen.add(r["sha"])
                if len(rows) >= limit: break
    conn.close()
    return rows

# -------------------- UI: Busca + Cards (expander como card) --------------------
hero("🛠️ Configuração da Nota")
section("🔧 Editar notas técnicas")

# --- Barra de busca com FORM: Enter ou clicar em Buscar reindexa FTS + pesquisa ---
with st.container(border=True):
    with st.form("search_form", clear_on_submit=False):
        q_input = st.text_input(
            "Pesquisar nota",
            value=st.session_state["search_q"],
            placeholder="ex.: colemps, 209/2025, abono permanência",
        )
        submitted = st.form_submit_button("Buscar", type="primary")

    if submitted:
        n = reindex_fts_missing()
        st.session_state["fts_msg"] = f"FTS reindexado para {n} nota(s) sem índice."
        st.session_state["search_q"] = q_input.strip()
        st.session_state["open_card_sha"] = None
        st.rerun()

# Mensagem pós-reindex (aparece após o rerun da submissão)
if st.session_state.get("fts_msg"):
    st.info(st.session_state["fts_msg"])
    st.session_state["fts_msg"] = None

# resultados SEM depender do estado do botão (usa search_q atualizado)
results = buscar(st.session_state["search_q"], limit=100) if st.session_state["search_q"] else []

def _badge_html(situ: str) -> str:
    if (situ or "").lower().startswith("parcial"):
        return "<span class='tag warn'>PARCIAL</span>"
    if (situ or "").lower().startswith("revog"):
        return "<span class='tag danger'>REVOGADA</span>"
    return "<span class='tag ok'>VIGENTE</span>"

if results:
    by_year: Dict[Optional[int], List[sqlite3.Row]] = defaultdict(list)
    for r in results:
        by_year[r["ano"]].append(r)

    for ano in sorted(by_year.keys(), reverse=True):
        st.subheader(f"Ano {ano}" if ano else "Sem ano")
        for r in by_year[ano]:
            sha   = r["sha"]
            titulo_full = r["arquivo"] or "(sem título)"
            situ = r["situacao"] or ("Vigente" if (r["em_vigor"] is None or r["em_vigor"] == 1) else "Revogada")
            badge = _badge_html(situ)
            snippet = (r["snippet"] or "").strip()

            exp = st.expander(titulo_full, expanded=(st.session_state["open_card_sha"] == sha))
            with exp:
                st.markdown(badge, unsafe_allow_html=True)
                st.markdown(f"<div class='exp-sub'>{(ano or '')} • {snippet}</div>", unsafe_allow_html=True)

                # Carrega metadados atuais
                conn = _connect(); cur = conn.cursor()
                meta = cur.execute("""
                    SELECT sha, ano, arquivo, snippet, em_vigor, situacao, justificativa_situacao
                      FROM notas WHERE sha = ?
                """, (sha,)).fetchone()
                conn.close()
                texto_atual = carregar_conteudo(sha)

                # Deriva "stem" (nome sem extensão) e a extensão atual (apenas a ÚLTIMA)
                old_name = meta["arquivo"] or ""
                old_ext  = Path(old_name).suffix or ".pdf"
                if old_ext and old_name.endswith(old_ext):
                    old_stem = old_name[: -len(old_ext)]
                else:
                    old_stem = Path(old_name).stem

                # Keys por card (para manter estado)
                k_title   = f"title_{sha}"
                k_year    = f"year_{sha}"        # int (estado interno antigo)
                k_year_txt= f"year_txt_{sha}"    # novo input textual
                k_situ    = f"situ_{sha}"
                k_text    = f"text_{sha}"
                k_just    = f"just_{sha}"

                # Defaults (uma vez)
                st.session_state.setdefault(k_title, old_stem)
                st.session_state.setdefault(k_year, int(meta["ano"] or 2025))
                st.session_state.setdefault(k_text, texto_atual or "")
                situ_default = meta["situacao"] or ("Vigente" if (meta["em_vigor"] is None or meta["em_vigor"] == 1) else "Revogada")
                st.session_state.setdefault(k_situ, situ_default)
                st.session_state.setdefault(k_just, meta["justificativa_situacao"] or "")
                st.session_state.setdefault(k_year_txt, str(st.session_state[k_year]))  # inicializa texto do ano

                # --- Form dinâmico (fora de st.form) ---
                st.markdown("<div class='cfg-form'>", unsafe_allow_html=True)

                st.text_input("Título da nota (sem extensão)", key=k_title)

                # Ano como texto (sem setas) usando key nova para evitar conflito de tipo
                st.text_input("Ano", key=k_year_txt)

                st.selectbox(
                    "Situação",
                    ["Vigente", "Parcialmente revogada", "Revogada"],
                    key=k_situ
                )

                # Campo condicional aparece imediatamente ao mudar a situação
                situ_now = st.session_state[k_situ]
                if situ_now == "Parcialmente revogada":
                    st.text_area("Observação (parcialmente revogada)", key=k_just, height=100)
                elif situ_now == "Revogada":
                    st.text_area("Observação (revogada)", key=k_just, height=100)
                else:
                    st.session_state[k_just] = st.session_state.get(k_just, "")

                st.text_area("Texto da nota (conteúdo pesquisável)", key=k_text, height=300)

                c1, c2 = st.columns([1,1])
                with c1:
                    save = st.button("💾 Salvar alterações", key=f"save_{sha}", type="primary")
                with c2:
                    close = st.button("❌ Fechar", key=f"close_{sha}")

                st.markdown("</div>", unsafe_allow_html=True)
                # --- fim da cfg-form ---

                if close:
                    st.session_state["open_card_sha"] = None
                    st.rerun()

                if save:
                    # valida ano (4 dígitos entre 1900-2100)
                    year_str = (st.session_state.get(k_year_txt) or "").strip()
                    if not (year_str.isdigit() and len(year_str) == 4 and 1900 <= int(year_str) <= 2100):
                        st.error("Informe um ano válido (4 dígitos entre 1900 e 2100).")
                    else:
                        year_int = int(year_str)
                        st.session_state[k_year] = year_int  # mantém estado interno coerente

                        # Lê valores do estado e garante que não há extensão digitada no título
                        clean_input = _strip_known_ext_from_input(st.session_state[k_title])
                        title_stem = _sanitize_filename(clean_input).strip()
                        if not title_stem:
                            st.error("Informe um título válido (sem extensão).")
                        else:
                            # salva texto + snippet
                            salvar_texto(sha, st.session_state[k_text] or "")
                            # salva metadados + renomeia arquivo (usando a EXT atual)
                            _ = salvar_metadados(
                                sha=sha,
                                titulo_stem=title_stem,
                                ano=year_int,
                                situacao=st.session_state[k_situ],
                                justificativa=st.session_state.get(k_just) or None,
                            )
                            st.success("Alterações salvas com sucesso.")
                            # mantém a busca e reabre este card
                            st.session_state["open_card_sha"] = sha
                            st.rerun()
else:
    if st.session_state["search_q"]:
        st.info("Nenhuma nota encontrada para os termos informados.")
