import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from login import valida_senha
import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Gestão Laboratorial",
    layout="wide"
)

# 1. Inicializa as variáveis de estado
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ==========================================
# CÓDIGO DO DASHBOARD (Se estiver logado)
# ==========================================
if st.session_state.logged_in:
    # Botão de Logout na barra lateral
    with st.sidebar:
        st.write(f"Logado como: **{st.session_state.username}**")
        if st.button("Sair / Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun() # Recarrega para voltar à tela de login

    # ---------------------------------------------------------
    # TODO O SEU CÓDIGO DO DASHBOARD ABAIXO (IDENTADO)
    # ---------------------------------------------------------
       
    def get_gspread_client():
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
    
        return gspread.authorize(creds)

    # 2. FUNÇÃO PRINCIPAL DE CARREGAMENTO (Esta sim leva o @st.cache_data)
    @st.cache_data(ttl=600)  # O cache expira a cada 10 minutos para buscar novidades do Sheets
    def load_data():
        # Obtém o cliente gspread ativo
        gc = get_gspread_client()
        
        # Abre a planilha do Google Sheets
        sheet = gc.open_by_key("1ABRFkZVcfskRaa_Yp13Ku9lzTmpggA6MJLdDperZbn0")
        
        # Aba 1: Produção Geral (df_geral)
        dados_geral = sheet.worksheet("Produção Geral").get_all_values()
        df_geral = pd.DataFrame(dados_geral[1:], columns=dados_geral[0])
        
        # Aba 2: Dados Consolidados (df_cons)
        dados_cons = sheet.worksheet("Consolidado").get_all_values()
        df_cons = pd.DataFrame(dados_cons[1:], columns=dados_cons[0])
        
        # Aba 3: Dicionário de Cenários PARCIAL/TOTAL (df_cenarios)
        dados_cenarios = sheet.worksheet("Dicionario_Cenarios").get_all_values()
        df_cenarios = pd.DataFrame(dados_cenarios[1:], columns=dados_cenarios[0])

        # Nova Aba: Tabela de Pacientes por Unidade
        dados_pacientes = sheet.worksheet("Pacientes").get_all_values()
        df_pacientes = pd.DataFrame(dados_pacientes[1:], columns=dados_pacientes[0])

        # Tratamento de dados brutos
        df_geral['Quantidade'] = pd.to_numeric(df_geral['Quantidade'], errors='coerce')

        df_geral['Valor'] = df_geral['Valor'].str.replace('R$', '', regex=False).str.strip()
        df_geral['Valor'] = df_geral['Valor'].str.replace(',', '.', regex=False)
        df_geral['Valor'] = pd.to_numeric(df_geral['Valor'], errors='coerce')

        df_geral['Custo Mensal'] = df_geral['Custo Mensal'].str.replace('R$', '', regex=False).str.strip()
        df_geral['Custo Mensal'] = df_geral['Custo Mensal'].str.replace(',', '.', regex=False)
        df_geral['Custo Mensal'] = pd.to_numeric(df_geral['Custo Mensal'], errors='coerce')

        df_cons['Pacientes'] = pd.to_numeric(df_cons['Pacientes'], errors='coerce')
        df_cons['Exames'] = pd.to_numeric(df_cons['Exames'], errors='coerce')

        df_cons['Exames por Paciente'] = df_cons['Exames por Paciente'].str.replace('R$', '', regex=False).str.strip()
        df_cons['Exames por Paciente'] = df_cons['Exames por Paciente'].str.replace(',', '.', regex=False)
        df_cons['Exames por Paciente'] = pd.to_numeric(df_cons['Exames por Paciente'], errors='coerce')

        df_cons['Total Mensal'] = df_cons['Total Mensal'].str.replace('.', '', regex=False)
        df_cons['Total Mensal'] = df_cons['Total Mensal'].str.replace('R$', '', regex=False).str.strip()
        df_cons['Total Mensal'] = df_cons['Total Mensal'].str.replace(',', '.', regex=False)
        df_cons['Total Mensal'] = pd.to_numeric(df_cons['Total Mensal'], errors='coerce')

        df_cons['Custo por Paciente'] = df_cons['Custo por Paciente'].str.replace('R$', '', regex=False).str.strip()
        df_cons['Custo por Paciente'] = df_cons['Custo por Paciente'].str.replace(',', '.', regex=False)
        df_cons['Custo por Paciente'] = pd.to_numeric(df_cons['Custo por Paciente'], errors='coerce')

        df_cons['Média por Exame'] = df_cons['Média por Exame'].str.replace('R$', '', regex=False).str.strip()
        df_cons['Média por Exame'] = df_cons['Média por Exame'].str.replace(',', '.', regex=False)
        df_cons['Média por Exame'] = pd.to_numeric(df_cons['Média por Exame'], errors='coerce')

        # Conversão de datas
        df_geral['Data'] = pd.to_datetime(df_geral['Data'], format='%d/%m/%Y', errors='coerce')
        df_cons['Mês/Ano'] = pd.to_datetime(df_cons['Mês/Ano'], format='%d/%m/%Y', errors='coerce')
        df_pacientes['Data_Exame'] = pd.to_datetime(df_pacientes['Data_Exame'], format='%d/%m/%Y', errors='coerce')
        
        return df_geral, df_cons, df_cenarios, df_pacientes

    df_geral, df_cons, df_cenarios, df_pacientes = load_data()

    # Título e Sidebar
    st.title("📊 Gestão de Indicadores Laboratoriais")

    # --- SEÇÃO DE FILTROS NA SIDEBAR ---
    st.sidebar.header("Filtros de Visualização")

    meses_disponiveis = df_cons['Mês/Ano'].dt.strftime('%m/%Y').unique().tolist()
    opcoes_mes = ["Todos"] + meses_disponiveis

    mes_selecionado = st.sidebar.selectbox("1. Selecione o Mês", options=opcoes_mes)

    categorias_disponiveis = df_geral['Categoria'].unique().tolist()
    opcoes_categoria = ["Todas"] + categorias_disponiveis

    categoria_selecionada = st.sidebar.selectbox("2. Selecione a Categoria", options=opcoes_categoria)

    # --- LÓGICA DE FILTRAGEM ---

    if mes_selecionado == "Todos":
        df_filtrado = df_geral.copy()
        df_cons_filtrado = df_cons.copy()
        df_pacientes_filtrado = df_pacientes.copy()
    else:
        mes_ref = pd.to_datetime(mes_selecionado, format='%m/%Y')
        df_filtrado = df_geral[
            (df_geral['Data'].dt.month == mes_ref.month) & 
            (df_geral['Data'].dt.year == mes_ref.year)
        ]
        df_cons_filtrado = df_cons[
            (df_cons['Mês/Ano'].dt.month == mes_ref.month) & 
            (df_cons['Mês/Ano'].dt.year == mes_ref.year)
        ]
        df_pacientes_filtrado = df_pacientes[
            (df_pacientes['Data_Exame'].dt.month == mes_ref.month) & 
            (df_pacientes['Data_Exame'].dt.year == mes_ref.year)
        ]

    if categoria_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria_selecionada]

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Exames na Categoria")

    lista_exames = df_filtrado[['Descrição']].drop_duplicates().sort_values(by='Descrição')
    lista_exames = lista_exames.reset_index(drop=True)
    st.sidebar.table(lista_exames)

    # --- LINHA 1: KPIs ---
    col1, col2, col3, col4, col5 = st.columns(5)
    total_custo = df_filtrado['Custo Mensal'].sum()
    total_exames = df_filtrado['Quantidade'].sum()
    media_custo_exame = total_custo / total_exames if total_exames > 0 else 0
    quantidade_pacientes = df_cons_filtrado['Pacientes'].sum()

    with col1:
        st.metric("Custo Total Acumulado", f"R$ {total_custo:,.2f}")
    with col2:
        st.metric("Total de Exames", f"{total_exames:,}")
    with col3:
        st.metric("Média Custo/Exame", f"R$ {media_custo_exame:.2f}")
    with col4:
        st.metric("Meses Analisados", len(df_cons))
    with col5:
        st.metric("Total de Pacientes", f"{quantidade_pacientes:,}")

    # --- LINHA 2: Gráficos de Produção ---
    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Evolução Mensal de Produção (Exames)")
        fig_producao = px.area(df_cons, 
                            x='Mês/Ano', 
                            y='Exames', 
                            markers=True, 
                            labels={'Quantidade': 'Total de Exames'}, 
                            color_discrete_sequence=['#27AE60'])
        fig_producao.update_xaxes(dtick="M1", tickformat="%b/%Y")
        st.plotly_chart(fig_producao, use_container_width=True)

    with c2:
        st.subheader("Distribuição por Categoria (Volume)")
        fig_pizza = px.pie(df_filtrado, values='Quantidade', names='Categoria', hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pizza, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    # --- LINHA 3: Detalhamento de Exames ---
    with c1:
        st.subheader("Top 10 Exames por Custo")
        top_exames = df_filtrado.groupby('Descrição')['Custo Mensal'].sum().nlargest(10).reset_index()
        fig_barras = px.bar(top_exames, x='Custo Mensal', y='Descrição', orientation='h',
                        text_auto='.2s', color='Custo Mensal', color_continuous_scale='Viridis')
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_barras, use_container_width=True)

    with c2:
        st.subheader("Top 10 Exames por Quantidade")
        top_exames = df_filtrado.groupby('Descrição')['Quantidade'].sum().nlargest(10).reset_index()
        fig_barras = px.bar(top_exames, x='Quantidade', y='Descrição', orientation='h',
                        text_auto='.2s', color='Quantidade', color_continuous_scale='Viridis')
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_barras, use_container_width=True)

    # --- LINHA 5: Indicadores de Eficiência ---
    st.markdown("---")
    st.subheader("📊 Indicadores Médios de Eficiência")

    fig_eficiencia = go.Figure()

    fig_eficiencia.add_trace(go.Bar(
        x=df_cons_filtrado['Mês/Ano'],
        y=df_cons_filtrado['Custo por Paciente'],
        name='Custo por Paciente (R$)',
        marker_color='rgba(150, 150, 150, 0.4)',
        text=df_cons_filtrado['Custo por Paciente'].map(lambda x: f"R${x:.2f}" if pd.notnull(x) else ""),
        textposition='auto',
    ))

    fig_eficiencia.add_trace(go.Scatter(
        x=df_cons_filtrado['Mês/Ano'],
        y=df_cons_filtrado['Exames por Paciente'],
        name='Exames por Paciente',
        mode='lines+markers+text',
        line=dict(color='lightblue', width=4),
        text=df_cons_filtrado['Exames por Paciente'].round(2),
        textposition='top center',
        yaxis='y2'
    ))

    fig_eficiencia.add_trace(go.Scatter(
        x=df_cons_filtrado['Mês/Ano'],
        y=df_cons_filtrado['Média por Exame'],
        name='Média por Exame (R$)',
        mode='lines+markers+text',
        line=dict(color='salmon', width=4),
        text=df_cons_filtrado['Média por Exame'].map(lambda x: f"R${x:.2f}" if pd.notnull(x) else ""),
        textposition='bottom center',
        yaxis='y2'
    ))

    fig_eficiencia.update_layout(
        xaxis=dict(type='date', tickmode='linear', dtick="M1", tickformat='%b/%Y', title=dict(text="Período")),
        yaxis=dict(title=dict(text="Custo por Paciente (R$)", font=dict(color="#444")), tickfont=dict(color="#444"), side='left', showgrid=True),
        yaxis2=dict(title=dict(text="Médias (Exames/Custo Unitário)", font=dict(color="blue")), tickfont=dict(color="blue"), overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        height=600, margin=dict(l=50, r=50, t=100, b=50), hovermode="x unified"
    )

    st.plotly_chart(fig_eficiencia, use_container_width=True)
    
    # ==========================================
    # --- LINHA: ATENDIMENTOS POR POSTO DE SAÚDE ---
    # ==========================================
    st.markdown("---")
    st.subheader("🏥 Volume de Atendimentos por Posto de Saúde")
    
    if not df_pacientes_filtrado.empty:
        df_unidades = df_pacientes_filtrado.groupby('Unidade')['Codigo_Paciente'].nunique().reset_index()
        df_unidades.columns = ['Unidade', 'Atendimentos']
        df_unidades = df_unidades.sort_values(by='Atendimentos', ascending=True)
        
        fig_unidades = px.bar(
            df_unidades, 
            x='Atendimentos', 
            y='Unidade', 
            orientation='h',
            text_auto=True,
            labels={'Atendimentos': 'Quantidade de Pacientes Atendidos', 'Unidade': 'Posto de Saúde'},
            color='Atendimentos',
            color_continuous_scale='Blues'
        )
        fig_unidades.update_layout(margin=dict(l=150, r=50, t=30, b=50), height=500)
        st.plotly_chart(fig_unidades, use_container_width=True)
    else:
        st.info("Nenhum dado de atendimento encontrado para os filtros selecionados.")

    # ==========================================
    # --- LINHA 6: PROJEÇÕES E SIMULAÇÃO DE CENÁRIOS (COM ESTUDO POR UNIDADE) ---
    # ==========================================
    st.markdown("---")
    st.subheader("🔮 Projeção e Simulação de Capacidade Mensal (Próximos 6 Meses)")
    st.markdown(
        "Simule a capacidade de atendimento do laboratório sob diferentes tetos orçamentários. "
        "Os cálculos utilizam a eficiência histórica real consolidada de **Março/2025 a Abril/2026**."
    )

    if 'df_cenarios' in locals() or 'df_cenarios' in globals():
        df_mapeamento = df_cenarios.copy()
        df_mapeamento.columns = df_mapeamento.columns.str.strip()
    else:
        st.error("❌ O DataFrame 'df_cenarios' não foi encontrado. Certifique-se de que ele foi retornado na função load_data().")
        st.stop()

    escopo_exames = st.radio(
        "Selecione o Modelo de Atendimento para a Projeção:",
        options=["Parcial (Apenas exames essenciais)", "Total (Todos os exames integrados)"],
        horizontal=True
    )

    if "Parcial" in escopo_exames:
        qtd_exames_perfil = df_mapeamento[df_mapeamento['CENÁRIO'] == 'PARCIAL']['CÓDIGO'].nunique()
        st.markdown(f"💡 *Nesse perfil estão presentes **{qtd_exames_perfil}** exames parciais de rotina/urgência. Cenário atual.*")
    else:
        qtd_exames_perfil = df_mapeamento['CÓDIGO'].nunique()
        st.markdown(f"💡 *Nesse perfil estão presentes **{qtd_exames_perfil}** exames (catálogo completo unificado).*")

    # Filtros da Janela Histórica
    df_historico_cons = df_cons[(df_cons['Mês/Ano'] >= '2025-03-01') & (df_cons['Mês/Ano'] <= '2026-04-30')]
    df_historico_geral = df_geral[(df_geral['Data'] >= '2025-03-01') & (df_geral['Data'] <= '2026-04-30')]
    df_historico_pacientes = df_pacientes[(df_pacientes['Data_Exame'] >= '2025-03-01') & (df_pacientes['Data_Exame'] <= '2026-04-30')]
    
    # Cálculo da distribuição percentual por Posto de Saúde obtido do histórico fixo
    if not df_historico_pacientes.empty:
        df_dist_unidades = df_historico_pacientes.groupby('Unidade')['Codigo_Paciente'].nunique().reset_index()
        total_pacientes_hist = df_dist_unidades['Codigo_Paciente'].sum()
        df_dist_unidades['Percentual'] = df_dist_unidades['Codigo_Paciente'] / total_pacientes_hist if total_pacientes_hist > 0 else 0
    else:
        df_dist_unidades = pd.DataFrame(columns=['Unidade', 'Percentual'])

    fallback_custo, fallback_exames = 12.50, 4.2

    if not df_mapeamento.empty and not df_historico_geral.empty:
        df_geral_mapeado = df_historico_geral.merge(df_mapeamento, left_on='Exame', right_on='CÓDIGO', how='left')
        
        if "Parcial" in escopo_exames:
            df_escopo = df_geral_mapeado[df_geral_mapeado['CENÁRIO'] == 'PARCIAL']
        else:
            df_escopo = df_geral_mapeado.copy()

        total_custo_periodo = df_escopo['Custo Mensal'].sum()
        total_exames_periodo = df_escopo['Quantidade'].sum()
        
        media_historica_custo_exame = total_custo_periodo / total_exames_periodo if total_exames_periodo > 0 else fallback_custo
        media_historica_exames_paciente = df_historico_cons['Exames por Paciente'].mean() if not df_historico_cons.empty else fallback_exames
        
        if "Parcial" in escopo_exames:
            media_historica_exames_paciente = max(1.5, media_historica_exames_paciente * 0.6)
    else:
        media_historica_custo_exame = fallback_custo
        media_historica_exames_paciente = fallback_exames

    st.info(
        f"📊 **Indicadores de Eficiência Aplicados (Mar/25 a Abr/26)** | "
        f"Custo Médio do Exame: **R$ {media_historica_custo_exame:.2f}** | "
        f"Média de Exames por Paciente: **{media_historica_exames_paciente:.2f}**"
    )

    cenarios = {
        "Cenário Econômico": 40000.00,
        "Cenário Realista": 60000.00,
        "Cenário de Expansão": 80000.00
    }

    Abas_cenarios = st.columns(3)

    for i, (nome_cenario, custo_mensal_alvo) in enumerate(cenarios.items()):
        with Abas_cenarios[i]:
            st.markdown(f"### {nome_cenario}")
            st.markdown(f"**Orçamento Mensal:** R$ {custo_mensal_alvo:,.2f}")
            
            exames_projetados_mes = custo_mensal_alvo / media_historica_custo_exame
            pacientes_projetados_mes = exames_projetados_mes / media_historica_exames_paciente
            
            custo_6meses = custo_mensal_alvo * 6
            exames_6meses = exames_projetados_mes * 6
            pacientes_6meses = pacientes_projetados_mes * 6

            st.metric(label="Pacientes Atendidos / Mês", value=f"{int(pacientes_projetados_mes):,}")
            st.metric(label="Capacidade de Exames / Mês", value=f"{int(exames_projetados_mes):,}")
            
            with st.expander("Visualizar Acumulado de 6 meses"):
                st.write(f"• **Investimento Total:** R$ {custo_6meses:,.2f}")
                st.write(f"• **Total de Exames no Período:** {int(exames_6meses):,}")
                st.write(f"• **Total de Pacientes no Período:** {int(pacientes_6meses):,}")
            
            # --- NOVA TABELA: ESTIMATIVA DE ATENDIMENTO POR UNIDADE ---
            st.markdown("**Pacientes Estimados / Unidade (Mensal):**")
            if not df_dist_unidades.empty:
                df_proj_unidade = df_dist_unidades.copy()
                # Calcula a projeção de pacientes baseada no peso de cada unidade
                df_proj_unidade['Pacientes/Mês'] = (df_proj_unidade['Percentual'] * pacientes_projetados_mes).astype(int)
                df_proj_unidade['Acumulado (6 Meses)'] = (df_proj_unidade['Percentual'] * pacientes_6meses).astype(int)
                
                # Formata a tabela para exibição limpa
                df_exibicao = df_proj_unidade[['Unidade', 'Pacientes/Mês', 'Acumulado (6 Meses)']].reset_index(drop=True)
                st.dataframe(df_exibicao, use_container_width=True)
            else:
                st.caption("Sem dados históricos de unidades para ratear a projeção.")
            st.markdown("---")

    meses_futuros = ["Mês 1", "Mês 2", "Mês 3", "Mês 4", "Mês 5", "Mês 6"]
    fig_projecao = go.Figure()
    cores_cenarios = {"Cenário Econômico": "orange", "Cenário Realista": "blue", "Cenário de Expansão": "green"}

    for nome_cenario, custo_mensal_alvo in cenarios.items():
        valores_acumulados = [custo_mensal_alvo * m for m in range(1, 7)]
        fig_projecao.add_trace(go.Scatter(
            x=meses_futuros, 
            y=valores_acumulados,
            mode='lines+markers',
            name=f"{nome_cenario} (R$ {custo_mensal_alvo/1000:.0f}k/mês)",
            line=dict(color=cores_cenarios[nome_cenario], width=3),
            hovertemplate="Acumulado: R$ %{y:,.2f}<extra></extra>"
        ))

    fig_projecao.update_layout(
        title=f"Tendência de Investimento Acumulado - Escopo: {escopo_exames.split(' ')[0]}",
        xaxis_title="Meses do Planejamento Orçamentário",
        yaxis_title="Investimento Acumulado (R$)",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    
    st.plotly_chart(fig_projecao, use_container_width=True)

# ==========================================
# CÓDIGO DA TELA DE LOGIN (Se NÃO estiver logado)
# ==========================================
else:
    st.title("Tela de Login")

    with st.form("login_form"):
        st.subheader("Insira suas credenciais")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        if valida_senha(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Bem-vindo, {username}!")
            st.rerun() 
        else:
            st.error("Usuário ou senha incorretos")
