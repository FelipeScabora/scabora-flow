import streamlit as st
import pandas as pd
import gspread
import requests
import re
import os
from datetime import datetime

# --- CONFIGURAÇÕES GERAIS ---
LINK_PLANILHA = "https://docs.google.com/spreadsheets/d/15NKid51OjP0GT0TG99UNMcTLEgfgNmSrQ2nNt6KFkk4/edit?gid=408922613#gid=408922613"
NOME_ABA_VENDAS = "Vendas & Renovações"
NOME_ABA_PONTOS = "Tabela de Pontuação"

COLUNAS_EMPRESAS = ['Razão Social', 'Nome Fantasia', 'CNPJ', 'Segmento/Ramo', 'Nome do Contato', 'E-mail', 'Telefone', 'Status']
COLUNAS_CONTATOS = ['CNPJ', 'Razão Social', 'Nome_contato', 'Segmento', 'Cargo_funcao', 'Telefone', 'E-mail', 'Perfil', 'Status']
COLUNAS_VENDAS   = ['Data', 'Mês', 'CNPJ', 'Razão Social', 'Tipo Venda', 'Produto', 'Qtd', 'Valor Total', 'Pontos', 'Canal', 'Status']

# --- VISUAL E CSS ---
def configurar_pagina():
    st.set_page_config(page_title="Scabora Flow", page_icon="⚡", layout="wide")
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
            h1 { text-align: center; margin-bottom: 2rem; color: #111827; }
            .stTabs [data-baseweb="tab-list"] { justify-content: center; }
            div[data-testid="metric-container"] {
                background-color: #ffffff; border: 1px solid #eef2f6; padding: 15px; border-radius: 12px; text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            div.stButton > button:first-child {
                background-color: #111827; color: white; border-radius: 8px; border: none; padding: 12px 24px; width: 100%; font-weight: 600;
            }
            div.stButton > button:hover { background-color: #374151; }
        </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SEGURA ---
def conectar_sheets_no_cache():
    try:
        # Verifica se existe arquivo local, senão busca nos segredos da nuvem
        if os.path.exists('credenciais.json'):
            conta = gspread.service_account(filename='credenciais.json')
        else:
            conta = gspread.service_account_from_dict(st.secrets["gspread_credentials"])
        return conta.open_by_url(LINK_PLANILHA)
    except Exception as e:
        st.error(f"❌ Erro de Conexão: {e}")
        return None

# --- CARREGAMENTO DE DADOS (CACHEADO) ---
@st.cache_data(ttl=300)
def carregar_dados_totais():
    planilha = conectar_sheets_no_cache()
    if not planilha: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try: df_emp = pd.DataFrame(planilha.worksheet("Empresas").get_all_records())
    except: df_emp = pd.DataFrame()

    try:
        try: df_vendas = pd.DataFrame(planilha.worksheet(NOME_ABA_VENDAS).get_all_records())
        except: df_vendas = pd.DataFrame(columns=COLUNAS_VENDAS)
    except: df_vendas = pd.DataFrame()

    try: df_pontos = pd.DataFrame(planilha.worksheet(NOME_ABA_PONTOS).get_all_records())
    except: df_pontos = pd.DataFrame()
        
    return df_emp, df_vendas, df_pontos

# --- CORREÇÃO FINANCEIRA (A SOLUÇÃO NUCLEAR) ---
def converter_dinheiro_br(valor):
    """Corrige erro de 99.99 virar 9999"""
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v_str = str(valor).strip().replace('R$', '').strip()
    try:
        if ',' in v_str: v_str = v_str.replace('.', '').replace(',', '.')
        val = float(v_str)
        # SE O VALOR FOR ABSURDO (> 3000), DIVIDE POR 100
        if val > 3000: val = val / 100
        return val
    except: return 0.0

def converter_pontos_br(valor):
    """Corrige erro de pontuação"""
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v_str = str(valor).strip().replace(',', '.')
    try:
        val = float(v_str)
        # SE O VALOR FOR ABSURDO (> 20), DIVIDE POR 10
        if val > 20: val = val / 10
        return val
    except: return 0.0

# --- LIMPEZA DE DADOS ---
def limpar_cnpjs(cnpj):
    c = str(cnpj).strip()
    if c.endswith('.0'): c = c[:-2]
    return re.sub(r'\D', '', c).zfill(14)

def aplicar_mascara_cnpj(c):
    c = str(c)
    if len(c) == 14: return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"
    return c

def limpar_emails(e):
    e = str(e).strip().lower()
    validos = [p.strip() for p in re.split(r'[ /;,]', e) if '@' in p and '.' in p]
    return " / ".join(list(dict.fromkeys(validos)))

def limpar_tels(t):
    return re.sub(r'\D', '', str(t))

def buscar_receita(cnpj):
    c = limpar_cnpjs(cnpj)
    if len(c) != 14: return None
    try:
        res = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{c}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        return res.json() if res.status_code == 200 else None
    except: return None

# --- ESCRITA NO SHEETS ---
def enviar_dados(aba_nome, df):
    planilha = conectar_sheets_no_cache()
    if planilha:
        aba = planilha.worksheet(aba_nome)
        if not aba.get_all_values(): aba.append_row(df.columns.tolist())
        aba.append_rows(df.values.tolist())
        st.cache_data.clear()

def atualizar_tabela_full(aba_nome, df_full):
    planilha = conectar_sheets_no_cache()
    if planilha:
        aba = planilha.worksheet(aba_nome)
        aba.clear()
        dados = [df_full.columns.tolist()] + df_full.astype(str).values.tolist()
        aba.update('A1', dados)
        st.cache_data.clear()