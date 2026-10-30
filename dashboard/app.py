"""Dashboard do Next Step SP (Marco E).

Interativo: gráficos com zoom e tooltip, comparação entre empresas, referência do setor (mediana e quartis),
clique no ranking e no mapa de risco para abrir os detalhes, chat com o agente e download dos dados.
A empresa escolhida fica no endereço da página (?empresa=...), para compartilhar o link.

Rode (na raiz do projeto, com o banco no ar): streamlit run dashboard/app.py   (ou: make dashboard)
"""

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dados as d  # noqa: E402

st.set_page_config(page_title="Next Step SP", page_icon="📊", layout="wide")

# Paleta de referência (skill dataviz): ordem fixa por entidade, nunca por posição no ranking
CORES_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
CINZA = "#8a8984"
STATUS = {"perigo": "#d03b3b", "cinzenta": "#c98500", "segura": "#2e8540"}
NOMES_ZONA = {"perigo": "Perigo (Z'' < 1,1)", "cinzenta": "Cinzenta (1,1 a 2,6)", "segura": "Segura (Z'' > 2,6)"}


def layout(fig: go.Figure, metrica: str | None = None, altura: int = 360) -> go.Figure:
    """Grade discreta, um só eixo, legenda acima, tooltip unificado por ano."""
    fig.update_layout(
        height=altura,
        margin={"l": 8, "r": 8, "t": 72, "b": 8},
        title={"y": 0.97, "yanchor": "top", "x": 0, "xanchor": "left"},
        legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0, "font": {"size": 11}},
        hovermode="x unified",
        font={"family": "sans-serif"},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    if metrica:
        fig.update_yaxes(tickformat=d.formato_eixo(metrica))
    return fig


def grafico_evolucao(series: pd.DataFrame, referencia: pd.DataFrame, metrica: str, empresas: list[str]) -> go.Figure:
    fig = go.Figure()
    escala = 1e9 if metrica in d.EM_REAIS else 1  # valores em reais: eixo em R$ bilhões
    if not referencia.empty and f"{metrica}__p50" in referencia:
        # Faixa entre o 1º e o 3º quartil do setor: onde está a metade "do meio" das empresas
        fig.add_trace(
            go.Scatter(
                x=list(referencia["ano"]) + list(referencia["ano"][::-1]),
                y=list(referencia[f"{metrica}__p75"] / escala) + list(referencia[f"{metrica}__p25"][::-1] / escala),
                fill="toself",
                fillcolor="rgba(138,137,132,0.15)",
                line={"width": 0},
                hoverinfo="skip",
                name="Setor: 25% a 75%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=referencia["ano"],
                y=referencia[f"{metrica}__p50"] / escala,
                mode="lines",
                line={"color": CINZA, "width": 2, "dash": "dash"},
                name="Mediana do setor",
                hovertemplate=("R$ %{y:,.1f} bi" if escala > 1 else "%{y:" + d.formato_eixo(metrica) + "}"),
            )
        )
    for i, empresa in enumerate(empresas):
        dados_empresa = series[series["empresa"] == empresa].sort_values("ano")
        fig.add_trace(
            go.Scatter(
                x=dados_empresa["ano"],
                y=dados_empresa[metrica] / escala,
                mode="lines+markers",
                line={"color": CORES_SERIES[i], "width": 2.5},
                marker={"size": 8},
                name=empresa.title(),
                hovertemplate=("R$ %{y:,.1f} bi" if escala > 1 else "%{y:" + d.formato_eixo(metrica) + "}"),
            )
        )
    fig.update_layout(title={"text": d.rotulo(metrica), "font": {"size": 15}})
    fig = layout(fig, metrica)
    if escala > 1:
        fig.update_yaxes(tickformat=",.0f", ticksuffix=" bi", tickprefix="R$ ")
    return fig


# ---------- Filtros globais (barra lateral) ----------
with st.sidebar:
    st.header("Next Step SP")
    st.caption("Plataforma de dados financeiros ponta a ponta com os balanços públicos da CVM.")
    inicio, fim = st.slider("Período", 2010, d.ULTIMO_ANO, (2015, d.ULTIMO_ANO))
    receita_minima = st.select_slider(
        "Receita mínima para comparações",
        options=[0.0, 1e8, 1e9, 1e10],
        value=d.RECEITA_MINIMA_PADRAO,
        format_func=lambda v: "sem corte" if v == 0 else d.formatar("receita_liquida", v),
        help="Holdings com receita quase zero geram margens absurdas e distorcem rankings e medianas.",
    )
    st.divider()
    q = d.qualidade()
    st.caption(
        f"{d.br(q['linhas_raw'] / 1e6)} mi de linhas na origem · {d.br(q['documentos'], 0)} balanços anuais · "
        f"{d.br(q['empresas'], 0)} empresas"
    )
    st.caption("Fonte: CVM, Portal de Dados Abertos (licença ODbL). Não é recomendação de investimento.")

aba_empresa, aba_ranking, aba_risco, aba_ia, aba_metodo = st.tabs(
    ["🏢 Empresa", "🏆 Ranking", "⚠️ Risco", "💬 Pergunte à IA", "🔎 Dados e método"]
)


# ---------- Empresa ----------
def aba_empresa_conteudo():
    """Aba Empresa. É uma função para poder encerrar só esta aba (return) sem parar as outras."""
    padrao = st.query_params.get("empresa", "WEG S.A.")
    c1, c2 = st.columns([1.3, 2])
    termo = c1.text_input("Buscar empresa", value=padrao.split(" ")[0], help="Ex.: weg, ambev, magazine, petrobras")
    achadas = d.buscar(termo) if termo else []
    if not achadas:
        st.warning("Nenhuma empresa comercial ou industrial com esse nome na base.")
        return
    nomes = [e["nome_oficial"] for e in achadas]
    empresa = c2.selectbox(
        "Empresa", nomes, index=nomes.index(padrao) if padrao in nomes else 0, key="empresa_principal"
    )
    st.query_params["empresa"] = empresa
    setor = d.setor_da_empresa(empresa)

    pares_opcoes = []
    if setor:
        pares = d.ranking("receita_liquida", fim, setor, receita_minima)
        pares_opcoes = [p for p in pares.get("empresa", pd.Series(dtype=str)).tolist() if p != empresa]
    c3, c4 = st.columns([2, 1.3])
    comparar = c3.multiselect(
        "Comparar com (até 3)",
        pares_opcoes,
        max_selections=3,
        help=f"Maiores empresas do setor por receita em {fim}." if setor else None,
        placeholder="Escolha empresas do mesmo setor",
    )
    mostrar_setor = c4.toggle("Mostrar referência do setor", value=True, disabled=not setor)

    empresas = [empresa, *comparar]
    series = d.series(tuple(empresas), inicio, fim)
    referencia = d.referencia_setor(setor, inicio, fim, receita_minima) if setor and mostrar_setor else pd.DataFrame()
    if series.empty:
        st.info("Sem balanços consistentes nesse período.")
        return

    principal = series[series["empresa"] == empresa].sort_values("ano")
    ultimo = principal.iloc[-1]
    ref_ultimo = referencia[referencia["ano"] == ultimo["ano"]] if not referencia.empty else pd.DataFrame()
    st.subheader(f"{empresa.title()} · {int(ultimo['ano'])}")
    st.caption(f"Setor (cadastro CVM): {setor or 'não informado'}")

    # Contêiner horizontal com quebra: em tela larga os 5 cards ficam lado a lado; em tela estreita, quebram de linha
    cards = st.container(horizontal=True, wrap=True, gap="small")
    for metrica in ["receita_liquida", "lucro_liquido", "margem_liquida", "roe", "aliquota_efetiva_ir_csll"]:
        coluna = cards
        comparacao = None
        if not ref_ultimo.empty and pd.notna(ultimo[metrica]) and metrica not in d.EM_REAIS:
            mediana = ref_ultimo[f"{metrica}__p50"].iloc[0]
            if pd.notna(mediana):
                comparacao = f"setor: {d.formatar(metrica, mediana)}"
        coluna.metric(
            d.rotulo(metrica),
            d.formatar(metrica, ultimo[metrica]),
            comparacao,
            delta_color="off",
            delta_arrow="off",
            help=d.regra(metrica),
            border=True,
            chart_data=principal[metrica].dropna().tolist(),  # minigráfico com a tendência do período
            chart_type="area",
            width=215,
        )

    grupo = st.segmented_control("Grupo de métricas", list(d.GRUPOS), default="Rentabilidade")
    metricas_grupo = d.GRUPOS[grupo or "Rentabilidade"]
    colunas = st.columns(2)
    for i, metrica in enumerate(metricas_grupo):
        with colunas[i % 2]:
            st.plotly_chart(grafico_evolucao(series, referencia, metrica, empresas), use_container_width=True)
            st.caption(d.regra(metrica))

    with st.expander("Ver tabela e baixar os dados"):
        tabela = series.sort_values(["empresa", "ano"])
        st.dataframe(
            tabela.assign(**{m: tabela[m].map(lambda v, m=m: d.formatar(m, v)) for m in d.METRICAS}).rename(
                columns={m: d.rotulo(m) for m in d.METRICAS}
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.download_button(
            "Baixar CSV", tabela.to_csv(index=False).encode("utf-8"), f"next_step_sp_{empresa[:20]}.csv", "text/csv"
        )


with aba_empresa:
    aba_empresa_conteudo()

# ---------- Ranking ----------
with aba_ranking:
    c1, c2, c3 = st.columns([1.2, 1.6, 0.6])
    metrica = c1.selectbox(
        "Métrica", d.METRICAS, index=d.METRICAS.index("margem_liquida"), format_func=d.rotulo, key="metrica_ranking"
    )
    setor_ranking = c2.selectbox("Setor", ["Todos", *d.setores()], key="setor_ranking")
    ano = c3.selectbox("Ano", list(range(d.ULTIMO_ANO, 2009, -1)), key="ano_ranking")
    tabela = d.ranking(metrica, ano, None if setor_ranking == "Todos" else setor_ranking, receita_minima)
    if tabela.empty:
        st.info("Sem empresas para esse filtro. Tente reduzir a receita mínima na barra lateral.")
    else:
        top = tabela.head(15).iloc[::-1]
        escala = 1e9 if metrica in d.EM_REAIS else 1
        fig = go.Figure(
            go.Bar(
                x=top[metrica] / escala,
                y=[e.title()[:45] for e in top["empresa"]],
                orientation="h",
                marker={"color": CORES_SERIES[0], "cornerradius": 4},
                text=[d.formatar(metrica, v) for v in top[metrica]],
                textposition="outside",
                customdata=top["empresa"],
                hovertemplate="%{customdata}<br>%{text}<extra></extra>",
            )
        )
        # Folga à direita para o rótulo da maior barra não ser cortado
        maximo, minimo = top[metrica].max() / escala, min(0, top[metrica].min() / escala)
        fig.update_xaxes(
            tickformat=",.0f" if escala > 1 else d.formato_eixo(metrica),
            ticksuffix=" bi" if escala > 1 else "",
            range=[minimo * 1.15, maximo * 1.18],
        )
        evento = st.plotly_chart(
            layout(fig, altura=40 * len(top) + 60).update_layout(hovermode="closest"),
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="grafico_ranking",
        )
        st.caption(f"{d.rotulo(metrica)}: {d.regra(metrica)}")
        if (tabela[metrica] > 1).any() and metrica in d.PERCENTUAIS:
            st.caption(
                "Valores acima de 100% são reais: em geral, ganhos não operacionais (ex.: venda de ativos) ou "
                "holdings que registram o lucro das controladas."
            )
        # Clique na barra ou escolha na lista: as duas formas abrem o detalhe
        selecionados = evento.selection.points if evento and evento.selection else []
        clicada = selecionados[0]["customdata"] if selecionados else None
        opcoes = tabela.head(15)["empresa"].tolist()
        escolhida = st.selectbox(
            "Ver detalhes de (ou clique numa barra)",
            opcoes,
            index=opcoes.index(clicada) if clicada in opcoes else None,
            format_func=str.title,
            placeholder="Escolha uma empresa do ranking",
            key="detalhe_ranking",
        )
        if escolhida:
            st.subheader(escolhida.title())
            detalhe = d.series((escolhida,), max(inicio, 2015), fim)
            mini = st.columns(3)
            for coluna, m in zip(mini, ["receita_liquida", metrica, "divida_sobre_patrimonio"], strict=False):
                coluna.plotly_chart(grafico_evolucao(detalhe, pd.DataFrame(), m, [escolhida]), use_container_width=True)
            if st.button("Abrir na aba Empresa", key="abrir_empresa"):
                st.query_params["empresa"] = escolhida
                st.rerun()

# ---------- Risco ----------
with aba_risco:
    avaliacao = d.avaliacao_modelo()
    modelo = avaliacao["modelos"][avaliacao["modelo_escolhido"]]
    altman = avaliacao["modelos"]["z_altman"]
    st.subheader("Risco de dificuldade financeira nos próximos 24 meses")
    st.markdown(
        "Nota do modelo (*gradient boosting*) sobre o balanço mais recente de cada empresa. É uma **nota relativa**: "
        "o percentil diz em que fatia de risco a empresa está. Use como **alerta para investigar**, não como veredito."
    )
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "AUC",
        d.br(modelo["auc"], 2),
        f"Z'' de Altman: {d.br(altman['auc'], 2)}",
        delta_color="off",
        delta_arrow="off",
        help="Chance de o modelo dar nota maior a uma empresa que quebrou do que a uma que não quebrou.",
    )
    k2.metric(
        "Precisão média",
        d.br(modelo["precisao_media"], 3),
        f"{modelo['precisao_media'] / avaliacao['taxa_base']:.1f}× o acaso".replace(".", ","),
        delta_color="off",
        delta_arrow="off",
    )
    k3.metric(
        "Acerto entre os 10% mais arriscados",
        f"{d.br(modelo['recall_top10'] * 100, 0)}%",
        "acaso: 10%",
        delta_color="off",
        delta_arrow="off",
    )
    k4.metric(
        "Empresas com evento no histórico",
        avaliacao["empresas_com_evento"],
        "base de aprendizado",
        delta_color="off",
        delta_arrow="off",
    )

    riscos = d.risco_atual()
    setor_risco = st.selectbox(
        "Filtrar setor", ["Todos", *sorted(riscos["setor"].dropna().unique())], key="setor_risco"
    )
    if setor_risco != "Todos":
        riscos = riscos[riscos["setor"] == setor_risco]

    fig = go.Figure()
    for zona in ["segura", "cinzenta", "perigo"]:
        parte = riscos[riscos["zona_altman"] == zona]
        fig.add_trace(
            go.Scatter(
                x=parte["z_altman"].clip(-10, 20),
                y=parte["percentil"] * 100,
                mode="markers",
                marker={"color": STATUS[zona], "size": 9, "line": {"width": 1, "color": "white"}, "opacity": 0.85},
                name=NOMES_ZONA[zona],
                customdata=parte[["nome_empresa", "setor", "ano"]].to_numpy(),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · balanço %{customdata[2]}"
                "<br>Z'' de Altman: %{x:.2f}<br>Percentil de risco: %{y:.0f}<extra></extra>",
            )
        )
    fig.add_vline(x=1.1, line={"color": CINZA, "dash": "dot", "width": 1})
    fig.add_vline(x=2.6, line={"color": CINZA, "dash": "dot", "width": 1})
    fig.update_layout(
        title={"text": "Modelo × Z'' de Altman (cada ponto é uma empresa)", "font": {"size": 15}},
        xaxis_title="Z'' de Altman (limitado entre -10 e 20)",
        yaxis_title="Percentil de risco do modelo",
    )
    evento = st.plotly_chart(
        layout(fig, altura=440).update_layout(hovermode="closest"),
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="grafico_risco",
    )
    st.caption(
        "Canto superior esquerdo: o modelo e o Altman concordam no alerta. Pontos altos à direita: o modelo vê risco "
        "que o Altman não vê. Clique num ponto para ver a empresa."
    )
    st.markdown("**As 25 notas mais altas** · clique numa linha (ou num ponto do gráfico) para ver a empresa")
    top_risco = riscos.head(25).reset_index(drop=True)
    tabela_risco = st.dataframe(
        top_risco[["nome_empresa", "setor", "ano", "percentil", "z_altman", "zona_altman", "situacao_emissor"]],
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tabela_risco",
        column_config={
            "nome_empresa": "Empresa",
            "setor": "Setor",
            "ano": st.column_config.NumberColumn("Balanço", format="%d"),
            "percentil": st.column_config.ProgressColumn("Percentil de risco", min_value=0, max_value=1, format="%.2f"),
            "z_altman": st.column_config.NumberColumn("Z'' de Altman", format="%.2f"),
            "zona_altman": "Zona Altman",
            "situacao_emissor": "Situação na CVM",
        },
    )
    pontos = evento.selection.points if evento and evento.selection else []
    linhas = tabela_risco.selection.rows if tabela_risco and tabela_risco.selection else []
    nome = pontos[0]["customdata"][0] if pontos else (top_risco.loc[linhas[0], "nome_empresa"] if linhas else None)
    if nome:
        st.subheader(nome.title())
        detalhe = d.series((nome,), max(inicio, 2015), fim)
        if detalhe.empty:
            st.info("Sem série consistente para essa empresa no período.")
        else:
            mini = st.columns(3)
            for coluna, m in zip(mini, ["margem_liquida", "liquidez_corrente", "divida_sobre_patrimonio"], strict=True):
                coluna.plotly_chart(grafico_evolucao(detalhe, pd.DataFrame(), m, [nome]), use_container_width=True)

    importancia = pd.DataFrame(avaliacao["importancia_sinais"]).head(8).iloc[::-1]
    fig = go.Figure(
        go.Bar(
            x=importancia["importancia"],
            y=importancia["sinal"].str.replace("_", " "),
            orientation="h",
            marker={"color": CORES_SERIES[0], "cornerradius": 4},
            hovertemplate="%{y}: %{x:.4f}<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": "Sinais que o modelo mais usa (queda na precisão sem o sinal)", "font": {"size": 15}}
    )
    st.plotly_chart(layout(fig, altura=320).update_layout(hovermode="closest"), use_container_width=True)

# ---------- Pergunte à IA ----------
with aba_ia:
    load_dotenv(d.RAIZ / ".env")
    st.subheader("Pergunte aos balanços")
    st.caption(
        "O agente (Claude Opus 5.5) não calcula nada sozinho: ele escolhe a consulta, e o número vem da camada "
        "semântica, com a regra de cada métrica."
    )
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.info("Para ativar o agente, coloque ANTHROPIC_API_KEY no arquivo .env do projeto e recarregue a página.")
    else:
        from agent.agente import perguntar

        st.session_state.setdefault("conversa", [])
        exemplos = st.columns(3)
        sugestoes = [
            "Qual a alíquota efetiva de IR e CSLL da Ambev em 2025?",
            "No setor de alimentos, quem teve a maior margem líquida em 2025?",
            "Como evoluiu a margem líquida da WEG de 2021 a 2025?",
        ]
        pergunta_exemplo = None
        for coluna, sugestao in zip(exemplos, sugestoes, strict=True):
            if coluna.button(sugestao, use_container_width=True):
                pergunta_exemplo = sugestao
        for mensagem in st.session_state["conversa"]:
            with st.chat_message(mensagem["papel"]):
                st.markdown(mensagem["texto"])
        pergunta = st.chat_input("Pergunte sobre receita, margens, alíquota efetiva, liquidez, endividamento...")
        pergunta = pergunta or pergunta_exemplo
        if pergunta:
            st.session_state["conversa"].append({"papel": "user", "texto": pergunta})
            with st.chat_message("user"):
                st.markdown(pergunta)
            with st.chat_message("assistant"), st.spinner("Consultando a camada semântica..."):
                resposta = perguntar(pergunta)
                st.markdown(resposta.texto)
                with st.expander(
                    f"Como a resposta foi montada · {len(resposta.chamadas)} consultas · US$ {resposta.custo_usd:.3f}"
                ):
                    st.json(resposta.chamadas)
            st.session_state["conversa"].append({"papel": "assistant", "texto": resposta.texto})

# ---------- Dados e método ----------
with aba_metodo:
    st.subheader("Como os dados chegam até aqui")
    st.graphviz_chart(
        """
        digraph {
          rankdir=LR; node [shape=box, style="rounded", fontname="Helvetica", fontsize=11];
          cvm [label="CVM\\nDFP, ITR, cadastro"]; raw [label="raw\\ncomo veio"];
          stg [label="staging\\ntipos e reais"]; inter [label="intermediate\\nsem duplicatas\\nconsolidado primeiro"];
          marts [label="marts\\ntabelas finais\\nauditoria de totais"];
          sem [label="camada semântica\\nMetricFlow · regras"];
          ml [label="modelo de risco\\nwalk-forward"]; dash [label="este painel"]; ia [label="agente de IA"];
          cvm -> raw [label=" Python"]; raw -> stg -> inter -> marts [label=" dbt"];
          marts -> sem; marts -> ml; sem -> dash; sem -> ia; ml -> dash;
        }
        """
    )
    q = d.qualidade()
    a, b, c, e = st.columns(4)
    a.metric("Linhas na origem", f"{d.br(q['linhas_raw'] / 1e6)} mi")
    b.metric("Balanços anuais (empresas comuns)", d.br(q["documentos"], 0))
    c.metric(
        "Com totais inconsistentes", q["inconsistentes"], "fora das métricas", delta_color="off", delta_arrow="off"
    )
    e.metric("Exceções investigadas à mão", q["excecoes"])
    if q["ultima_carga"]:
        st.caption(f"Última carga da CVM: {q['ultima_carga']:%d/%m/%Y %H:%M}")

    st.subheader("Avaliação do modelo de risco")
    linhas = [
        {
            "Régua": nome.replace("_", " "),
            "AUC": m["auc"],
            "IC 95% da AUC": f"{m['auc_ic95'][0]:.2f} a {m['auc_ic95'][1]:.2f}",
            "Precisão média": m["precisao_media"],
            "Acerto no top 10%": "n/a" if m["recall_top10"] is None else f"{m['recall_top10']:.0%}",
        }
        for nome, m in avaliacao["modelos"].items()
    ]
    st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)
    st.caption(
        f"Validação walk-forward {avaliacao['anos'][0]}–{avaliacao['anos'][1]}: {d.br(avaliacao['linhas'], 0)} "
        f"balanços, {avaliacao['casos_reais']} com evento em até 24 meses "
        f"({avaliacao['empresas_com_evento']} empresas). "
        f"Taxa base: {avaliacao['taxa_base']:.2%}."
    )
    st.subheader("Limites conhecidos")
    st.markdown(
        """
- Bancos e seguradoras ficam de fora das métricas (plano de contas diferente).
- Os balanços trimestrais (ITR) já estão no banco, mas ainda não entram nas métricas.
- O cadastro da CVM guarda só a situação **atual** da empresa; o nome nos documentos também é o atual.
- JBS S.A. e JBS N.V. aparecem como empresas separadas com a mesma receita (mudança de sede).
- Margens acima de 100% podem ser reais (ganhos não operacionais, como venda de ativos).
"""
    )
