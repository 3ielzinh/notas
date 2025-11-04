# pages/4_🧾_Gerenciar_Termos.py
import streamlit as st
import pandas as pd

from core.sidebar import render_sidebar
from core.ui import hero, section
from core.db import (
    import_terms_from_dataframe,
    get_terms_df,
    update_terms_from_editor,
    delete_terms,
)

st.set_page_config(page_title="Gerenciar Termos (Admin)", page_icon="🧾", layout="wide")

with st.sidebar:
    render_sidebar()

hero("🧾 Gerenciar Termos", "Administre os termos utilizados na anonimização")

# =========================
# 1) Importar/atualizar planilha de termos (SALVA NO BANCO)
# =========================
section("📥 Importar/Atualizar Planilha de Termos")

st.markdown(
    """
    **Formato aceito**:
    - **Formato longo**: colunas `categoria` e `termo`; ou  
    - **Formato largo**: cada **coluna** é uma categoria e as **linhas** contêm os termos.

    Arquivos aceitos: **.xlsx**, **.xls** ou **.csv**.
    """
)

up = st.file_uploader(
    "Envie a planilha de termos",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=False,
    key="upload_termos"
)

if up is not None:
    try:
        if up.name.lower().endswith(".csv"):
            df_up = pd.read_csv(up, dtype=str, sep=";")  # 👈 aqui está o ajuste
        else:
            df_up = pd.read_excel(up, dtype=str)
    except Exception as e:
        df_up = None
        st.error(f"Falha ao ler a planilha: {e}")


    if df_up is not None:
        st.caption("Prévia dos dados lidos:")
        st.dataframe(df_up.head(20), use_container_width=True)

        if st.button("⏬ Importar termos para o banco", type="primary", use_container_width=False):
            try:
                inserted, touched = import_terms_from_dataframe(df_up)
                st.success(f"Importação concluída! Inseridos: {inserted} | Atualizados/Ignorados: {touched}")
            except Exception as e:
                st.error(f"Ocorreu um erro ao gravar no banco: {e}")

# =========================
# 2) Editar/ativar/desativar/excluir termos (DIRETO DO BANCO)
# =========================
section("📋 Termos cadastrados")
st.caption("Os termos abaixo são usados para sanitizar dados dos PDFs durante a importação.")

df = get_terms_df(only_enabled=False)

if df.empty:
    st.warning("Nenhum termo cadastrado. Faça o upload da planilha acima.")
else:
    show_cols = ["id", "category", "term", "enabled"]
    view = df[show_cols].copy()
    view["enabled"] = view["enabled"].astype(int)

    edited = st.data_editor(
        view,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "category": st.column_config.TextColumn("Categoria"),
            "term": st.column_config.TextColumn("Termo"),
            "enabled": st.column_config.CheckboxColumn("Ativo (1=sim)")
        }
    )

    col1, col2, col3 = st.columns([1,1,2])

    with col1:
        if st.button("💾 Salvar alterações", type="primary"):
            try:
                changed = update_terms_from_editor(edited)
                st.success(f"Alterações salvas! Registros afetados: {changed}")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    with col2:
        ids_to_delete = st.multiselect("Selecionar IDs para excluir", edited["id"].tolist())
        if st.button("🗑️ Excluir selecionados"):
            if not ids_to_delete:
                st.info("Nenhum ID selecionado.")
            else:
                try:
                    removed = delete_terms(ids_to_delete)
                    st.success(f"Exclusões concluídas! Registros removidos: {removed}")
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

    with col3:
        st.info("Dica: use 'enabled=0' para desativar temporariamente sem excluir o termo.")
