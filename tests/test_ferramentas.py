"""As ferramentas do agente validam a entrada antes de consultar e se defendem de injeção."""

import pytest

from agent import ferramentas


def test_literal_dobra_aspas():
    assert ferramentas._literal("D'Ávila S.A.") == "'D''Ávila S.A.'"


@pytest.mark.parametrize("texto", ["WEG {{ x }}", "linha\nquebrada", "\x00"])
def test_literal_rejeita_caracteres_perigosos(texto):
    with pytest.raises(ValueError):
        ferramentas._literal(texto)


def test_rejeita_metrica_inexistente():
    with pytest.raises(ValueError, match="Métricas inválidas"):
        ferramentas.consultar_metricas(["x'; drop table"], 2025, 2025)


@pytest.mark.parametrize(("inicio", "fim"), [(2009, 2025), (2025, 2024), (2025, 2030)])
def test_rejeita_anos_invalidos(inicio, fim):
    with pytest.raises(ValueError, match="Anos"):
        ferramentas.consultar_metricas(["receita_liquida"], inicio, fim)


def test_rejeita_agrupamento_invalido():
    with pytest.raises(ValueError, match="agrupar_por"):
        ferramentas.consultar_metricas(["receita_liquida"], 2025, 2025, agrupar_por=["cnpj"])


def test_rejeita_varios_anos_sem_agrupar_por_ano():
    with pytest.raises(ValueError, match="único ano"):
        ferramentas.consultar_metricas(["receita_liquida"], 2021, 2025, agrupar_por=["empresa"])


def test_limpa_linha_do_metricflow():
    linha = {"metric_time__year": "2025-01-01T00:00:00", "documento__nome_empresa": "WEG S.A.", "roe": "0.36", "x": ""}
    assert ferramentas._limpar_linha(linha, ["roe"]) == {"ano": 2025, "empresa": "WEG S.A.", "roe": 0.36}


@pytest.mark.banco
def test_busca_empresa_pelo_nome():
    achadas = ferramentas.buscar_empresas("weg")
    assert achadas[0]["nome_oficial"] == "WEG S.A."


@pytest.mark.banco
def test_receita_da_weg_2025():
    linha = ferramentas.consultar_metricas(["receita_liquida"], 2025, 2025, empresas=["WEG S.A."])[0]
    assert linha["receita_liquida"] == pytest.approx(40_804_110_000)


@pytest.mark.banco
def test_aliquota_vazia_com_prejuizo():
    linha = ferramentas.consultar_metricas(["aliquota_efetiva_ir_csll"], 2023, 2023, empresas=["MAGAZINE LUIZA S.A."])[
        0
    ]
    assert linha["aliquota_efetiva_ir_csll"] is None
