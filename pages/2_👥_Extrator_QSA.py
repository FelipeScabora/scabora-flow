import streamlit as st
import pandas as pd
import utils
import time

utils.configurar_pagina()
st.title("👥 Extrator de Sócios (QSA)")

c_esp1, c_cent, c_esp2 = st.columns([1, 2, 1])
with c_cent:
    with st.container(border=True):
        arquivo_cont = st.file_uploader("Upload Excel/CSV com CNPJ", type=['xlsx', 'csv'], key="cont")
        
        if arquivo_cont:
            if st.button("🔍 Extrair Sócios"):
                df_bruto = pd.read_csv(arquivo_cont, dtype=str) if arquivo_cont.name.endswith('.csv') else pd.read_excel(arquivo_cont, dtype=str)
                cols = df_bruto.columns.str.lower()
                col_cnpj = next((c for c in cols if 'cnpj' in c), None)
                
                if col_cnpj:
                    lista = []
                    cnpjs = df_bruto.iloc[:, cols.get_loc(col_cnpj)].apply(utils.limpar_cnpjs).unique()
                    bar = st.progress(0)
                    
                    for i, c in enumerate(cnpjs):
                        dados = utils.buscar_receita(c)
                        time.sleep(0.2)
                        if dados and 'qsa' in dados:
                            for s in dados['qsa']:
                                lista.append({
                                    'CNPJ': utils.aplicar_mascara_cnpj(c),
                                    'Razão Social': dados.get('razao_social', '').title(),
                                    'Nome_contato': s.get('nome_socio', '').title(),
                                    'Cargo_funcao': s.get('qualificacao_socio', 'Sócio'),
                                    'Status': ''
                                })
                        bar.progress((i+1)/len(cnpjs))
                    
                    if lista:
                        utils.enviar_dados("Contatos", pd.DataFrame(lista))
                        st.success(f"{len(lista)} sócios extraídos!")
                else:
                    st.error("Coluna CNPJ não encontrada.")