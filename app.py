import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from login import valida_senha
import gspread
from google.oauth2.service_account import Credentials


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

    # Configuração da página
    st.set_page_config(page_title="Dashboard de Gestão Laboratorial", layout="wide")

    # 1. FUNÇÃO PRIVADA PARA AUTENTICAÇÃO (Sem cache de dados do Streamlit)
    # CÓDIGO NOVO (Correto para o Streamlit Cloud)
    def get_gspread_client():
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Carrega os dados do Secrets do Streamlit
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Força a correção de quebras de linha que o TOML costuma desconfigurar
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=scopes
        )
        return gspread.authorize(creds)

    # 2. FUNÇÃO PRINCIPAL DE CARREGAMENTO (Esta sim leva o @st.cache_data)
    @st.cache_data(ttl=600)  # O cache expira a cada 10 minutos para buscar novidades do Sheets
    def load_data():
        # Obtém o cliente gspread ativo
        gc = get_gspread_client()
        
        # Abre a planilha do Google Sheets
        sheet = gc.open("Laboratorio Cascavel")
        
        # --- EXEMPLO DE LEITURA DAS ABAS ---
        # Captura os dados brutos de cada aba e converte para DataFrame do Pandas
        # Altere os nomes das abas ("Producao Geral", "Consolidado", "Cenarios") para os nomes exatos do seu Sheets
        
        # Aba 1: Produção Geral (df_geral)
        dados_geral = sheet.worksheet("Produção Geral").get_all_values()
        df_geral = pd.DataFrame(dados_geral[1:], columns=dados_geral[0])
        
        # Aba 2: Dados Consolidados (df_cons)
        dados_cons = sheet.worksheet("Consolidado").get_all_values()
        df_cons = pd.DataFrame(dados_cons[1:], columns=dados_cons[0])
        
        # Aba 3: Dicionário de Cenários PARCIAL/TOTAL (df_cenarios)
        dados_cenarios = sheet.worksheet("Dicionario_Cenarios").get_all_values()
        df_cenarios = pd.DataFrame(dados_cenarios[1:], columns=dados_cenarios[0])

        df_geral['Quantidade'] = pd.to_numeric(df_geral['Quantidade'], errors='coerce')

        df_geral['Valor'] = df_geral['Valor'].str.replace('R$', '', regex=False).str.strip()
        df_geral['Valor'] = df_geral['Valor'].str.replace(',', '.', regex=False)
        df_geral['Valor'] = pd.to_numeric(df_geral['Valor'], errors='coerce')

        df_geral['Custo Mensal'] = df_geral['Custo Mensal'].str.replace('R$', '', regex=False).str.strip()
        df_geral['Custo Mensal'] = df_geral['Custo Mensal'].str.replace(',', '.', regex=False)
        df_geral['Custo Mensal'] = pd.to_numeric(df_geral['Custo Mensal'], errors='coerce')

        # Pacientes	Exames	Exames por Paciente	Total Mensal	Custo por Paciente	Média por Exame 
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

        df_geral['Data'] = pd.to_datetime(df_geral['Data'], format='%d/%m/%Y', errors='coerce')
        df_cons['Mês/Ano'] = pd.to_datetime(df_cons['Mês/Ano'], format='%d/%m/%Y', errors='coerce')
        
        return df_geral, df_cons, df_cenarios

    df_geral, df_cons, df_cenarios = load_data()

    # Título e Sidebar
    st.title("📊 Gestão de Indicadores Laboratoriais")

    # --- SEÇÃO DE FILTROS NA SIDEBAR ---
    st.sidebar.header("Filtros de Visualização")

    # 1. Filtro de Mês/Ano (Baseado no DataFrame Consolidado ou Produção Geral)
    # Criamos uma lista formatada para exibição amigável
    meses_disponiveis = df_cons['Mês/Ano'].dt.strftime('%m/%Y').unique().tolist()
    opcoes_mes = ["Todos"] + meses_disponiveis

    mes_selecionado = st.sidebar.selectbox("1. Selecione o Mês", options=opcoes_mes)

    # 2. Filtro de Categoria
    categorias_disponiveis = df_geral['Categoria'].unique().tolist()
    opcoes_categoria = ["Todas"] + categorias_disponiveis

    categoria_selecionada = st.sidebar.selectbox("2. Selecione a Categoria", options=opcoes_categoria)

    # --- LÓGICA DE FILTRAGEM ---

    # Primeiro, filtramos por Mês
    if mes_selecionado == "Todos":
        df_filtrado = df_geral.copy()
        df_cons_filtrado = df_cons.copy()
    else:
        # Convertemos a seleção de volta para o formato de data para comparar
        mes_ref = pd.to_datetime(mes_selecionado, format='%m/%Y')
        df_filtrado = df_geral[
            (df_geral['Data'].dt.month == mes_ref.month) & 
            (df_geral['Data'].dt.year == mes_ref.year)
        ]
        df_cons_filtrado = df_cons[
            (df_cons['Mês/Ano'].dt.month == mes_ref.month) & 
            (df_cons['Mês/Ano'].dt.year == mes_ref.year)
        ]

    # Depois, aplicamos o filtro de Categoria sobre o resultado anterior
    if categoria_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria_selecionada]

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Exames na Categoria")

    # Extraímos a lista de exames únicos baseada na categoria selecionada
    # (df_filtrado já está filtrado pela categoria na lógica anterior)
    lista_exames = df_filtrado[['Descrição']].drop_duplicates().sort_values(by='Descrição')

    # Resetamos o index para não aparecer números aleatórios na lateral
    lista_exames = lista_exames.reset_index(drop=True)

    # Exibimos como uma tabela simples na barra lateral
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
        # Alteramos o 'y' para a coluna de quantidade de exames
        fig_producao = px.area(df_cons, 
                            x='Mês/Ano', 
                            y='Exames', # <--- Verifique se este é o nome exato na sua planilha
                            markers=True, 
                            labels={'Quantidade': 'Total de Exames'}, 
                            color_discrete_sequence=['#27AE60']) # Um verde para diferenciar do custo
        
        # Ajuste para garantir que o eixo X mostre os meses corretamente como fizemos no outro
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
    # --- LINHA 4: Detalhamento de Exames ---
        st.subheader("Top 10 Exames por Quantidade")
        top_exames = df_filtrado.groupby('Descrição')['Quantidade'].sum().nlargest(10).reset_index()
        fig_barras = px.bar(top_exames, x='Quantidade', y='Descrição', orientation='h',
                        text_auto='.2s', color='Quantidade', color_continuous_scale='Viridis')
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_barras, use_container_width=True)

    # --- LINHA 5: Indicadores de Eficiência (Barras e Linhas com Eixo Duplo) ---
    st.markdown("---")
    st.subheader("📊 Indicadores Médios de Eficiência")

    # IMPORTANTE: Usamos df_cons_filtrado para que o gráfico responda ao filtro de mês
    # Se "Todos" estiver selecionado, ele mostra a série histórica.
    # Se um mês for selecionado, ele mostra o comparativo daquele mês.

    fig_eficiencia = go.Figure()

    # 1. Custo por Paciente (Barras - Eixo Y Principal)
    fig_eficiencia.add_trace(go.Bar(
        x=df_cons_filtrado['Mês/Ano'],
        y=df_cons_filtrado['Custo por Paciente'],
        name='Custo por Paciente (R$)',
        marker_color='rgba(150, 150, 150, 0.4)',  # Cinza neutro
        text=df_cons_filtrado['Custo por Paciente'].map(lambda x: f"R${x:.2f}"),
        textposition='auto',
    ))

    # 2. Exames por Paciente (Linha Azul Claro - Eixo Y Secundário)
    fig_eficiencia.add_trace(go.Scatter(
        x=df_cons_filtrado['Mês/Ano'],
        y=df_cons_filtrado['Exames por Paciente'],
        name='Exames por Paciente',
        mode='lines+markers+text', # Adicionado text para garantir visibilidade se houver só 1 ponto
        line=dict(color='lightblue', width=4),
        text=df_cons_filtrado['Exames por Paciente'].round(2),
        textposition='top center',
        yaxis='y2'
    ))

    # 3. Média por Exame (Linha Vermelho Claro - Eixo Y Secundário)
    fig_eficiencia.add_trace(go.Scatter(
        x=df_cons_filtrado['Mês/Ano'],
        y=df_cons_filtrado['Média por Exame'],
        name='Média por Exame (R$)',
        mode='lines+markers+text',
        line=dict(color='salmon', width=4),
        text=df_cons_filtrado['Média por Exame'].map(lambda x: f"R${x:.2f}"),
        textposition='bottom center',
        yaxis='y2'
    ))

    # Configuração do Layout com Eixo Duplo
    fig_eficiencia.update_layout(
        xaxis=dict(
            type='date', 
            tickmode='linear',  # Força o modo linear de marcação
            dtick="M1",         # Define o intervalo para exatamente 1 mês
            tickformat='%b/%Y', 
            title=dict(text="Período")
        ),
        yaxis=dict(
            title=dict(
                text="Custo por Paciente (R$)",
                font=dict(color="#444")  # Correção: font dentro de title
            ),
            tickfont=dict(color="#444"),
            side='left',
            showgrid=True
        ),
        yaxis2=dict(
            title=dict(
                text="Médias (Exames/Custo Unitário)",
                font=dict(color="blue") # Correção: font dentro de title
            ),
            tickfont=dict(color="blue"),
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.05, 
            xanchor="center", 
            x=0.5
        ),
        height=600,
        margin=dict(l=50, r=50, t=100, b=50),
        hovermode="x unified"
    )

    st.plotly_chart(fig_eficiencia, use_container_width=True)
    
    # ==========================================
    # --- LINHA 6: PROJEÇÕES E SIMULAÇÃO DE CENÁRIOS (PERÍODO HISTÓRICO ÚNICO) ---
    # ==========================================
    st.markdown("---")
    st.subheader("🔮 Projeção e Simulação de Capacidade Mensal (Próximos 6 Meses)")
    st.markdown(
        "Simule a capacidade de atendimento do laboratório sob diferentes tetos orçamentários. "
        "Os cálculos utilizam a eficiência histórica real consolidada de **Março/2025 a Abril/2026**."
    )

    # 1. VALIDAÇÃO DO DF_CENARIOS: Garante que ele existe na sessão ou escopo local
    if 'df_cenarios' in locals() or 'df_cenarios' in globals():
        df_mapeamento = df_cenarios.copy()
        df_mapeamento.columns = df_mapeamento.columns.str.strip()
    else:
        st.error("❌ O DataFrame 'df_cenarios' não foi encontrado. Certifique-se de que ele foi retornado na função load_data().")
        st.stop()

    # 2. FILTRO DE ESCOPO NA TELA (Centralizado e direto)
    escopo_exames = st.radio(
        "Selecione o Modelo de Atendimento para a Projeção:",
        options=["Parcial (Apenas exames essenciais)", "Total (Todos os exames integrados)"],
        horizontal=True
    )

    # CÁLCULO DINÂMICO DA QUANTIDADE DE EXAMES REFERENCIADOS
    # Conta os códigos únicos presentes no seu df_cenarios dependendo da escolha
    if "Parcial" in escopo_exames:
        qtd_exames_perfil = df_mapeamento[df_mapeamento['CENÁRIO'] == 'PARCIAL']['CÓDIGO'].nunique()
        st.markdown(f"💡 *Nesse perfil estão presentes **{qtd_exames_perfil}** exames parciais de rotina/urgência. Cenário atual.*")
    else:
        # O cenário total engloba todos os tipos mapeados na lista (Parcial + Total juntos)
        qtd_exames_perfil = df_mapeamento['CÓDIGO'].nunique()
        st.markdown(f"💡 *Nesse perfil estão presentes **{qtd_exames_perfil}** exames (catálogo completo unificado).*")

    # 3. FILTRAGEM TEMPORAL FIXA: Março/2025 a Abril/2026
    df_historico_cons = df_cons[(df_cons['Mês/Ano'] >= '2025-03-01') & (df_cons['Mês/Ano'] <= '2026-04-30')]
    df_historico_geral = df_geral[(df_geral['Data'] >= '2025-03-01') & (df_geral['Data'] <= '2026-04-30')]
    
    # Fallbacks de segurança estatística caso o banco de dados falhe no carregamento
    fallback_custo, fallback_exames = 12.50, 4.2

    # 4. PROCESSAMENTO E MAPEAMENTO DA REGRA DE NEGÓCIO
    if not df_mapeamento.empty and not df_historico_geral.empty:
        # Cruza a produção geral com o mapeamento de cenários por exame
        df_geral_mapeado = df_historico_geral.merge(df_mapeamento, left_on='Exame', right_on='CÓDIGO', how='left')
        
        if "Parcial" in escopo_exames:
            # Filtra apenas os exames definidos estritamente como PARCIAL
            df_escopo = df_geral_mapeado[df_geral_mapeado['CENÁRIO'] == 'PARCIAL']
        else:
            # O cenário TOTAL engloba a soma de toda a operação (Parcial + Total juntos)
            df_escopo = df_geral_mapeado.copy()

        # Recalcula as métricas reais com base no escopo selecionado dentro do período
        total_custo_periodo = df_escopo['Custo Mensal'].sum()
        total_exames_periodo = df_escopo['Quantidade'].sum()
        
        # Coeficiente 1: Custo unitário médio por exame realizado
        media_historica_custo_exame = total_custo_periodo / total_exames_periodo if total_exames_periodo > 0 else fallback_custo
        
        # Coeficiente 2: Média de exames por paciente
        media_historica_exames_paciente = df_historico_cons['Exames por Paciente'].mean() if not df_historico_cons.empty else fallback_exames
        
        # Ajuste estatístico: Pacientes que realizam apenas exames parciais/essenciais demandam menos volume individual
        if "Parcial" in escopo_exames:
            media_historica_exames_paciente = max(1.5, media_historica_exames_paciente * 0.6)
    else:
        media_historica_custo_exame = fallback_custo
        media_historica_exames_paciente = fallback_exames

    # Exibe no painel os coeficientes obtidos do histórico para transparência do gestor
    st.info(
        f"📊 **Indicadores de Eficiência Aplicados (Mar/25 a Abr/26)** | "
        f"Custo Médio do Exame: **R$ {media_historica_custo_exame:.2f}** | "
        f"Média de Exames por Paciente: **{media_historica_exames_paciente:.2f}**"
    )

    # 5. DEFINIÇÃO DOS TETOS ORÇAMENTÁRIOS MENSAIS ALVOS
    cenarios = {
        "Cenário Econômico": 40000.00,
        "Cenário Realista": 60000.00,
        "Cenário de Expansão": 80000.00
    }

    # 6. RENDERIZAÇÃO DOS CARDS DE RESULTADOS (3 Colunas)
    Abas_cenarios = st.columns(3)

    for i, (nome_cenario, custo_mensal_alvo) in enumerate(cenarios.items()):
        with Abas_cenarios[i]:
            st.markdown(f"### {nome_cenario}")
            st.markdown(f"**Orçamento Mensal:** R$ {custo_mensal_alvo:,.2f}")
            
            # Matemática da Projeção de Atendimento Mensal
            exames_projetados_mes = custo_mensal_alvo / media_historica_custo_exame
            pacientes_projetados_mes = exames_projetados_mes / media_historica_exames_paciente
            
            # Acumuladores de planejamento para a janela de 6 meses
            custo_6meses = custo_mensal_alvo * 6
            exames_6meses = exames_projetados_mes * 6
            pacientes_6meses = pacientes_projetados_mes * 6

            # Exibição clara e legível da capacidade mensal
            st.metric(label="Pacientes Atendidos / Mês", value=f"{int(pacientes_projetados_mes):,}")
            st.metric(label="Capacidade de Exames / Mês", value=f"{int(exames_projetados_mes):,}")
            
            with st.expander("Visualizar Acumulado de 6 meses"):
                st.write(f"• **Investimento Total:** R$ {custo_6meses:,.2f}")
                st.write(f"• **Total de Exames no Período:** {int(exames_6meses):,}")
                st.write(f"• **Total de Pacientes no Período:** {int(pacientes_6meses):,}")
            st.markdown("---")

    # 7. GRÁFICO COMPARATIVO DE CUSTOS ACUMULADOS (Plotly)
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
            
            # Força o Streamlit a recarregar o script imediatamente.
            # Como logged_in agora é True, ele vai entrar no bloco do Dashboard
            # e a tela de login sumirá completamente.
            st.rerun() 
        else:
            st.error("Usuário ou senha incorretos")
