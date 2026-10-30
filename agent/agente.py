"""Agente de IA: responde perguntas em português sobre os balanços usando só a camada semântica.

Rode (na raiz do projeto, com o banco no ar e ANTHROPIC_API_KEY no .env):
    python -m agent.agente "Qual a margem líquida da WEG em 2025?"
"""

import json
import sys
from dataclasses import dataclass, field

import anthropic
from anthropic import beta_tool
from dotenv import load_dotenv

from agent import ferramentas
from agent.ferramentas import RAIZ

MODELO = "claude-opus-5-5"
ESFORCO = "medium"  # perguntas de consulta não precisam do esforço máximo

# Preço do Claude Opus 5.5 (US$ por milhão de tokens), para estimar o custo de cada pergunta
PRECO_ENTRADA, PRECO_SAIDA = 4.00, 20.00

INSTRUCOES = """Você é o analista do projeto Next Step SP. Responde perguntas sobre as demonstrações financeiras
anuais (DFP) de companhias abertas brasileiras, publicadas pela CVM, de 2010 a 2025.

Regras (siga todas):
1. Todo número da resposta vem de uma ferramenta. Nunca calcule, estime ou lembre números por conta própria;
   no máximo formate (percentual com 1 casa, valores em R$ milhões ou bilhões).
2. Antes de consultar uma empresa, use buscar_empresas para achar o nome oficial. Se não achar, diga que a empresa
   não está na base; não chute outra.
3. Para saber o que cada métrica significa, use listar_metricas e explique a fórmula em uma linha, em português simples.
4. Escopo: só empresas comerciais e industriais. Bancos e seguradoras usam outro plano de contas e não estão nas
   métricas: se a pergunta for sobre eles, diga isso.
5. Se uma métrica vier vazia, explique o motivo provável pela regra dela (ex.: alíquota efetiva não é calculada
   quando há prejuízo antes dos tributos; documentos com totais inconsistentes ficam de fora).
6. Responda em português do Brasil, curto e direto. Termine citando a fonte: "Fonte: CVM (DFP), camada semântica
   Next Step SP"."""


@beta_tool
def listar_metricas() -> str:
    """Lista as métricas disponíveis, com o nome técnico, o rótulo e a regra de cálculo."""
    return json.dumps(ferramentas.listar_metricas(), ensure_ascii=False)


@beta_tool
def buscar_empresas(termo: str) -> str:
    """Procura empresas pelo nome e devolve o nome oficial, o setor e os anos disponíveis.

    Args:
        termo: parte do nome da empresa, ex.: "weg", "magazine luiza".
    """
    return _rodar(ferramentas.buscar_empresas, termo)


@beta_tool
def listar_setores() -> str:
    """Lista os setores de atividade (cadastro da CVM) que existem na base."""
    return _rodar(ferramentas.listar_setores)


@beta_tool
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
) -> str:
    """Calcula métricas pela camada semântica. Use para qualquer número da resposta.

    Args:
        metricas: nomes técnicos das métricas (de listar_metricas).
        ano_inicio: primeiro ano do exercício (2010 a 2025).
        ano_fim: último ano do exercício (2010 a 2025).
        empresas: nomes oficiais (de buscar_empresas); omita para todas.
        setor: nome exato do setor (de listar_setores); omita para todos.
        agrupar_por: lista com "ano", "empresa" e/ou "setor". Padrão: ["ano", "empresa"].
        ordenar_por: métrica (entre as pedidas) para ordenar, útil em rankings.
        decrescente: true para do maior para o menor.
        limite: máximo de linhas (até 50).
    """
    return _rodar(
        ferramentas.consultar_metricas,
        metricas,
        ano_inicio,
        ano_fim,
        empresas=empresas,
        setor=setor,
        agrupar_por=agrupar_por,
        ordenar_por=ordenar_por,
        decrescente=decrescente,
        limite=limite,
    )


def _rodar(funcao, *args, **kwargs) -> str:
    """Executa a ferramenta; um erro volta como texto, para a IA corrigir a chamada em vez de quebrar o agente."""
    try:
        return json.dumps(funcao(*args, **kwargs), ensure_ascii=False)
    except (ValueError, RuntimeError) as erro:
        return json.dumps({"erro": str(erro)}, ensure_ascii=False)


FERRAMENTAS = [listar_metricas, buscar_empresas, listar_setores, consultar_metricas]


@dataclass
class Resposta:
    texto: str
    chamadas: list[dict] = field(default_factory=list)  # ferramentas usadas, para auditoria e avaliação
    tokens_entrada: int = 0
    tokens_saida: int = 0
    recusou: bool = False

    @property
    def custo_usd(self) -> float:
        return (self.tokens_entrada * PRECO_ENTRADA + self.tokens_saida * PRECO_SAIDA) / 1_000_000


def perguntar(pergunta: str, cliente: anthropic.Anthropic | None = None) -> Resposta:
    """Faz uma pergunta ao agente e devolve a resposta, as ferramentas usadas e o custo."""
    load_dotenv(RAIZ / ".env")
    cliente = cliente or anthropic.Anthropic()
    runner = cliente.beta.messages.tool_runner(
        model=MODELO,
        max_tokens=16000,
        system=INSTRUCOES,
        output_config={"effort": ESFORCO},
        # Se o modelo recusar por precaução, a API tenta de novo com o modelo indicado pela própria Anthropic
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        tools=FERRAMENTAS,
        messages=[{"role": "user", "content": pergunta}],
    )
    resposta = Resposta(texto="")
    for mensagem in runner:
        resposta.tokens_entrada += mensagem.usage.input_tokens
        resposta.tokens_saida += mensagem.usage.output_tokens
        for bloco in mensagem.content:
            if bloco.type == "tool_use":
                resposta.chamadas.append({"ferramenta": bloco.name, "entrada": bloco.input})
            elif bloco.type == "text":
                resposta.texto = bloco.text
        resposta.recusou = mensagem.stop_reason == "refusal"
    return resposta


def main():
    if len(sys.argv) < 2:
        sys.exit('Uso: python -m agent.agente "sua pergunta"')
    resposta = perguntar(" ".join(sys.argv[1:]))
    print(resposta.texto)
    print(f"\n[{len(resposta.chamadas)} consultas · US$ {resposta.custo_usd:.3f}]")


if __name__ == "__main__":
    main()
