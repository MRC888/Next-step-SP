# Post 2 — 35 milhões de linhas
Status: rascunho v1 (22/10/2026), aguardando revisão de Marcelo. Data: sex 23/10/2026. Imagem: a fazer depois da aprovação do texto.

---

Baixei mais de 15 anos de balanços. A parte difícil não foi baixar.

No post anterior, contei o problema: os balanços das empresas da bolsa são públicos, mas difíceis de usar. Esta semana terminei a etapa 3 do projeto: a ingestão, que traz esses dados para um banco de dados.

Por que a CVM? Dados reais, de todos os setores, atualizados toda semana. E as empresas reenviam balanços corrigidos, então o dado de hoje pode mudar amanhã.

Esse é o desafio de verdade: manter tudo atualizado sem baixar tudo de novo e sem duplicar nada.

Como resolvi, em Python:
1. Antes de baixar, pergunto ao servidor se o arquivo mudou. Se não mudou, pulo.
2. Se mudou, comparo a "impressão digital" do arquivo (hash SHA-256). Se o conteúdo é o mesmo, não recarrego.
3. Carrego no PostgreSQL com COPY, um arquivo por transação: ou entra inteiro, ou nada muda.
4. Guardo os dados exatamente como vieram. Limpar é outra etapa, que pode ser refeita sem baixar de novo.
5. Dados pessoais do cadastro ficam de fora.

Resultado:
• 34 arquivos, 35,2 milhões de linhas, em 3 minutos e 22 segundos
• Segunda execução: "sem mudança" em tudo, em segundos
• Contagem no banco igual à dos arquivos originais

A lição: uma boa ingestão é aquela que você pode rodar 100 vezes sem estragar nada.

Próxima etapa: a modelagem. E já encontrei o primeiro problema: linhas duplicadas na fonte oficial.

#EngenhariaDeDados #Python #PostgreSQL #ETL #DadosAbertos
