import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth
from .state import AUTH_STATUS, USERNAME, NAME, USER_ROLES

# Cacheie apenas a LEITURA de arquivo (não cria widgets)
@st.cache_data
def _load_auth_config(config_path: str = "config/auth_config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Permite sobrescrever a chave do cookie via variável de ambiente em produção
    env_key = os.getenv("STREAMLIT_AUTH_KEY")
    if env_key:
        cfg["cookie"]["key"] = env_key
    return cfg

def _build_authenticator(config: dict) -> stauth.Authenticate:
    """
    NÃO cachear esta função!
    Ela cria internamente CookieManager (widget) via streamlit-authenticator.
    """
    return stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"],
        preauthorized=config.get("preauthorized", {})
    )

def do_login_ui(form_title: str = "🔐 Login", location: str = "main"):
    """
    Compatível com streamlit-authenticator >= 0.4.x.
    Chama o formulário de login e sincroniza st.session_state com nossas chaves canônicas.
    """
    config = _load_auth_config()
    authenticator = _build_authenticator(config)

    # v0.4.x: não retorna tupla; popula st.session_state
    authenticator.login(
        location=location,
        fields={"Form name": form_title},
        key="Login"  # previne conflitos em multipage
    )

    # Normaliza chaves
    st.session_state[AUTH_STATUS] = st.session_state.get("authentication_status")
    st.session_state[USERNAME] = st.session_state.get("username")
    st.session_state[NAME] = st.session_state.get("name")

    if st.session_state.get(AUTH_STATUS):
        user = st.session_state.get(USERNAME)
        roles = config["credentials"]["usernames"].get(user, {}).get("roles", [])
        st.session_state[USER_ROLES] = roles

    return authenticator
