# pages/4_❓_Ajuda.py
import streamlit as st
import base64
from pathlib import Path
from core.sidebar import render_sidebar
from datetime import datetime
import locale  # Importa o módulo de localização

# ---------------------------------
# Configuração da página
# ---------------------------------
st.set_page_config(page_title="Ajuda e Guia de Uso", page_icon="❓", layout="wide")

# ---------------------------------
# Renderização da Sidebar
# ---------------------------------
with st.sidebar:
    render_sidebar()

# ---------------------------------
# Header e Estilos Globais
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
    """Carrega o CSS global do projeto (styles/style.css) e o Font Awesome."""
    try:
        if path.exists():
            css = path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Falha ao carregar CSS: {e}")

    # 🔹 Importa a biblioteca de ícones Font Awesome
    st.markdown("""
        <link rel="stylesheet"
              href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        <style>
            i.fa-solid, i.fa-regular, i.fa-brands {
                margin-right: 6px;
                color: #0956A4;
            }
        </style>
    """, unsafe_allow_html=True)


def get_logo_b64() -> tuple[str, str]:
    """Tenta logo.svg; se não houver, usa inss_logo.png. Retorna (b64, mime)."""
    svg_b64 = file_to_b64(ASSETS_PATH / "logo.svg")
    if svg_b64:
        return svg_b64, "image/svg+xml"
    png_b64 = file_to_b64(ASSETS_PATH / "inss_logo.png")
    if png_b64:
        return png_b64, "image/png"
    return "", ""


def inject_custom_header(
    title_text: str = "REPOSITÓRIO DE NOTAS TÉCNICAS - DILAG",
    subtitle_text: str = "Diretoria de Gestão de Pessoas - DGP",
):
    """Injeta logo, título e subtítulo no header usando CSS."""
    logo_b64, logo_mime = get_logo_b64()

    header_css = f"""
    <style>
        [data-testid="stHeader"] {{
            background-image: url("data:{logo_mime};base64,{logo_b64}");
            background-repeat: no-repeat;
            background-size: 130px;
            background-position: calc(var(--toggle-safe) + 8px) center;
        }}
        [data-testid="stHeader"]::before {{
            content: "{title_text}";
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            transform: translateY(-80%);
            text-align: center;
            font-weight: 800;
            font-size: 22px;
            color: var(--header-fg);
        }}
        [data-testid="stHeader"]::after {{
            content: "{subtitle_text}";
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            text-align: center;
            font-weight: 400;
            font-size: 20px;
            color: rgba(255, 255, 255, 0.85);
        }}
    </style>
    """
    st.markdown(header_css, unsafe_allow_html=True)


# Carrega o CSS global e injeta o header customizado
load_css()
inject_custom_header()

# =====================================================================
# CONTEÚDO DA PÁGINA DE AJUDA (EMOJIS → ÍCONES)
# =====================================================================

def aplicar_estilos_customizados():
    """Injeta CSS para customizar a página com identidade visual."""
    st.markdown(
        """
        <style>
        p, li {
            font-size: 1.15rem !important;
        }
        button[data-baseweb="tab"]:hover {
            color: #0956A4 !important;
            border-bottom-color: #0956A4 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #0956A4 !important;
            font-weight: bold !important;
            border-bottom-color: #0956A4 !important;
        }
        div[data-testid="stExpander"] summary:hover {
            color: #0956A4 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


aplicar_estilos_customizados()

# --- CABEÇALHO ---
st.markdown('<h1><i class="fa-solid fa-circle-question"></i> Central de Ajuda</h1>', unsafe_allow_html=True)
st.subheader("Está com dificuldades para usar o sistema? Leia o tutorial abaixo!")

# --- DATA ---
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except locale.Error:
    pass

today_date = datetime.now().strftime("%d de %B de %Y").lower()
st.caption(f"Última atualização: {today_date}")

st.divider()

# --- ABAS ---
tab_quick, tab_details, tab_advanced, tab_glossary = st.tabs(
    [
        "**Guia Rápido**",
        "**Funcionalidades Detalhadas**",
        "**Dicas Avançadas**",
        "**Glossário**",
    ]
)

# --- ABA 1 ---
with tab_quick:
    st.markdown("Siga estes três passos simples para encontrar o que você precisa.")
    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("<h3><i class='fa-solid fa-keyboard'></i> Digite os Termos</h3>", unsafe_allow_html=True)
        st.markdown(
            "Use a barra de pesquisa na página **Pesquisa** para digitar palavras-chave, "
            "números de processo ou qualquer termo relevante. Pressione **Buscar**."
        )

    with col2:
        st.markdown("<h3><i class='fa-solid fa-list'></i> Analise os Resultados</h3>", unsafe_allow_html=True)
        st.markdown(
            "Navegue pela lista de resultados. Cada 'card' contém o **título**, o **ano**, a **situação** "
            "e um resumo com os termos <mark>destacados</mark>.",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown("<h3><i class='fa-solid fa-download'></i> Baixe ou Visualize</h3>", unsafe_allow_html=True)
        st.markdown(
            "Clique em **Baixar** para salvar o PDF original ou expanda a seção "
            "**Visualizar documento** para ler o conteúdo diretamente na tela."
        )

# --- ABA 2 ---
with tab_details:
    st.markdown("<h2><i class='fa-solid fa-magnifying-glass'></i> A Busca em Detalhes</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            - **Lógica "E" (AND):** Cada palavra é obrigatória.  
            - **Busca por Prefixo:** Encontra palavras que começam com o termo.  
            - **Sensibilidade a acentos:** `cálculo` ≠ `calculo`.  
            - **Não diferencia maiúsculas/minúsculas.**
            """
        )
    with col2:
        with st.container(border=True):
            st.caption("Exemplo da Lógica AND")
            st.markdown("`abono permanência 2024` → retorna documentos com **todas** as palavras da busca. ")

# --- ABA 3 ---
with tab_advanced:
    st.markdown("<h2><i class='fa-solid fa-brain'></i> Torne-se um Usuário Avançado</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        - **Combinando Filtros:** Use busca + filtros para afinar resultados.  
        - **Sem operadores de negação:** Não há suporte para `NÃO` ou `-`.  
        - **Sem busca exata:** Aspas (`"..."`) não são suportadas.  
        - **Relevância:** Termos mais frequentes aparecem primeiro.
        """
    )

# --- ABA 4 ---
with tab_glossary:
    st.markdown("<h2><i class='fa-solid fa-book-open'></i> Termos e Conceitos</h2>", unsafe_allow_html=True)
    st.markdown("**Nota Técnica:** Documento com parecer técnico ou jurídico fundamentado.")
    st.markdown("**Indexação:** Processo que cadastra textos para busca rápida.")
    st.markdown("**Snippet:** Trecho do texto exibido nos resultados da busca.")
    st.markdown("**Token `[REMOVIDO]`:** Marca que substitui dados sensíveis.")

st.divider()

# --- FAQ ---
st.markdown("<h2><i class='fa-solid fa-circle-question'></i> Perguntas Frequentes (FAQ)</h2>", unsafe_allow_html=True)

with st.expander("Os dados são atualizados em tempo real?"):
    st.markdown(
        "**Não.** A indexação é manual e periódica pela DILAG, podendo haver um pequeno intervalo entre publicação e atualização."
    )

with st.expander("Minha busca não retornou resultados. O que pode ter acontecido?"):
    st.markdown(
        """
        1. Termos muito restritivos — use menos palavras.  
        2. Erros de digitação.  
        3. Documento ainda não indexado.
        """
    )

with st.expander("Encontrei uma nota com erro. Como proceder?"):
    st.markdown(
        "Entre em contato com a equipe administradora, informando o nome do arquivo e a correção necessária."
    )

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("<h2><i class='fa-solid fa-triangle-exclamation'></i> Aviso de Validade</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            "Este é um acervo histórico. Sempre confirme a validade de uma Nota Técnica com a legislação vigente."
        )

with col2:
    st.markdown("<h2><i class='fa-solid fa-headset'></i> Suporte e Contato</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            """
            **Setor Responsável:** Divisão de Legislação Aplicada à Gestão de Pessoas - DILAG  
            **E-mail:** dilag@inss.gov.br
            """
        )
