import streamlit as st
import pandas as pd
import utils
import time

utils.configurar_pagina()
st.title("🏢 Cadastro de Empresas")

c_esp1, c_cent, c_esp2 = st.columns([1, 2, 1])
with c_cent:
    with st.container(border=True):
        arquivo_emp = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'], key="emp")
        
        if arquivo_emp:
            df_bruto = pd.read_csv(arquivo_emp, dtype=str) if arquivo_emp.name.endswith('.csv') else pd.read_excel(arquivo_emp, dtype=str)
            df_final = pd.DataFrame(columns=utils.COLUNAS_EMPRESAS)
            cols = df_bruto.columns.str.lower()
            
            col_razao = next((c for c in cols if 'razao' in c or 'empresa' in c), None)
            col_cnpj = next((c for c in cols if 'cnpj' in c), None)
            col_tel = next((c for c in cols if 'tel' in c or 'cel' in c), None)
            col_mail = next((c for c in cols if 'mail' in c), None)
            col_nome = next((c for c in cols if 'nome' in c), None)
            
            if col_razao and col_cnpj:
                df_final['Razão Social'] = df_bruto.iloc[:, cols.get_loc(col_razao)].str.title()
                df_final['CNPJ_NUM'] = df_bruto.iloc[:, cols.get_loc(col_cnpj)].apply(utils.limpar_cnpjs)
                if col_tel: df_final['Telefone'] = df_bruto.iloc[:, cols.get_loc(col_tel)].fillna('').astype(str).apply(utils.limpar_tels)
                if col_mail: df_final['E-mail'] = df_bruto.iloc[:, cols.get_loc(col_mail)].fillna('').astype(str).apply(utils.limpar_emails)
                if col_nome: df_final['Nome do Contato'] = df_bruto.iloc[:, cols.get_loc(col_nome)].str.title()
                
                st.info(f"{len(df_final)} empresas identificadas.")
                
                if st.button("🚀 Enriquecer e Enviar"):
                    df_emp_atual, _, _ = utils.carregar_dados_totais()
                    cnpjs_existentes = []
                    if not df_emp_atual.empty:
                        cnpjs_existentes = df_emp_atual['CNPJ'].apply(utils.limpar_cnpjs).tolist()
                    
                    df_novo = df_final[~df_final['CNPJ_NUM'].isin(cnpjs_existentes)].copy()
                    
                    if not df_novo.empty:
                        bar = st.progress(0)
                        ramos = []
                        for i, row in enumerate(df_novo.itertuples()):
                            dados = utils.buscar_receita(row.CNPJ_NUM)
                            ramos.append(dados['cnae_fiscal_descricao'].title() if dados else "")
                            bar.progress((i+1)/len(df_novo))
                            time.sleep(0.2)
                        
                        df_novo['Segmento/Ramo'] = ramos
                        df_novo['CNPJ'] = df_novo['CNPJ_NUM'].apply(utils.aplicar_mascara_cnpj)
                        utils.enviar_dados("Empresas", df_novo.drop(columns=['CNPJ_NUM']).fillna(''))
                        st.success(f"Cadastro Realizado! {len(df_novo)} novas empresas.")
                    else:
                        st.warning("Todas as empresas já existem.")
            else:
                st.error("Colunas 'Razão Social' ou 'CNPJ' não encontradas.")