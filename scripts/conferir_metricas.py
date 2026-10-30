"""Confere as métricas do MetricFlow contra um cálculo independente, feito direto do raw (dados como vieram da CVM).

Os dois caminhos não compartilham código: aqui as contas são lidas do schema raw, com a escala aplicada à mão,
e as fórmulas são escritas em Python. Se os dois chegarem ao mesmo número, a regra de negócio está certa.

Rode (na raiz do projeto, com o banco no ar): python scripts/conferir_metricas.py
"""

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parent.parent
MF = Path(sys.executable).parent / "mf"
TOLERANCIA = 1e-6  # diferença relativa aceita (só arredondamento)

# Empresa (nome exato na CVM) e ano. Magazine Luiza 2023 testa prejuízo (números negativos).
CASOS = [("WEG S.A.", 2025), ("AMBEV S.A.", 2025), ("MAGAZINE LUIZA S.A.", 2023)]

METRICAS = [
    "receita_liquida",
    "lucro_bruto",
    "lucro_liquido",
    "margem_bruta",
    "margem_operacional",
    "margem_liquida",
    "aliquota_efetiva_ir_csll",
    "liquidez_corrente",
    "divida_sobre_patrimonio",
    "roe",
]

CONTAS = {
    "dre": ["3.01", "3.03", "3.05", "3.07", "3.08", "3.11"],
    "bpa": ["1.01"],
    "bpp": ["2.01", "2.03", "2.01.04", "2.02.01"],
}


def contas_do_raw(conn, empresa, ano):
    """Lê as contas do raw: consolidado, exercício atual, versão mais recente, valores convertidos para reais."""
    valores = {}
    for demonstracao, codigos in CONTAS.items():
        linhas = conn.execute(
            f"""
            select cd_conta, vl_conta::numeric * case when escala_moeda = 'MIL' then 1000 else 1 end
            from raw.dfp_{demonstracao}_con
            where denom_cia = %s and dt_refer = %s and ordem_exerc = 'ÚLTIMO' and cd_conta = any(%s)
              and versao = (
                  select max(versao) from raw.dfp_{demonstracao}_con where denom_cia = %s and dt_refer = %s
              )
            """,
            (empresa, f"{ano}-12-31", codigos, empresa, f"{ano}-12-31"),
        ).fetchall()
        valores.update({conta: float(valor) for conta, valor in linhas})
    return valores


def calculo_manual(c):
    """As mesmas regras da camada semântica, escritas à mão a partir dos códigos de conta."""
    divida = c["2.01.04"] + c["2.02.01"]
    return {
        "receita_liquida": c["3.01"],
        "lucro_bruto": c["3.03"],
        "lucro_liquido": c["3.11"],
        "margem_bruta": c["3.03"] / c["3.01"],
        "margem_operacional": c["3.05"] / c["3.01"],
        "margem_liquida": c["3.11"] / c["3.01"],
        # Regra de negócio: só com lucro antes dos tributos positivo; com prejuízo, fica vazia
        "aliquota_efetiva_ir_csll": -c["3.08"] / c["3.07"] if c["3.07"] > 0 else None,
        "liquidez_corrente": c["1.01"] / c["2.01"],
        "divida_sobre_patrimonio": divida / c["2.03"],
        "roe": c["3.11"] / c["2.03"],
    }


def calculo_metricflow(empresa, ano):
    """Pede as métricas ao MetricFlow (mf query) e lê o resultado em CSV."""
    with tempfile.NamedTemporaryFile(suffix=".csv") as saida:
        subprocess.run(
            [
                str(MF),
                "query",
                "--metrics",
                ",".join(METRICAS),
                "--group-by",
                "metric_time__year",
                "--where",
                f"{{{{ Dimension('documento__nome_empresa') }}}} = '{empresa}'",
                "--start-time",
                f"{ano}-01-01",
                "--end-time",
                f"{ano}-12-31",
                "--csv",
                saida.name,
            ],
            cwd=RAIZ / "modeling",
            check=True,
            capture_output=True,
        )
        with open(saida.name, encoding="utf-8") as f:
            linha = next(csv.DictReader(f))
    return {m: float(linha[m]) if linha[m] else None for m in METRICAS}


def _iguais(a, b):
    """Iguais dentro da tolerância; dois vazios (métrica sem sentido no ano) também contam como iguais."""
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) / max(abs(a), 1e-9) <= TOLERANCIA


def _fmt(valor):
    return f"{'vazio':>18}" if valor is None else f"{valor:>18,.4f}"


def main():
    falhas = 0
    with psycopg.connect("host=localhost port=5433 user=sp_data dbname=sp_data") as conn:
        for empresa, ano in CASOS:
            manual = calculo_manual(contas_do_raw(conn, empresa, ano))
            mf = calculo_metricflow(empresa, ano)
            print(f"\n{empresa} {ano}")
            for m in METRICAS:
                ok = _iguais(manual[m], mf[m])
                falhas += not ok
                print(f"  {'OK  ' if ok else 'FALHA'} {m:<26} manual={_fmt(manual[m])}  metricflow={_fmt(mf[m])}")
    print(f"\n{len(CASOS) * len(METRICAS) - falhas} de {len(CASOS) * len(METRICAS)} conferências OK")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
