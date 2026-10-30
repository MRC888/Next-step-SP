# Post 3 — Dado sujo, dado limpo
Status: **postado** em 30/10/2026 (texto v1 colado pelo Claude no LinkedIn; imagem anexada e publicação feita por Marcelo). Imagem: `imagem.png` (barra com "▲ este post" na modelagem).
Números conferidos no banco do Mac em 30/10/2026 (dbt build: 13 testes, 0 erros).

---

Um balanço publicado na CVM não fechava. Faltavam R$ 370 milhões. E o erro estava na fonte oficial.

No último post, mostrei como trouxe 35 milhões de linhas de balanços públicos para um banco de dados. Mas dado público não é dado pronto. Ele chega repetido, em escalas diferentes, com versões corrigidas e, às vezes, com erro.

Esta foi a etapa 4 do projeto: a modelagem. É a limpeza dos dados, feita em camadas com dbt, uma ferramenta que organiza essa limpeza em passos de SQL que podem ser testados.

Comecei só com os balanços anuais. O caminho foi este:
• 8,6 milhões de linhas entraram, do jeito que a CVM publica
• − 4,3 milhões: cada balanço repete o ano anterior, só para comparação
• − 19 mil: linhas duplicadas na fonte e balanços reenviados com correção
• − 1,6 milhão: contagem dupla. Empresas com controladas publicam o balanço do grupo e o da controladora. Fico com o do grupo
• Resultado: 2,7 milhões de linhas limpas, em reais, de 1.218 empresas

E os R$ 370 milhões?

Um dos testes automáticos confere a regra básica da contabilidade: o que a empresa tem (ativo) precisa ser igual ao que ela deve mais o capital dos donos (passivo + patrimônio líquido). Uma empresa falhou: a Itapebi, no balanço de 2021.

Abrindo conta por conta, as contas detalhadas estavam certas. Só a linha de total tinha sido preenchida sem o patrimônio líquido. A prova: no balanço do ano seguinte, a própria empresa repete os números de 2021 para comparação, e ali o total aparece corrigido.

Registrei o caso como exceção conhecida, com o motivo e a evidência. O teste continua vigiando todas as outras empresas. E ficou uma regra para as próximas etapas: nas métricas, somo as contas detalhadas em vez de confiar no total.

Outra lição veio do desempenho. A primeira versão da limpeza rodou 70 minutos e caiu. Ao guardar o passo mais pesado como tabela, em vez de recalcular toda vez, o tempo caiu para cerca de 1 minuto.

Próxima etapa: as regras de negócio. Cada métrica (receita, margem, endividamento, alíquota efetiva de imposto) com a sua regra escrita, para que uma IA possa calcular sem inventar.

Para quem trabalha com dados: qual foi o erro mais estranho que você já encontrou numa fonte oficial?

#EngenhariaDeDados #dbt #SQL #QualidadeDeDados #DadosAbertos
