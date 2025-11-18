# core/sidebar.py
import streamlit as st
import secrets

from core.state import NAME, USER_ROLES, AUTH_STATUS, USERNAME, DEFAULT_ROLES
from core.auth import _load_auth_config, _build_authenticator

# -----------------------------
# Helpers de sessão e cookies
# -----------------------------
def _purge_auth_cookies(cfg: dict):
    """Remove cookies relacionados à autenticação e zera estados voláteis."""
    try:
        import extra_streamlit_components as stx
        # Use uma key diferente de 'init' para evitar colisão com a lib
        cm = stx.CookieManager(key="cm_purge")
        base = cfg["cookie"]["name"]
        allc = cm.get_all() or {}
        for k in list(allc.keys()):
            # deleta o cookie base e possíveis variações da lib
            if k == base or base in k or k in ("name", "username", "authentication_status"):
                cm.delete(k)
    except Exception:
        pass

    # Zera estados que podem ter sido restaurados por cookie
    st.session_state["authentication_status"] = None
    st.session_state["username"] = None
    st.session_state["name"] = None
    st.session_state[AUTH_STATUS] = None
    st.session_state[USERNAME] = None
    st.session_state[NAME] = None


def _styled_logout(cfg: dict):
    """Apaga cookies + limpa sessão e recarrega a página."""
    try:
        import extra_streamlit_components as stx
        cm = stx.CookieManager(key="cm_logout")
        base = cfg["cookie"]["name"]
        allc = cm.get_all() or {}
        for k in list(allc.keys()):
            if k == base or base in k or k in ("name", "username", "authentication_status"):
                cm.delete(k)
    except Exception:
        pass

    # Limpa chaves nossas e volta perfil padrão
    for k in ["authentication_status", "username", "name", AUTH_STATUS, USERNAME, NAME, USER_ROLES]:
        if k in st.session_state:
            del st.session_state[k]

    st.session_state["show_login_form"] = False
    st.session_state[USER_ROLES] = DEFAULT_ROLES.copy()
    st.rerun()


# -----------------------------
# Sidebar
# -----------------------------
def render_sidebar():
    """Sidebar com:
        1) Navegação (Pesquisa sempre; Importação/Configuração/Admin se logado e com permissão)
        2) Acesso (Entrar/Sair) sem auto-login da sessão anterior e sem chaves duplicadas
    """
    # Perfil padrão VISUALIZAR para visitantes
    if USER_ROLES not in st.session_state:
        st.session_state[USER_ROLES] = DEFAULT_ROLES.copy()

    roles = st.session_state.get(USER_ROLES, DEFAULT_ROLES)
    auth_status = st.session_state.get(AUTH_STATUS, st.session_state.get("authentication_status"))
    name = st.session_state.get(NAME, st.session_state.get("name"))

    # --------------------------------
    # Navegação controlada
    # --------------------------------
    st.header("Menu de Navegação")
    st.page_link("pages/1_🔎_Pesquisa.py", label="Pesquisa", icon="🔎")

    if auth_status:
        st.page_link("pages/2_📥_Importacao.py", label="Importação", icon="📥")
        st.page_link("pages/3_🛠️_Configuracao_Nota.py", label="Configuração da Nota", icon="🛠️")
        # Página para usuários logados
        st.page_link("pages/6_📖_Guia.py", label="Guia", icon="📖")
    else:
        # Página para visitantes não logados
        st.page_link("pages/5_❓_Ajuda.py", label="Ajuda", icon="❓")


    st.divider()

    # --------------------------------
    # Acesso (Login / Logout)
    # --------------------------------
    # st.header("🔒 Acesso")

    # Estado auxiliar do formulário
    if "show_login_form" not in st.session_state:
        st.session_state.show_login_form = False

    # LOGADO
    if auth_status:
        st.success(f"{name}")
        st.caption("Perfis: " + ", ".join(roles))

        # Botão SAIR (100% largura) — limpeza robusta
        cfg_current = _load_auth_config()
        if st.button("Sair", key="btn_logout_full", use_container_width=True):
            _styled_logout(cfg_current)
        return  # encerra aqui para não renderizar login

    # NÃO LOGADO
    # Botão ENTRAR (abre o formulário)
    if st.button("Entrar", key="btn_open_login", use_container_width=True):
        st.session_state.show_login_form = True

    if st.session_state.show_login_form:
        # Carrega config e PURGA cookies antigos ANTES de abrir o form
        cfg = _load_auth_config()
        _purge_auth_cookies(cfg)

        # Chave efêmera para a assinatura do cookie nesta tentativa
        # (invalida cookies anteriores da mesma 'name')
        if "auth_dynamic_key" not in st.session_state:
            st.session_state["auth_dynamic_key"] = secrets.token_urlsafe(16)

        cfg = dict(cfg)  # cópia rasa
        cfg["cookie"] = dict(cfg["cookie"])
        cfg["cookie"]["key"] = f'{cfg["cookie"]["key"]}::{st.session_state["auth_dynamic_key"]}'

        # Cria o authenticator apenas agora (evita CookieManager duplicado)
        auth = _build_authenticator(cfg)

        # Renderiza formulário de login na sidebar
        auth.login(
            location="sidebar",
            fields={"Form name": "Entrar"},
            key="login_sidebar",
        )

        # Sincroniza estado pós-submit
        st.session_state[AUTH_STATUS] = st.session_state.get("authentication_status")
        st.session_state[USERNAME] = st.session_state.get("username")
        st.session_state[NAME] = st.session_state.get("name")

        if st.session_state.get(AUTH_STATUS) is True:
            # Define roles a partir do YAML real (sem chave efêmera)
            cfg_users = _load_auth_config()
            user = st.session_state.get(USERNAME)
            roles_cfg = cfg_users["credentials"]["usernames"].get(user, {}).get("roles", DEFAULT_ROLES)
            st.session_state[USER_ROLES] = roles_cfg

            # Fecha form e reseta chave efêmera
            st.session_state.show_login_form = False
            if "auth_dynamic_key" in st.session_state:
                del st.session_state["auth_dynamic_key"]

            st.success(f"Bem-vindo, {st.session_state.get(NAME)}!")
            st.rerun()

        elif st.session_state.get(AUTH_STATUS) is False:
            st.error("Usuário ou senha incorretos.")
            # Mantém formulário aberto para nova tentativa

        else:
            st.info("Informe usuário e senha para continuar.")

        # Botão FECHAR (sem logar) — recolhe o formulário
        if st.button("Fechar", key="btn_close_login", use_container_width=True):
            st.session_state.show_login_form = False
            # Garante que não restem cookies/estados residuais
            _purge_auth_cookies(_load_auth_config())
            if "auth_dynamic_key" in st.session_state:
                del st.session_state["auth_dynamic_key"]
            st.rerun()