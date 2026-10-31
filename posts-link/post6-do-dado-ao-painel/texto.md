# Post 6 — Do dado ao painel (projeto completo)
Status: rascunho v1 (30/10/2026), aguardando revisão de Marcelo. Imagem: `imagem.png` (print real do painel, barra completa).
Números: README e guia de estudo (todos testados até 30/10/2026). Este é o post para **impulsionar**.

Antes de publicar:
- Trocar `[link do GitHub]` e `[link do site]` pelos endereços reais (GitHub público e página no portfólio).
- Revisar o `CLAUDE.md` do repositório (tem dados pessoais) antes de deixar o GitHub público.
- Linha opcional, decisão sua: "Estou em transição da área fiscal para dados e aberto a oportunidades em engenharia de dados e IA." Se quiser, entra antes da pergunta final.

---

Os balanços de todas as empresas da bolsa brasileira são públicos. Quase ninguém consegue usar.

São milhões de linhas em códigos contábeis, com duplicatas, escalas diferentes, versões corrigidas e até erros na fonte. Nos últimos posts, mostrei cada etapa de um projeto para transformar isso em respostas. Hoje ele está completo.

O caminho, do arquivo bruto ao painel:

1. Ingestão. Baixa da CVM só o que mudou: 35,2 milhões de linhas de balanços anuais e trimestrais.

2. Limpeza. Tira duplicatas, repetições e contagem dupla, com testes automáticos. Um deles achou um balanço oficial com R$ 370 milhões faltando no total.

3. Regras de negócio. Dez métricas, como margem, ROE e alíquota efetiva de imposto, escritas uma única vez. Conferi cada uma contra o cálculo feito à mão: 30 de 30.

4. Agente de IA. Responde em português, mas não calcula nada: consulta as regras. Numa prova com gabarito, acertou 20 de 20, incluindo as pegadinhas.

5. Modelo de risco. Aponta empresas com risco de recuperação judicial em até 24 meses. Ganha do Z-score de Altman, mas por pouco (AUC 0,69 contra 0,66). Mostro esse limite em vez de esconder.

6. Painel. Compara uma empresa com o setor, monta rankings, mostra o mapa de risco e tem um chat com o agente.

Tudo roda com um comando, e cada número do painel pode ser rastreado até a linha original da CVM.

O que eu levo do projeto: a parte difícil não foi o algoritmo nem a IA. Foi desconfiar do dado, escrever a regra antes de calcular e testar tudo o que eu afirmo. Foi aí que a minha experiência na área fiscal mais ajudou.

Código, documentação e resultados: [link do GitHub]
Página do projeto: [link do site]

Para quem trabalha com dados: o que você olharia primeiro neste projeto?

#EngenhariaDeDados #InteligenciaArtificial #dbt #Python #DadosAbertos
