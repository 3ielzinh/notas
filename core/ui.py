import streamlit as st

def hero(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.caption(subtitle)

def section(title: str):
    st.subheader(title)

def section(title: str, subtitle: str = ""):
    import streamlit as st
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)
