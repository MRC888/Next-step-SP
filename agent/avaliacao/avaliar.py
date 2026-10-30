"""Prova do agente: roda as perguntas de agent/avaliacao/perguntas.json e corrige sem IA.

Correção determinística (mais barata e auditável que um juiz de IA):
- numero: cada valor esperado tem de aparecer no texto (aceita formatos como "16,6%", "R$ 40,8 bilhões", "0,96").
- ranking: o nome da empresa certa tem de aparecer.
- pegadinha: o agente tem de recusar ou explicar, sem inventar número.

Rode (na raiz, com banco e chave): python -m agent.avaliacao.avaliar
Resultado salvo em agent/avaliacao/resultado.json (texto de cada resposta, nota, custo).
"""

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

from agent.agente import perguntar

PASTA = Path(__file__).resolve().parent
TOLERANCIA = 0.01  # 1%: a resposta arredonda (ex.: 16,6% para 0,16606)

ESCALAS = {"tri": 1e12, "trilh": 1e12, "bi": 1e9, "bilh": 1e9, "mi": 1e6, "milh": 1e6, "mil": 1e3}
NUMERO = re.compile(
    r"(?P<num>\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)\s*(?P<sufixo>%|trilh\w*|tri\b|bilh\w*|bi\b|milh\w*|mi\b|mil\b)?",
    re.IGNORECASE,
)


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def numeros_no_texto(texto: str) -> list[tuple[float, str]]:
    """Extrai números no padrão brasileiro e devolve (valor, tipo): tipo é "percentual", "reais" ou "vezes"."""
    achados = []
    for m in NUMERO.finditer(texto):
        valor = float(m["num"].replace(".", "").replace(",", "."))
        sufixo = (m["sufixo"] or "").lower()
        if sufixo == "%":
            achados.append((valor / 100, "percentual"))
        elif sufixo:
            escala = next(v for k, v in ESCALAS.items() if sufixo.startswith(k))
            achados.append((valor * escala, "reais"))
        else:
            achados.append((valor, "vezes"))
    return achados


def _bate(esperado: dict, achados: list[tuple[float, str]]) -> bool:
    alvo = abs(esperado["valor"])
    return any(tipo == esperado["unidade"] and abs(valor - alvo) <= TOLERANCIA * alvo for valor, tipo in achados)


def corrigir(questao: dict, texto: str) -> tuple[bool, str]:
    """Devolve (acertou, motivo)."""
    normal = _sem_acento(texto)
    achados = numeros_no_texto(texto)
    for palavra in questao.get("deve_conter", []):
        if _sem_acento(palavra) not in normal:
            return False, f"faltou '{palavra}'"
    if questao.get("deve_conter_algum") and not any(_sem_acento(p) in normal for p in questao["deve_conter_algum"]):
        return False, "não explicou a limitação"
    for esperado in questao.get("esperados", []):
        if not _bate(esperado, achados):
            return False, f"valor {esperado['valor']} ({esperado['unidade']}) não encontrado"
    for proibido in questao.get("valores_proibidos", []):
        if _bate({"valor": proibido, "unidade": "percentual"}, achados):
            return False, f"deu o valor sem sentido {proibido}"
    if questao.get("proibido_numero_percentual") and any(t == "percentual" for _, t in achados):
        return False, "inventou percentual"
    if questao.get("proibido_numero_reais") and any(t == "reais" for _, t in achados):
        return False, "inventou valor em reais"
    return True, "ok"


def main():
    questoes = json.loads((PASTA / "perguntas.json").read_text(encoding="utf-8"))
    if len(sys.argv) > 1:  # rodar só algumas: python -m agent.avaliacao.avaliar 1 2 17
        questoes = [q for q in questoes if str(q["id"]) in sys.argv[1:]]
    resultados, custo_total = [], 0.0
    for q in questoes:
        inicio = time.time()
        resposta = perguntar(q["pergunta"])
        acertou, motivo = corrigir(q, resposta.texto)
        custo_total += resposta.custo_usd
        resultados.append(
            {
                "id": q["id"],
                "tipo": q["tipo"],
                "pergunta": q["pergunta"],
                "acertou": acertou,
                "motivo": motivo,
                "resposta": resposta.texto,
                "ferramentas": resposta.chamadas,
                "custo_usd": round(resposta.custo_usd, 4),
                "segundos": round(time.time() - inicio, 1),
            }
        )
        situacao = "OK   " if acertou else "ERRO "
        print(f"{situacao} #{q['id']:>2} {q['tipo']:<9} {motivo:<45} US$ {resposta.custo_usd:.3f}")

    acertos = sum(r["acertou"] for r in resultados)
    pegadinhas = [r for r in resultados if r["tipo"] == "pegadinha"]
    resumo = {
        "acertos": acertos,
        "total": len(resultados),
        "pegadinhas_ok": sum(r["acertou"] for r in pegadinhas),
        "pegadinhas_total": len(pegadinhas),
        "custo_total_usd": round(custo_total, 3),
        "resultados": resultados,
    }
    (PASTA / "resultado.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{acertos}/{len(resultados)} acertos · pegadinhas {resumo['pegadinhas_ok']}/{len(pegadinhas)}")
    print(f"Custo total: US$ {custo_total:.2f}")


if __name__ == "__main__":
    main()
