import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth
from .state import AUTH_STATUS, USERNAME, NAME, USER_ROLES

@st.cache_resource
def load_authenticator(config_path: str = "config/auth_config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Permite sobrescrever a chave via env em produção
    env_key = os.getenv("STREAMLIT_AUTH_KEY")
    if env_key:
        config["cookie"]["key"] = env_key

    authenticator = stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"],
        preauthorized=config.get("preauthorized", {})
    )
    return authenticator, config

def do_login_ui(title: str = "🔐 Login"):
    authenticator, config = load_authenticator()
    name, authentication_status, username = authenticator.login(title, "main")

    st.session_state[AUTH_STATUS] = authentication_status
    st.session_state[USERNAME] = username
    st.session_state[NAME] = name

    if authentication_status:
        roles = config["credentials"]["usernames"][username].get("roles", [])
        st.session_state[USER_ROLES] = roles

    return authenticator
