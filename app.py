# app.py
import base64
from pathlib import Path

import streamlit as st

# Componentes que você já usa no projeto
from core.ui import hero, section
from core.sidebar import render_sidebar

# ---------------------------------
# Configuração base
# ---------------------------------
st.set_page_config(page_title="Notas Técnicas — INSS", page_icon="📁", layout="wide")

# Sidebar padrão do projeto
with st.sidebar:
    render_sidebar()

# ---------------------------------
# Caminhos e utilitários de estilo
# ---------------------------------
ROOT = Path(__file__).resolve().parent
STYLES_PATH = ROOT / "styles" / "style.css"
ASSETS_PATH = ROOT / "assets"

def _file_to_b64(path: Path) -> str:
    try:
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception:
        pass
    return ""

def _load_css(path: Path = STYLES_PATH):
    """Carrega o CSS global do projeto (styles/style.css)."""
    try:
        if path.exists():
            css = path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Falha ao carregar CSS: {e}")

def _get_logo_b64() -> tuple[str, str]:
    """Tenta logo.svg; se não houver, usa inss_logo.png. Retorna (b64, mime)."""
    svg_b64 = _file_to_b64(ASSETS_PATH / "logo.svg")
    if svg_b64:
        return svg_b64, "image/svg+xml"
    png_b64 = _file_to_b64(ASSETS_PATH / "inss_logo.png")
    if png_b64:
        return png_b64, "image/png"
    return "", ""

def _inject_header_with_logo(title_text: str = "REPOSITÓRIO DE NOTAS TÉCNICAS DO INSS"):
    """
    Injeta logo à esquerda e título centralizado no header,
    usando as mesmas variáveis definidas no style.css.
    """
    try:
        logo_b64, logo_mime = _get_logo_b64()
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

# Carrega o CSS global e injeta header como na página de Pesquisa
_load_css()
_inject_header_with_logo()

# ---------------------------------
# Conteúdo da home
# ---------------------------------
hero("📁 Notas Técnicas — INSS")
st.caption("Pesquise notas na base pública")

# Atalho coerente com as outras páginas
st.page_link("pages/1_🔎_Pesquisa.py", label="🔎 Começar")

# Aviso importante (mesmo bloco usado na Pesquisa)
with st.container(border=True):
    st.markdown("### ⚠️ Aviso Importante – Repositório de Notas Técnicas DILAG")
    st.markdown(
        "Este repositório reúne todas as Notas Técnicas já emitidas pela DILAG, "
        "independentemente de o entendimento nelas expresso permanecer ou não vigente.\n\n"
        "Ressalta-se que as Notas Técnicas não devem ser utilizadas como fundamento exclusivo "
        "para a tomada de decisões. O valor do material está nos fundamentos e interpretações "
        "contidos nos documentos, sendo indispensável verificar previamente a vigência e a "
        "atualidade dos normativos e dispositivos legais citados.\n\n"
        "A utilização das informações aqui disponíveis sem essa verificação pode resultar em "
        "decisões baseadas em entendimentos ultrapassados ou revogados."
    )

# (Opcional) Você pode adicionar outras seções abaixo, no mesmo estilo
# section("Outra seção")
