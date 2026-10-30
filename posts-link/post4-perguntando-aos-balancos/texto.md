# Post 4 — Perguntando aos balanços
Status: rascunho v1 (30/10/2026), aguardando revisão de Marcelo. Imagem: `imagem.png` (barra com "▲ este post" no agente de IA).
Números: `agent/avaliacao/resultado.json` (prova de 30/10/2026: 20/20, 4/4 pegadinhas, US$ 1,03).

---

Perguntei a uma IA quanto a Ambev pagou de imposto sobre o lucro em 2025. Ela não chutou.

Resposta: alíquota efetiva de IR e CSLL de 17,7%, contra os 34% nominais do lucro real. E veio com a conta: lucro antes dos tributos, despesa de imposto e a regra usada.

O segredo não está no modelo de IA. Está no que vem antes dele.

1. A camada semântica. Escrevi, num arquivo, a regra de cada métrica: receita, margens, ROE, endividamento, liquidez e a alíquota efetiva. A IA não calcula nada. Ela escolhe qual consulta fazer, e o número sai da regra.

2. Ferramentas, não memória. O agente tem quatro ferramentas: listar as métricas, achar o nome oficial da empresa, listar setores e consultar. Se o número não veio de uma ferramenta, ele não pode responder.

3. Uma prova, não uma impressão. Montei 20 perguntas com gabarito: 12 de valor, 4 de ranking e 4 pegadinhas. Exemplos de pegadinha: perguntar sobre um banco (que fica fora das métricas), sobre uma empresa que não existe e sobre a alíquota de quem teve prejuízo (que não faz sentido calcular).

Resultado: 20 de 20, incluindo as 4 pegadinhas. Em vez de inventar, o agente explicou por que não podia responder. A prova inteira custou US$ 1,03, cerca de 5 centavos de dólar por pergunta.

A minha experiência na área fiscal entrou numa regra: com prejuízo antes dos tributos, a alíquota efetiva fica vazia. Sem essa regra, a Magazine Luiza em 2023 apareceria com uma "alíquota" de 52,6%, um número que parece real e não significa nada.

Para quem trabalha com IA: como vocês medem se o agente está acertando?

#InteligenciaArtificial #EngenhariaDeDados #dbt #LLM #DadosAbertos
