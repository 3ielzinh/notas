# pages/4_📖_Guia.py
import streamlit as st
import base64
from pathlib import Path
from core.sidebar import render_sidebar
from datetime import datetime

# ---------------------------------
# Configuração da página
# ---------------------------------
st.set_page_config(page_title="Guia do Administrador", page_icon="📖", layout="wide")

# ---------------------------------
# Renderização da Sidebar (Ordem correta: antes do header)
# ---------------------------------
with st.sidebar:
    render_sidebar()

# ---------------------------------
# Header e Estilos Globais (Estrutura Padrão Mantida)
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
    """Carrega o CSS global do projeto."""
    try:
        if path.exists():
            css = path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Falha ao carregar CSS: {e}")

def get_logo_b64() -> tuple[str, str]:
    """Obtém o logo do sistema."""
    svg_b64 = file_to_b64(ASSETS_PATH / "logo.svg")
    if svg_b64:
        return svg_b64, "image/svg+xml"
    png_b64 = file_to_b64(ASSETS_PATH / "inss_logo.png")
    if png_b64:
        return png_b64, "image/png"
    return "", ""

def inject_custom_header(
    title_text: str = "REPOSITÓRIO DE NOTAS TÉCNICAS - DILAG",
    subtitle_text: str = "Diretoria de Gestão de Pessoas - DGP"
):
    """Injeta o header customizado na página."""
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
            position: absolute; left: 0; right: 0; top: 50%;
            transform: translateY(-80%); text-align: center;
            font-weight: 800; font-size: 22px; color: var(--header-fg);
        }}
        [data-testid="stHeader"]::after {{
            content: "{subtitle_text}";
            position: absolute; left: 0; right: 0; top: 50%;
            text-align: center; font-weight: 400; font-size: 20px;
            color: rgba(255, 255, 255, 0.85);
        }}
    </style>
    """
    st.markdown(header_css, unsafe_allow_html=True)

# Carrega o CSS global e injeta o header customizado
load_css()
inject_custom_header()


# =====================================================================
# CONTEÚDO DA PÁGINA "GUIA DO ADMINISTRADOR"
# =====================================================================

# --- FUNÇÃO PARA FORMATAR DATA EM PORTUGUÊS ---
def format_date_pt_br(dt):
    """ Formata um objeto datetime para o formato 'dd de mês de aaaa' em português. """
    meses = (
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    )
    dia = dt.day
    mes = meses[dt.month - 1]
    ano = dt.year
    return f"{dia} de {mes} de {ano}"

# --- FUNÇÃO PARA APLICAR ESTILOS CUSTOMIZADOS ---
def aplicar_estilos_customizados():
    """ Injeta CSS para customizar a página. """
    st.markdown("""
        <style>
        p, li { font-size: 1.15rem !important; }
        button[data-baseweb="tab"]:hover { color: #0956A4 !important; border-bottom-color: #0956A4 !important; }
        button[data-baseweb="tab"][aria-selected="true"] { color: #0956A4 !important; font-weight: bold !important; border-bottom-color: #0956A4 !important; }
        div[data-testid="stExpander"] summary:hover { color: #0956A4 !important; }
        .custom-card { background-color: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #E0E0E0; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); transition: box-shadow 0.3s ease-in-out; margin-bottom: 1rem; }
        .custom-card:hover { box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.15); }
        </style>
    """, unsafe_allow_html=True)

# Aplica os estilos
aplicar_estilos_customizados()


# --- CABEÇALHO ---
st.title("🛠️ Guia do Administrador", anchor=False)
st.subheader("Manual de Gerenciamento de Notas Técnicas")

# --- USA A NOVA FUNÇÃO DE DATA ---
st.caption(f"Última atualização: {format_date_pt_br(datetime.now())}")
st.divider()

st.info("**Bem-vindo(a), Administrador(a).** Esta página detalha o processo para adicionar, anonimizar e catalogar novas Notas Técnicas no sistema, garantindo a qualidade e a integridade da nossa base de conhecimento.")


# --- FLUXO DE TRABALHO ---
st.header("📋 Fluxo de Trabalho: Adicionando uma Nova Nota")
st.markdown("O processo de cadastro é dividido em 4 etapas principais. Siga o guia abaixo.")

# --- ETAPA 1 ---
st.subheader("Etapa 1: Upload do Arquivo PDF")
st.markdown(
    "1.  Acesse a página de **Importação** na barra lateral.\n"
    "2.  Utilize o campo de upload para selecionar o arquivo da Nota Técnica em formato **PDF** do seu computador.\n"
    "3.  Aguarde o sistema processar o arquivo. Uma pré-visualização do texto extraído será exibida."
)


# --- ETAPA 2 ---
st.subheader("Etapa 2: Anonimização de Termos Sensíveis")
st.markdown(
    "A privacidade é fundamental. Nesta etapa, você irá revisar e censurar os dados sensíveis do documento."
)
st.markdown(
    """
    - **Sugestões Automáticas:** O sistema irá varrer o texto e sugerir a remoção de termos que constam na lista de exclusão principal (CPFs, nomes, etc.).
    - **Revisão Manual:** Revise o texto e as sugestões.
    - **Resultado:** Todos os termos censurados serão substituídos por uma tarja branca na versão final do texto.
    """
)


# --- ETAPA 3 ---
st.subheader("Etapa 3: Cadastro de Metadados")
st.markdown(
    "Metadados são as informações que catalogam a nota e permitem que ela seja encontrada corretamente. Preencha todos os campos com atenção:"
)
st.markdown(
    """
    - **Nome da Nota:** Um nome claro e conciso para o documento.
    - **Ano de Emissão:** O ano em que a Nota Técnica foi oficialmente emitida.
    - **Situação:** O status atual do entendimento da nota. As opções são:
        - **Vigente:** O entendimento é válido e atual. (Padrão para novas notas).
        - **Parcialmente Revogada:** Uma parte do conteúdo da nota foi substituída, mantendo-se vigente o restante. 
        - **Revogada:** O entendimento foi superado. Ao selecionar esta opção, um novo campo aparecerá.
    - **Resumo:** Um breve resumo da Nota Técnica para facilitar seu entendimento.
    """
)


# --- ETAPA 4 ---
st.subheader("Etapa 4: Salvar e Indexar")
st.markdown(
    "Após preencher todos os campos, clique em **Salvar Nota**. Ao fazer isso, o sistema irá:\n"
    "1.  Salvar o arquivo PDF original e sua versão em texto anonimizado.\n"
    "2.  Registrar todos os metadados no banco de dados.\n"
    "3.  **Indexar** o conteúdo para que a nota fique imediatamente disponível para busca por todos os usuários."
)

st.divider()

# --- FAQ ---
st.header("❔ Perguntas Frequentes de Administradores")

with st.expander("**O que acontece se eu fizer o upload de uma nota que já existe?**"):
    st.markdown(
        "O sistema é projetado para verificar a duplicidade de arquivos. Caso identifique um documento idêntico, ele irá alertá-lo(a) e impedir o novo cadastro, oferecendo a opção de visualizar ou editar a nota existente. (?)"
    )

with st.expander("**Posso editar os metadados ou o texto de uma nota depois de salva?**"):
    st.markdown(
        "..."
    )

with st.expander("**Como eu adiciono um novo termo à lista *permanente* de censura?**"):
    st.markdown(
        "A adição de novos termos à lista de anonimização global (que se aplica a todos os futuros uploads) é feita em uma área de configuração separada, geralmente chamada **'Gerenciar Termos'**. A anonimização manual durante o upload de uma nota aplica-se apenas àquele documento específico."
    )