import streamlit as st
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÃO VISUAL (CSS) ---
def carregar_css():
    st.markdown("""
    <style>
        .stApp {background-color: #0E1117;}
        div[data-testid="stExpander"] {
            border: 1px solid #2b313e;
            border-radius: 10px;
            background-color: #161b24;
        }
        .card-metric {
            background-color: #1f2937;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #ff4b4b;
            text-align: center;
        }
        h1, h2, h3 {font-family: 'Sans-serif'; font-weight: 700;}
        .highlight {color: #ff4b4b; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- MOCKUP DE DADOS (Simulando seu Utils/Google Sheets) ---
def get_google_sheet_names():
    # Aqui você usaria: gspread.open('NOME_PLANILHA').worksheets()
    return ["Base_Geral_Jan", "Base_Eventos_SP", "Base_Leads_Frio"]

def carregar_aba(nome_aba):
    # Simulação de dados vindos do Sheets
    data = {
        'CNPJ': ['111', '222', '333', '444'],
        'Empresa': ['Padaria A', 'Mecânica B', 'Tech C', 'Consultoria D'],
        'Email': ['padaria@teste.com', 'mecanica@teste.com', 'tech@teste.com', 'consult@teste.com'],
        'Produto_Atual': ['Móvel Vivo', 'Fixo Vivo', 'Nada', 'Móvel + Fixo'], # Coluna crucial
        'Ultimo_Contato': ['2023-01-01', '', '2023-12-01', '']
    }
    return pd.DataFrame(data)

# --- FUNÇÕES DE EMAIL ---
def enviar_email_real(conta, senha, para, assunto, corpo):
    # Lógica de envio encapsulada
    try:
        msg = MIMEMultipart()
        msg['From'] = conta
        msg['To'] = para
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(conta, senha)
        server.sendmail(conta, para, msg.as_string())
        server.quit()
        return True, "Enviado"
    except Exception as e:
        return False, str(e)

# --- PÁGINA PRINCIPAL ---
def main():
    st.set_page_config(page_title="Scabora Flow", layout="wide", page_icon="🚀")
    carregar_css()

    # --- SIDEBAR: CONFIGURAÇÕES GERAIS ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10856/10856864.png", width=50) # Logo Fictício
        st.title("⚙️ Configurações")
        
        st.markdown("### 📧 Gerenciar Remetentes")
        # Ideal: Usar st.secrets ou um JSON seguro. Aqui é visual.
        remetentes = st.data_editor(
            pd.DataFrame([
                {"Alias": "Principal", "Email": "felipe@dominio.com", "Senha": "***", "Ativo": True},
                {"Alias": "Comercial", "Email": "comercial@dominio.com", "Senha": "***", "Ativo": False},
            ]),
            num_rows="dynamic",
            key="sender_config"
        )
        
        st.divider()
        st.info("💡 Dica: Alterne os remetentes para evitar bloqueios de SPAM.")

    # --- CABEÇALHO ---
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.title("🚀 Central de Campanhas")
        st.markdown("Crie máquinas de vendas automatizadas e segmentadas.")
    with c_head2:
        st.metric("Disparos Hoje", "127", "12%")

    # --- WIZARD EM TABS (Para organizar o fluxo) ---
    tab1, tab2, tab3 = st.tabs(["1️⃣ Base & Inteligência", "2️⃣ Criação da Mensagem", "3️⃣ Disparo & Acompanhamento"])

    # --- TAB 1: DADOS ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📂 Origem dos Dados")
            abas_disponiveis = get_google_sheet_names()
            aba_selecionada = st.selectbox("Selecione a Aba do Google Sheets para importar:", abas_disponiveis)
            
            if st.button("🔄 Carregar/Atualizar Base"):
                with st.spinner("Conectando ao Google Sheets..."):
                    df = carregar_aba(aba_selecionada)
                    st.session_state['df_base'] = df
                    st.success(f"{len(df)} leads carregados!")

        with c2:
            st.subheader("🧠 Estratégia de Segmentação")
            # AQUI ESTÁ A LÓGICA QUE VOCÊ PEDIU
            tipo_filtro = st.radio("Quem vamos atacar hoje?", 
                                 ["Todos", 
                                  "Oportunidade Cruzada (Tem Móvel, oferecer Fixo)",
                                  "Oportunidade Cruzada (Tem Fixo, oferecer Móvel)",
                                  "Mar Aberto (Não tem nada)"])

        # Aplicação dos Filtros
        if 'df_base' in st.session_state:
            df_work = st.session_state['df_base'].copy()
            
            # Lógica simples baseada em strings, pode ser refinada
            if tipo_filtro == "Oportunidade Cruzada (Tem Móvel, oferecer Fixo)":
                df_work = df_work[df_work['Produto_Atual'].str.contains("Móvel") & ~df_work['Produto_Atual'].str.contains("Fixo")]
            elif tipo_filtro == "Oportunidade Cruzada (Tem Fixo, oferecer Móvel)":
                df_work = df_work[df_work['Produto_Atual'].str.contains("Fixo") & ~df_work['Produto_Atual'].str.contains("Móvel")]
            elif tipo_filtro == "Mar Aberto (Não tem nada)":
                df_work = df_work[df_work['Produto_Atual'] == "Nada"] # Ou string vazia
            
            # Filtro Anti-Spam (Exemplo: Já contatados recentemente)
            usar_blacklist = st.checkbox("🛡️ Excluir leads contatados recentemente (Anti-Chato)", value=True)
            if usar_blacklist:
                df_work = df_work[df_work['Ultimo_Contato'] == ""]

            st.session_state['df_final'] = df_work
            
            st.markdown(f"### 🎯 Leads Qualificados para Disparo: `{len(df_work)}`")
            st.dataframe(df_work, use_container_width=True, hide_index=True)

    # --- TAB 2: MENSAGEM ---
    with tab2:
        c_msg1, c_msg2 = st.columns([2, 1])
        
        with c_msg1:
            st.subheader("✍️ Copywriting")
            assunto = st.text_input("Assunto do E-mail", "Uma ideia para a {Empresa}")
            
            # Sugestão de Template baseada no filtro escolhido
            template_padrao = "Olá {Nome},\n\nVi que vocês já usam Vivo Móvel. Tenho uma condição especial para incluir a fixa..."
            corpo_email = st.text_area("Corpo do E-mail (Use {Empresa}, {Nome})", template_padrao, height=250)

        with c_msg2:
            st.subheader("🧪 Teste A/B Rápido")
            st.info("Envie um teste para você mesmo antes de disparar para a base.")
            email_teste = st.text_input("Seu e-mail de teste")
            if st.button("Enviar Teste"):
                st.toast("E-mail de teste enviado! (Simulação)")

    # --- TAB 3: DISPARO ---
    with tab3:
        st.subheader("🚀 Painel de Controle de Disparo")
        
        if 'df_final' not in st.session_state or st.session_state['df_final'].empty:
            st.warning("Selecione uma base na Aba 1 primeiro.")
        else:
            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            col_kpi1.metric("Total a Enviar", len(st.session_state['df_final']))
            sender_ativo = remetentes[remetentes['Ativo'] == True].iloc[0]['Email'] if not remetentes.empty else "Nenhum"
            col_kpi2.metric("Remetente Ativo", sender_ativo)
            col_kpi3.metric("Tempo Estimado", f"{len(st.session_state['df_final']) * 2} seg") # 2s de delay

            st.write("---")
            
            if st.button("🔥 INICIAR MÁQUINA DE VENDAS", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.container(height=200, border=True)
                
                # Loop de Envio
                df_envio = st.session_state['df_final']
                total = len(df_envio)
                
                sucessos = 0
                falhas = 0
                
                for i, row in enumerate(df_envio.itertuples()):
                    # Simulação de Envio
                    empresa = row.Empresa
                    email_destino = row.Email
                    
                    status_text.text(f"Enviando para: {empresa} ({i+1}/{total})...")
                    
                    # AQUI ENTRARIA O ENVIO REAL
                    # sucesso, msg = enviar_email_real(...)
                    time.sleep(1) # Delay anti-bloqueio
                    
                    # Log visual
                    sucessos += 1
                    log_container.markdown(f"✅ **{empresa}**: Enviado com sucesso!")
                    
                    progress_bar.progress((i + 1) / total)
                
                st.success(f"Ciclo Finalizado! {sucessos} enviados, {falhas} falhas.")
                st.balloons()
                
                # TODO: Salvar Log de volta no Google Sheets (Coluna 'Ultimo_Contato')

if __name__ == "__main__":
    main()