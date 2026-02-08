import streamlit as st
import utils

# Configuração Global
utils.configurar_pagina()

st.title("⚡ Scabora Flow")

st.markdown("""
### Sistema Operacional de Vendas

Bem-vindo, Felipe. Selecione um módulo no menu lateral para começar:

* **🏢 Cadastro:** Enriquecimento de Leads e envio para base.
* **👥 Extrator QSA:** Descoberta de sócios e decisores.
* **💰 Vendas:** Lançamento de contratos e radar de renovação.
* **📧 Marketing:** Disparos de e-mail e WhatsApp.

---
""")

col_kpi1, col_kpi2 = st.columns(2)
with col_kpi1:
    st.info("💡 **Dica do Dia:** Comece o dia verificando o **Radar de Renovação** na aba de Vendas.")
with col_kpi2:
    if st.button("🔄 Recarregar Sistema (Limpar Cache)"):
        st.cache_data.clear()
        st.success("Sistema atualizado!")
        st.rerun()