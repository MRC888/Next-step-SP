"""Ferramentas que o agente de IA pode usar. Funcionam sozinhas, sem IA (dá para testar e reutilizar no dashboard).

Regra de ouro: todo número que o agente responde vem daqui, ou seja, da camada semântica (MetricFlow).
A IA escolhe QUAL pergunta fazer; o cálculo é sempre o das regras de negócio.
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
MODELAGEM = RAIZ / "modeling"
MANIFESTO = MODELAGEM / "target" / "semantic_manifest.json"
MF = Path(sys.executable).parent / "mf"

ANO_MIN, ANO_MAX = 2010, 2026
LIMITE_MAXIMO = 10_000  # o agente limita a 50 linhas (agent/agente.py); o dashboard precisa de mais

# Métricas de apoio existem só para compor as razões; o agente não as oferece como resposta principal.
METRICAS_DE_APOIO = {"lucro_antes_ir_positivo", "despesa_ir_csll_com_lucro"}

AGRUPAMENTOS = {
    "ano": "metric_time__year",
    "empresa": "documento__nome_empresa",
    "setor": "empresa__setor",
}


def _conectar():
    load_dotenv(RAIZ / ".env")
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        user=os.getenv("POSTGRES_USER", "sp_data"),
        password=os.getenv("POSTGRES_PASSWORD") or None,  # vazio: usa o ~/.pgpass
        dbname=os.getenv("POSTGRES_DB", "sp_data"),
    )


def _catalogo():
    """Lê as métricas do manifesto que o dbt gera a partir de models/semantic/_semantic.yml."""
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    return {
        m["name"]: {"nome": m["name"], "rotulo": m.get("label") or m["name"], "regra": m.get("description") or ""}
        for m in manifesto["metrics"]
        if m["name"] not in METRICAS_DE_APOIO
    }


def listar_metricas() -> list[dict]:
    """Lista as métricas disponíveis: nome técnico, rótulo e a regra de cálculo em português."""
    return sorted(_catalogo().values(), key=lambda m: m["nome"])


def buscar_empresas(termo: str, limite: int = 10) -> list[dict]:
    """Procura empresas pelo nome (sem diferenciar maiúsculas/acentos parciais) e devolve o nome oficial.

    Só aparecem empresas comerciais e industriais com balanço anual na base (escopo da camada semântica).
    """
    termo = termo.strip()
    if not termo:
        return []
    with _conectar() as conn:
        linhas = conn.execute(
            """
            select f.nome_empresa, d.setor, min(f.ano) as primeiro_ano, max(f.ano) as ultimo_ano
            from marts.fct_contas_anuais as f
            left join marts.dim_empresa as d on f.cnpj = d.cnpj
            where f.nome_empresa ilike %s
            group by f.nome_empresa, d.setor
            order by max(f.ano) desc, f.nome_empresa
            limit %s
            """,
            (f"%{termo}%", min(limite, LIMITE_MAXIMO)),
        ).fetchall()
    return [{"nome_oficial": n, "setor": s, "primeiro_ano": a1, "ultimo_ano": a2} for n, s, a1, a2 in linhas]


def listar_setores() -> list[str]:
    """Lista os setores do cadastro da CVM que têm empresas na base."""
    with _conectar() as conn:
        linhas = conn.execute(
            """
            select distinct d.setor
            from marts.fct_contas_anuais as f
            inner join marts.dim_empresa as d on f.cnpj = d.cnpj
            where d.setor is not null
            order by 1
            """
        ).fetchall()
    return [s for (s,) in linhas]


def _literal(texto: str) -> str:
    """Texto seguro dentro do filtro do MetricFlow: rejeita caracteres de controle e dobra as aspas."""
    if re.search(r"[\x00-\x1f{}]", texto):
        raise ValueError(f"Texto inválido no filtro: {texto!r}")
    return "'" + texto.replace("'", "''") + "'"


def consultar_metricas(
    metricas: list[str],
    ano_inicio: int,
    ano_fim: int,
    empresas: list[str] | None = None,
    setor: str | None = None,
    agrupar_por: list[str] | None = None,
    ordenar_por: str | None = None,
    decrescente: bool = True,
    limite: int = 20,
    receita_minima: float | None = None,
) -> list[dict]:
    """Calcula métricas pela camada semântica (MetricFlow) e devolve uma linha por grupo.

    Args:
        metricas: nomes técnicos (ver listar_metricas).
        ano_inicio / ano_fim: anos do exercício (DFP), inclusive.
        empresas: nomes oficiais (ver buscar_empresas). Vazio = todas.
        setor: nome exato do setor (ver listar_setores). Vazio = todos.
        agrupar_por: combinação de "ano", "empresa", "setor". Padrão: ["ano", "empresa"].
        ordenar_por: uma das métricas pedidas, para rankings.
        decrescente: ordem do ranking.
        limite: máximo de linhas.
        receita_minima: só empresas-ano com receita líquida acima deste valor (R$). Evita razões absurdas
            de holdings com receita quase zero. O filtro é feito dentro do MetricFlow, antes do ranking.
    """
    catalogo = _catalogo()
    desconhecidas = [m for m in metricas if m not in catalogo]
    if not metricas or desconhecidas:
        raise ValueError(f"Métricas inválidas: {desconhecidas or 'nenhuma'}. Use listar_metricas.")
    if not (ANO_MIN <= ano_inicio <= ano_fim <= ANO_MAX):
        raise ValueError(f"Anos devem estar entre {ANO_MIN} e {ANO_MAX}, com início <= fim.")
    agrupar_por = agrupar_por or ["ano", "empresa"]
    if any(g not in AGRUPAMENTOS for g in agrupar_por):
        raise ValueError(f"agrupar_por aceita só {list(AGRUPAMENTOS)}.")
    if ordenar_por and ordenar_por not in metricas:
        raise ValueError("ordenar_por precisa ser uma das métricas pedidas.")

    filtros = []
    if empresas:
        nomes = ", ".join(_literal(e) for e in empresas)
        filtros.append(f"{{{{ Dimension('documento__nome_empresa') }}}} in ({nomes})")
    if setor:
        filtros.append(f"{{{{ Dimension('empresa__setor') }}}} = {_literal(setor)}")
    if receita_minima:
        filtros.append(f"{{{{ Metric('receita_liquida', group_by=['documento']) }}}} >= {float(receita_minima)}")

    comando = [
        str(MF),
        "query",
        "--metrics",
        ",".join(metricas),
        "--group-by",
        ",".join(AGRUPAMENTOS[g] for g in agrupar_por),
        "--start-time",
        f"{ano_inicio}-01-01",
        "--end-time",
        f"{ano_fim}-12-31",
        "--limit",
        str(min(max(limite, 1), LIMITE_MAXIMO)),
    ]
    for filtro in filtros:
        comando += ["--where", filtro]
    if ordenar_por:
        comando += ["--order", f"{'-' if decrescente else ''}{ordenar_por}"]
    elif "ano" in agrupar_por:
        comando += ["--order", "metric_time__year"]

    with tempfile.NamedTemporaryFile(suffix=".csv") as saida:
        processo = subprocess.run(
            [*comando, "--csv", saida.name], cwd=MODELAGEM, capture_output=True, text=True, check=False
        )
        if processo.returncode != 0:
            raise RuntimeError(f"MetricFlow falhou: {processo.stderr.strip()[-500:]}")
        with open(saida.name, encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))

    return [_limpar_linha(linha, metricas) for linha in linhas]


def _limpar_linha(linha: dict, metricas: list[str]) -> dict:
    """Troca os nomes técnicos das colunas por nomes curtos e converte números."""
    resultado = {}
    for coluna, valor in linha.items():
        if coluna == "metric_time__year":
            resultado["ano"] = int(valor[:4])
        elif coluna == "documento__nome_empresa":
            resultado["empresa"] = valor
        elif coluna == "empresa__setor":
            resultado["setor"] = valor
        elif coluna in metricas:
            resultado[coluna] = float(valor) if valor not in ("", None) else None
    return resultado
