import streamlit as st
import pandas as pd
import utils
from datetime import datetime, timedelta
import altair as alt

utils.configurar_pagina()
st.title("💰 Gestão de Vendas")

df_emp, df_vendas, df_pontos = utils.carregar_dados_totais()

if df_pontos.empty:
    st.error("Erro: Tabela de Pontuação não carregada. Verifique o nome da aba no Sheets.")
    st.stop()

# --- TRATAMENTO DOS DADOS (USANDO AS FUNÇÕES DO UTILS) ---
df_pontos.columns = df_pontos.columns.str.strip()
c_val = next(c for c in df_pontos.columns if 'valor' in c.lower())
c_pts = next(c for c in df_pontos.columns if 'ponto' in c.lower())
c_tipo = next(c for c in df_pontos.columns if 'tipo' in c.lower())
c_prod = next(c for c in df_pontos.columns if 'produto' in c.lower())

# Aplica a correção de valores aqui
df_pontos[c_val] = df_pontos[c_val].apply(utils.converter_dinheiro_br)
df_pontos[c_pts] = df_pontos[c_pts].apply(utils.converter_pontos_br)

if not df_vendas.empty:
    df_vendas['Pontos'] = df_vendas['Pontos'].apply(utils.converter_pontos_br)
    df_vendas['Valor Total'] = df_vendas['Valor Total'].apply(utils.converter_dinheiro_br)
    if 'Data' in df_vendas.columns:
        df_vendas['Data_ISO'] = pd.to_datetime(df_vendas['Data'], dayfirst=True, errors='coerce')

tab_op, tab_an = st.tabs(["📝 Operacional", "📊 Análises & Radar"])

# --- ABA OPERACIONAL ---
with tab_op:
    with st.expander("➕ Adicionar Venda", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            cnpj_in = st.text_input("CNPJ Cliente").strip()
            cnpj_limpo = utils.limpar_cnpjs(cnpj_in)
            nome_cli = "Novo Cliente"
            if cnpj_in and not df_emp.empty:
                match = df_emp[df_emp['CNPJ'].astype(str).apply(utils.limpar_cnpjs) == cnpj_limpo]
                if not match.empty:
                    nome_cli = match.iloc[0]['Razão Social']
                    st.success(f"Cliente: {nome_cli}")
            canal = st.selectbox("Canal", ["Indicação", "Prospecção", "Base", "WhatsApp"])
        
        with c2:
            tipo = st.selectbox("Tipo", sorted(df_pontos[c_tipo].unique()))
            prods = df_pontos[df_pontos[c_tipo] == tipo][c_prod].tolist()
            prod = st.selectbox("Produto", prods)
            qtd = st.number_input("Qtd", 1)

        try:
            item = df_pontos[(df_pontos[c_tipo] == tipo) & (df_pontos[c_prod] == prod)].iloc[0]
            tot_val = item[c_val] * qtd
            tot_pts = item[c_pts] * qtd
            
            # Formatação Visual
            v_show = f"{tot_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            p_show = f"{tot_pts:.1f}".replace('.', ',')
            st.info(f"Prévia: R$ {v_show} | {p_show} Pts")
            
            if st.button("Salvar Venda", type="primary"):
                nova = {
                    'Data': data.strftime("%d/%m/%Y"),
                    'Mês': data.strftime("%B").capitalize(),
                    'CNPJ': utils.aplicar_mascara_cnpj(cnpj_limpo),
                    'Razão Social': nome_cli,
                    'Tipo Venda': tipo,
                    'Produto': prod,
                    'Qtd': qtd,
                    'Valor Total': f"{tot_val:.2f}".replace('.', ','),
                    'Pontos': f"{tot_pts:.1f}".replace('.', ','),
                    'Canal': canal,
                    'Status': "Tramitando"
                }
                utils.enviar_dados(utils.NOME_ABA_VENDAS, pd.DataFrame([nova])[utils.COLUNAS_VENDAS])
                st.success("Salvo!")
                st.rerun()
        except: pass

    if not df_vendas.empty:
        st.write("---")
        df_edit = st.data_editor(
            df_vendas, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Valor Total": st.column_config.NumberColumn(format="R$ %.2f"),
                "Pontos": st.column_config.NumberColumn(format="%.1f"),
                "Data": st.column_config.TextColumn()
            }
        )
        if st.button("💾 Salvar Edições Tabela"):
            df_save = df_edit.copy()
            df_save['Valor Total'] = df_save['Valor Total'].apply(lambda x: f"{float(x):.2f}".replace('.', ','))
            df_save['Pontos'] = df_save['Pontos'].apply(lambda x: f"{float(x):.1f}".replace('.', ','))
            if 'Data_ISO' in df_save.columns: df_save = df_save.drop(columns=['Data_ISO'])
            
            utils.atualizar_tabela_full(utils.NOME_ABA_VENDAS, df_save[utils.COLUNAS_VENDAS])
            st.success("Atualizado!")

# --- ABA RADAR ---
with tab_an:
    st.subheader("📡 Radar de Renovação")
    if not df_vendas.empty and 'Data_ISO' in df_vendas.columns:
        df_radar = df_vendas.copy()
        df_radar['Vencimento'] = df_radar['Data_ISO'] + timedelta(days=730)
        df_radar['Dias Restantes'] = (df_radar['Vencimento'] - datetime.now()).dt.days
        
        df_crit = df_radar[(df_radar['Dias Restantes'] > 0) & (df_radar['Dias Restantes'] <= 90)]
        
        if not df_crit.empty:
            st.dataframe(df_crit[['Razão Social', 'Vencimento', 'Dias Restantes']].sort_values('Dias Restantes'))
        else:
            st.info("Nenhum contrato vencendo em breve.")