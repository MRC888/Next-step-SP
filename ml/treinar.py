"""Modelo de risco de dificuldade financeira (Marco D).

Pergunta de negócio: dado o balanço anual que a empresa acabou de publicar, qual a chance de ela entrar em
recuperação judicial, falência ou liquidação nos próximos 24 meses?

Avaliação walk-forward (sem ver o futuro): para cada ano A, os modelos treinam só com balanços cujo desfecho
(janela de 24 meses) já era conhecido antes do primeiro balanço de A ser publicado, e preveem os balanços de A.
As previsões de todos os anos são juntadas e avaliadas de uma vez, o que aproveita todos os casos reais.

Comparações: Z'' de Altman (referência da literatura), "patrimônio negativo" e "teve prejuízo".

Rode (na raiz do projeto): python -m ml.treinar
Saídas: ml/resultados/metricas.json, ml/resultados/modelo.joblib e a tabela ml.risco_atual no banco.
"""

import json
import os
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import psycopg
from dotenv import load_dotenv
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "ml" / "resultados"
HORIZONTE_MESES = 24  # igual à var horizonte_risco_meses do dbt
PRIMEIRO_ANO_TESTE = 2013  # antes disso há poucos anos de histórico para treinar
SEMENTE = 42

SINAIS = [
    "x1_capital_de_giro_sobre_ativo",
    "x2_lucros_retidos_sobre_ativo",
    "x3_ebit_sobre_ativo",
    "x4_patrimonio_sobre_passivo",
    "liquidez_corrente",
    "divida_sobre_ativo",
    "roa",
    "margem_liquida",
    "crescimento_receita",
    "log_ativo",
    "patrimonio_negativo",
    "teve_prejuizo",
]


def _conectar():
    load_dotenv(RAIZ / ".env")
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        user=os.getenv("POSTGRES_USER", "sp_data"),
        password=os.getenv("POSTGRES_PASSWORD") or None,
        dbname=os.getenv("POSTGRES_DB", "sp_data"),
    )


def carregar() -> pd.DataFrame:
    with _conectar() as conn:
        cursor = conn.execute("select * from marts.fct_risco_features")
        colunas = [c.name for c in cursor.description]
        dados = pd.DataFrame(cursor.fetchall(), columns=colunas)
    for coluna in [*SINAIS, "z_altman"]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce").astype(float)
    dados["dt_entrega"] = pd.to_datetime(dados["dt_entrega"])
    dados["fim_janela"] = dados["dt_entrega"] + pd.DateOffset(months=HORIZONTE_MESES)
    return dados


def _limitar_extremos(x: np.ndarray) -> np.ndarray:
    """Razões contábeis têm valores absurdos (holding com receita quase zero); corta no intervalo [-10, 10]."""
    return np.clip(x, -10, 10)


def modelos() -> dict:
    """Configurações simples e fixas: sem ajuste fino no teste (seria uma forma de colar)."""
    preparo = [SimpleImputer(strategy="median"), FunctionTransformer(_limitar_extremos)]
    return {
        "regressao_logistica": make_pipeline(
            *preparo,
            StandardScaler(),
            LogisticRegression(class_weight="balanced", C=0.5, max_iter=2000),
        ),
        "gradient_boosting": make_pipeline(
            *preparo,
            HistGradientBoostingClassifier(
                max_depth=3, learning_rate=0.05, max_iter=200, class_weight="balanced", random_state=SEMENTE
            ),
        ),
    }


def walk_forward(dados: pd.DataFrame) -> pd.DataFrame:
    """Previsões fora da amostra: cada ano é previsto por modelos que só conheciam o passado."""
    completos = dados[dados["janela_completa"]]
    previsoes = []
    for ano in range(PRIMEIRO_ANO_TESTE, int(completos["ano"].max()) + 1):
        teste = completos[completos["ano"] == ano]
        if teste.empty:
            continue
        # Só entra no treino o que já tinha desfecho conhecido antes do primeiro balanço do ano de teste sair
        treino = completos[completos["fim_janela"] < teste["dt_entrega"].min()]
        if treino["alvo"].sum() < 3:
            continue
        resultado = teste[["cnpj", "nome_empresa", "ano", "alvo", "z_altman", "patrimonio_negativo", "teve_prejuizo"]]
        resultado = resultado.copy()
        for nome, modelo in modelos().items():
            modelo.fit(treino[SINAIS], treino["alvo"])
            resultado[nome] = modelo.predict_proba(teste[SINAIS])[:, 1]
        previsoes.append(resultado)
    return pd.concat(previsoes, ignore_index=True)


def _metricas(alvo: np.ndarray, nota: np.ndarray) -> dict:
    """AUC, precisão média e recall entre os 10% de maior risco.

    O recall no top 10% só vale para notas contínuas: numa régua de sim/não (ex.: teve prejuízo), os empates
    no corte jogam bem mais de 10% das empresas no "top", e o número fica inflado. Nesses casos fica vazio.
    """
    top10 = None
    if len(np.unique(nota)) > 2:
        selecionados = np.argsort(-nota, kind="stable")[: max(1, round(len(nota) * 0.10))]
        top10 = round(float(alvo[selecionados].sum() / alvo.sum()), 3)
    return {
        "auc": round(float(roc_auc_score(alvo, nota)), 3),
        "precisao_media": round(float(average_precision_score(alvo, nota)), 3),
        "recall_top10": top10,
    }


def _intervalo(alvo: np.ndarray, nota: np.ndarray, n: int = 1000) -> list[float]:
    """Intervalo de 95% da AUC por bootstrap: com poucos casos, a incerteza tem de aparecer."""
    gerador = np.random.default_rng(SEMENTE)
    aucs = []
    for _ in range(n):
        indices = gerador.integers(0, len(alvo), len(alvo))
        if alvo[indices].sum() in (0, len(indices)):
            continue
        aucs.append(roc_auc_score(alvo[indices], nota[indices]))
    return [round(float(np.percentile(aucs, 2.5)), 3), round(float(np.percentile(aucs, 97.5)), 3)]


def avaliar(previsoes: pd.DataFrame) -> dict:
    alvo = previsoes["alvo"].to_numpy()
    notas = {
        "z_altman": -previsoes["z_altman"].fillna(previsoes["z_altman"].median()).to_numpy(),  # Z baixo = risco
        "patrimonio_negativo": previsoes["patrimonio_negativo"].to_numpy(),
        "teve_prejuizo": previsoes["teve_prejuizo"].to_numpy(),
        "regressao_logistica": previsoes["regressao_logistica"].to_numpy(),
        "gradient_boosting": previsoes["gradient_boosting"].to_numpy(),
    }
    return {
        "linhas": int(len(alvo)),
        "casos_reais": int(alvo.sum()),
        "empresas_com_evento": int(previsoes.loc[previsoes["alvo"] == 1, "cnpj"].nunique()),
        "taxa_base": round(float(alvo.mean()), 4),
        "anos": [int(previsoes["ano"].min()), int(previsoes["ano"].max())],
        "modelos": {
            nome: {**_metricas(alvo, nota), "auc_ic95": _intervalo(alvo, nota)} for nome, nota in notas.items()
        },
    }


def treinar_final(dados: pd.DataFrame, nome: str):
    """Treina o modelo escolhido com todo o histórico de desfecho conhecido."""
    completos = dados[dados["janela_completa"]]
    modelo = modelos()[nome]
    modelo.fit(completos[SINAIS], completos["alvo"])
    importancia = permutation_importance(
        modelo,
        completos[SINAIS],
        completos["alvo"],
        scoring="average_precision",
        n_repeats=10,
        random_state=SEMENTE,
    )
    pesos = sorted(zip(SINAIS, importancia.importances_mean, strict=True), key=lambda par: par[1], reverse=True)
    return modelo, [{"sinal": s, "importancia": round(float(v), 4)} for s, v in pesos]


def gravar_risco_atual(dados: pd.DataFrame, modelo, nome: str):
    """Nota de risco do balanço mais recente de cada empresa (ainda sem desfecho conhecido)."""
    atuais = dados.sort_values("dt_entrega").groupby("cnpj").tail(1)
    atuais = atuais[atuais["ano"] >= date.today().year - 2].copy()
    # Nota relativa, não probabilidade calibrada: o peso extra dado aos casos raros (class_weight) infla os valores.
    # Para comunicar, use o percentil ("entre as X% mais arriscadas").
    atuais["nota_risco"] = modelo.predict_proba(atuais[SINAIS])[:, 1]
    atuais["percentil"] = atuais["nota_risco"].rank(pct=True)
    atuais["zona_altman"] = pd.cut(
        atuais["z_altman"], [-np.inf, 1.1, 2.6, np.inf], labels=["perigo", "cinzenta", "segura"]
    ).astype(str)
    colunas = ["cnpj", "nome_empresa", "setor", "ano", "nota_risco", "percentil", "z_altman", "zona_altman"]
    with _conectar() as conn:
        conn.execute("create schema if not exists ml")
        conn.execute("drop table if exists ml.risco_atual")
        conn.execute(
            """create table ml.risco_atual (
                cnpj text primary key, nome_empresa text, setor text, ano int,
                nota_risco double precision, percentil double precision,
                z_altman double precision, zona_altman text, modelo text, gerado_em date)"""
        )
        with conn.cursor().copy(
            "copy ml.risco_atual (cnpj, nome_empresa, setor, ano, nota_risco, percentil, z_altman, zona_altman,"
            " modelo, gerado_em) from stdin"
        ) as cp:
            for linha in atuais[colunas].itertuples(index=False):
                valores = [None if pd.isna(v) else v for v in linha]
                cp.write_row((*valores, nome, date.today()))
    return len(atuais)


def main():
    dados = carregar()
    previsoes = walk_forward(dados)
    metricas = avaliar(previsoes)

    # Escolha pela precisão média (a métrica certa quando os casos são raros), entre os modelos treinados
    escolhido = max(
        ["regressao_logistica", "gradient_boosting"], key=lambda m: metricas["modelos"][m]["precisao_media"]
    )
    modelo, importancia = treinar_final(dados, escolhido)
    empresas = gravar_risco_atual(dados, modelo, escolhido)

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, RESULTADOS / "modelo.joblib")
    metricas.update(
        {
            "modelo_escolhido": escolhido,
            "importancia_sinais": importancia,
            "empresas_pontuadas": empresas,
            "horizonte_meses": HORIZONTE_MESES,
        }
    )
    (RESULTADOS / "metricas.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    previsoes.to_csv(RESULTADOS / "previsoes_walk_forward.csv", index=False)

    print(
        f"Walk-forward {metricas['anos']}: {metricas['linhas']} balanços, {metricas['casos_reais']} balanços com"
        f" evento nos 24 meses seguintes ({metricas['empresas_com_evento']} empresas)"
    )
    print(f"Taxa base (chute): {metricas['taxa_base']:.2%}\n")
    print(f"{'régua':<22}{'AUC':>7}{'IC 95%':>16}{'prec. média':>13}{'recall top10%':>15}")
    for nome, m in metricas["modelos"].items():
        ic = f"[{m['auc_ic95'][0]:.2f}, {m['auc_ic95'][1]:.2f}]"
        top10 = "n/a" if m["recall_top10"] is None else f"{m['recall_top10']:.0%}"
        print(f"{nome:<22}{m['auc']:>7.3f}{ic:>16}{m['precisao_media']:>13.3f}{top10:>15}")
    print(f"\nEscolhido: {escolhido}. Sinais mais importantes: {[i['sinal'] for i in importancia[:4]]}")
    print(f"Risco atual gravado em ml.risco_atual: {empresas} empresas")


if __name__ == "__main__":
    main()
