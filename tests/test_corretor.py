"""O corretor da prova do agente lê números no padrão brasileiro e reprova respostas erradas ou inventadas."""

import json

import pytest

from agent.avaliacao.avaliar import RAIZ_AVALIACAO, corrigir, numeros_no_texto

QUESTOES = {q["id"]: q for q in json.loads((RAIZ_AVALIACAO / "perguntas.json").read_text(encoding="utf-8"))}


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("16,6%", (0.166, "percentual")),
        ("R$ 40,8 bilhões", (40.8e9, "reais")),
        ("R$ 979,1 milhões", (979.1e6, "reais")),
        ("1.234,5 mil", (1234.5e3, "reais")),
        ("0,96", (0.96, "vezes")),
    ],
)
def test_le_numeros_no_padrao_brasileiro(texto, esperado):
    valor, tipo = numeros_no_texto(texto)[0]
    assert tipo == esperado[1]
    assert valor == pytest.approx(esperado[0])


@pytest.mark.parametrize(
    ("questao", "resposta", "deve_acertar"),
    [
        (1, "A receita líquida da WEG em 2025 foi de R$ 40,8 bilhões.", True),
        (3, "A margem líquida foi de 16,6%.", True),
        (3, "A margem líquida foi de 18%.", False),
        (6, "A liquidez corrente foi de 0,96.", True),
        (10, "Teve prejuízo de R$ 979,1 milhões.", True),
        (10, "Teve lucro de R$ 979 milhões.", False),
        (11, "20,1% em 2024 e 16,8% em 2025.", True),
        (13, "A Petrobras liderou.", True),
        (17, "O Itaú Unibanco é um banco e não está nas métricas.", True),
        (17, "Banco: margem de 25%.", False),
        (18, "Não se aplica: houve prejuízo antes dos tributos.", True),
        (18, "A alíquota foi 52,6%, com prejuízo.", False),
        (19, "A Padaria do Zé S.A. não está na base.", True),
        (20, "O documento de 2022 tem totais inconsistentes e ficou de fora.", True),
    ],
)
def test_corretor(questao, resposta, deve_acertar):
    acertou, _ = corrigir(QUESTOES[questao], resposta)
    assert acertou is deve_acertar
