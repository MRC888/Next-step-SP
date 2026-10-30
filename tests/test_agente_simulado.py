"""O agente de ponta a ponta com uma API simulada: sem custo e sem chave.

O "servidor falso" responde como o Claude: primeiro pede a ferramenta consultar_metricas, depois responde em texto.
Confere o formato da requisição, o ciclo de ferramentas, a resposta final e a contagem de tokens.
"""

import json

import anthropic
import httpx2
import pytest

from agent import agente, ferramentas


def _mensagem(conteudo, motivo, entrada=1000, saida=100):
    return {
        "id": "msg_teste",
        "type": "message",
        "role": "assistant",
        "model": agente.MODELO,
        "content": conteudo,
        "stop_reason": motivo,
        "stop_sequence": None,
        "usage": {"input_tokens": entrada, "output_tokens": saida},
    }


def test_agente_usa_a_ferramenta_e_responde(monkeypatch):
    requisicoes = []

    def servidor(request: httpx2.Request) -> httpx2.Response:
        corpo = json.loads(request.content)
        requisicoes.append(corpo)
        if len(requisicoes) == 1:
            pedido = {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "consultar_metricas",
                "input": {
                    "metricas": ["margem_liquida"],
                    "ano_inicio": 2025,
                    "ano_fim": 2025,
                    "empresas": ["WEG S.A."],
                },
            }
            return httpx2.Response(200, json=_mensagem([pedido], "tool_use"))
        texto = {"type": "text", "text": "A margem líquida da WEG em 2025 foi de 16,6%."}
        return httpx2.Response(200, json=_mensagem([texto], "end_turn", 1500, 50))

    # A ferramenta real chamaria o MetricFlow; aqui devolve um valor fixo
    monkeypatch.setattr(
        ferramentas,
        "consultar_metricas",
        lambda *a, **k: [{"ano": 2025, "empresa": "WEG S.A.", "margem_liquida": 0.166}],
    )
    cliente = anthropic.Anthropic(
        api_key="sk-ant-teste", http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(servidor))
    )

    resposta = agente.perguntar("Qual a margem líquida da WEG em 2025?", cliente=cliente)

    assert resposta.texto == "A margem líquida da WEG em 2025 foi de 16,6%."
    assert [c["ferramenta"] for c in resposta.chamadas] == ["consultar_metricas"]
    assert resposta.tokens_entrada == 2500 and resposta.tokens_saida == 150
    assert resposta.custo_usd == pytest.approx((2500 * 4 + 150 * 20) / 1e6)

    primeira = requisicoes[0]
    assert primeira["model"] == "claude-opus-5-5"
    assert primeira["output_config"] == {"effort": "medium"}
    assert primeira["fallbacks"] == "default"
    assert {t["name"] for t in primeira["tools"]} == {
        "listar_metricas",
        "buscar_empresas",
        "listar_setores",
        "consultar_metricas",
    }
    # Na segunda chamada, o resultado da ferramenta volta para a IA
    resultado = requisicoes[1]["messages"][-1]["content"][0]
    conteudo = resultado["content"]
    texto = conteudo if isinstance(conteudo, str) else conteudo[0]["text"]
    assert resultado["type"] == "tool_result" and "0.166" in texto
