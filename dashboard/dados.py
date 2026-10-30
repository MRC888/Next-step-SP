"""Camada de dados do dashboard: consultas com cache e formatação no padrão brasileiro.

Toda métrica vem de agent/ferramentas.py, ou seja, da camada semântica (MetricFlow): o painel, o agente e as
consultas usam a mesma regra de cálculo. O cache evita repetir consultas (cada uma leva ~2 s).
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from agent import ferramentas  # noqa: E402

ULTIMO_ANO = 2025
RECEITA_MINIMA_PADRAO = 1e8  # R$ 100 mi: tira holdings com receita quase zero, que distorcem razões

# Métricas agrupadas por finalidade, como em painéis de análise de pares
GRUPOS = {
    "Tamanho": ["receita_liquida", "lucro_liquido"],
    "Rentabilidade": ["margem_bruta", "margem_operacional", "margem_liquida", "roe"],
    "Tributos": ["aliquota_efetiva_ir_csll"],
    "Liquidez e endividamento": ["liquidez_corrente", "divida_sobre_patrimonio"],
}
METRICAS = [m for grupo in GRUPOS.values() for m in grupo]
PERCENTUAIS = {"margem_bruta", "margem_operacional", "margem_liquida", "aliquota_efetiva_ir_csll", "roe"}
EM_REAIS = {"receita_liquida", "lucro_liquido"}


# ---------- Formatação ----------
def br(numero: float, casas: int = 1) -> str:
    return f"{numero:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar(metrica: str, valor) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    if metrica in PERCENTUAIS:
        return f"{br(valor * 100)}%"
    if metrica in EM_REAIS:
        return f"R$ {br(valor / 1e9)} bi" if abs(valor) >= 1e9 else f"R$ {br(valor / 1e6)} mi"
    return br(valor, 2)


def formato_eixo(metrica: str) -> str:
    """Formato do eixo no Plotly (d3-format)."""
    if metrica in PERCENTUAIS:
        return ".0%"
    return ".2f"


# ---------- Consultas ----------
@st.cache_data(ttl=3600, show_spinner=False)
def catalogo() -> dict:
    return {m["nome"]: m for m in ferramentas.listar_metricas()}


def rotulo(metrica: str) -> str:
    return catalogo()[metrica]["rotulo"]


def regra(metrica: str) -> str:
    return catalogo()[metrica]["regra"]


@st.cache_data(ttl=3600, show_spinner=False)
def buscar(termo: str) -> list[dict]:
    return ferramentas.buscar_empresas(termo, limite=20)


@st.cache_data(ttl=3600, show_spinner=False)
def setores() -> list[str]:
    return ferramentas.listar_setores()


@st.cache_data(ttl=3600, show_spinner=False)
def setor_da_empresa(empresa: str) -> str | None:
    achadas = [e for e in ferramentas.buscar_empresas(empresa, limite=20) if e["nome_oficial"] == empresa]
    return achadas[0]["setor"] if achadas else None


@st.cache_data(ttl=3600, show_spinner="Consultando a camada semântica...")
def series(empresas: tuple[str, ...], inicio: int, fim: int) -> pd.DataFrame:
    """Todas as métricas, por ano e empresa."""
    linhas = ferramentas.consultar_metricas(
        METRICAS, inicio, fim, empresas=list(empresas), agrupar_por=["ano", "empresa"], limite=5000
    )
    return pd.DataFrame(linhas)


@st.cache_data(ttl=3600, show_spinner="Calculando a referência do setor...")
def referencia_setor(setor: str, inicio: int, fim: int, receita_minima: float) -> pd.DataFrame:
    """Mediana e quartis do setor por ano (a referência típica em análise de pares)."""
    linhas = ferramentas.consultar_metricas(
        METRICAS,
        inicio,
        fim,
        setor=setor,
        agrupar_por=["ano", "empresa"],
        limite=10000,
        receita_minima=receita_minima,
    )
    dados = pd.DataFrame(linhas)
    if dados.empty:
        return dados
    agregado = dados.groupby("ano")[METRICAS].quantile([0.25, 0.5, 0.75]).unstack()
    agregado.columns = [f"{metrica}__p{int(q * 100)}" for metrica, q in agregado.columns]
    agregado["empresas"] = dados.groupby("ano")["empresa"].nunique()
    return agregado.reset_index()


@st.cache_data(ttl=3600, show_spinner="Montando o ranking...")
def ranking(metrica: str, ano: int, setor: str | None, receita_minima: float) -> pd.DataFrame:
    metricas = [metrica] if metrica == "receita_liquida" else [metrica, "receita_liquida"]
    linhas = ferramentas.consultar_metricas(
        metricas,
        ano,
        ano,
        setor=setor,
        agrupar_por=["empresa"],
        ordenar_por=metrica,
        limite=25,
        receita_minima=receita_minima,
    )
    return pd.DataFrame(linhas).dropna(subset=[metrica]) if linhas else pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def risco_atual() -> pd.DataFrame:
    with ferramentas._conectar() as conn:
        cursor = conn.execute(
            """select r.nome_empresa, r.setor, r.ano, r.nota_risco, r.percentil, r.z_altman, r.zona_altman,
                      d.situacao_emissor
               from ml.risco_atual as r
               left join marts.dim_empresa as d on r.cnpj = d.cnpj
               order by r.nota_risco desc"""
        )
        return pd.DataFrame(cursor.fetchall(), columns=[c.name for c in cursor.description])


@st.cache_data(ttl=600, show_spinner=False)
def avaliacao_modelo() -> dict:
    return json.loads((RAIZ / "ml" / "resultados" / "metricas.json").read_text(encoding="utf-8"))


@st.cache_data(ttl=600, show_spinner=False)
def qualidade() -> dict:
    with ferramentas._conectar() as conn:
        documentos, inconsistentes, empresas = conn.execute(
            """select count(*), count(*) filter (where not dados_consistentes), count(distinct cnpj)
               from marts.fct_contas_anuais"""
        ).fetchone()
        excecoes = conn.execute("select count(*) from seeds.excecoes_conhecidas").fetchone()[0]
        linhas_raw = conn.execute("select coalesce(sum(linhas), 0) from raw._controle_cargas").fetchone()[0]
        ultima_carga = conn.execute("select max(carregado_em) from raw._controle_cargas").fetchone()[0]
    return {
        "documentos": documentos,
        "inconsistentes": inconsistentes,
        "empresas": empresas,
        "excecoes": excecoes,
        "linhas_raw": int(linhas_raw),
        "ultima_carga": ultima_carga,
    }
