# Post 1 — O ponto de partida
Status: **aprovado e postado** (22/10/2026), versão v2. Mudanças da v1: explica o que é "balanço" antes de perguntar; pergunta final com exemplos; sem a frase "apaixonado por tecnologia / não me vejo fazendo outra coisa" (pode soar mal no emprego atual). Imagem: `post1-imagem.png`.

---

Os balanços de toda empresa da bolsa são públicos. Quase ninguém consegue usar.

Balanço é o "boletim" financeiro de uma empresa: quanto vendeu, quanto lucrou, quanto deve, quanto pagou de imposto. Toda semana, a CVM atualiza esses números de cerca de 700 companhias abertas.

O problema: eles estão em 35 milhões de linhas, em códigos contábeis (como "3.01" e "2.03"), espalhados em arquivos por ano. Para responder "essa empresa vai bem?", alguém precisa baixar, limpar e montar planilhas por horas.

Trabalho na área fiscal, com impostos e regimes tributários. E decidi construir, do zero, uma plataforma de dados ponta a ponta com esses balanços.

O plano tem 9 etapas:
1. Ambiente (Docker, PostgreSQL, Python)
2. Escolha da base (CVM: DFP e ITR)
3. Ingestão automatizada
4. Modelagem em camadas (dbt)
5. Camada semântica: as regras de cálculo de cada métrica
6. Agente de IA que responde perguntas em português usando essas regras
7. Machine learning para estimar risco de dificuldade financeira
8. Dashboard
9. Automação: tudo rodando sozinho toda semana

As 3 primeiras estão prontas.

O objetivo é elevar meu nível em engenharia de dados e IA, construindo algo real, com decisões que eu consiga defender.

Vou compartilhar o processo por aqui, com os problemas reais do caminho.

Se você pudesse perguntar qualquer coisa aos números das empresas da bolsa, o que perguntaria?
Por exemplo: quem mais lucrou em 2025? Quanto de imposto uma empresa paga sobre o lucro? Quem está endividada demais?

#EngenhariaDeDados #Python #SQL #InteligenciaArtificial #DadosAbertos
