# Post 2 — 35 milhões de linhas
Status: **aprovado** por Marcelo (22/10/2026), versão v2. Data: sex 23/10/2026. Imagem: `imagem.png`.
Mudanças da v1: explica "ingestão" para leigos; termos técnicos com explicação curta; tempo da 2ª execução testado (2 s); fecha com uma pergunta.

---

Baixei mais de 15 anos de balanços. A parte difícil não foi baixar.

No último post, contei o problema: os balanços das empresas da bolsa são públicos, mas difíceis de usar. Esta semana terminei a etapa 3 do projeto: a ingestão.

Ingestão é o "encanamento" de um projeto de dados: o caminho que leva o dado da fonte até o banco de dados.

A fonte é a CVM, que atualiza os balanços toda semana. E as empresas reenviam balanços corrigidos, então o dado de hoje pode mudar amanhã.

Por isso, o desafio de verdade não é baixar uma vez. É manter tudo atualizado sem baixar tudo de novo e sem duplicar nada.

Como resolvi, em Python:
1. Antes de baixar, pergunto ao servidor da CVM se o arquivo mudou. Se não mudou, pulo.
2. Se mudou, comparo a "impressão digital" do arquivo (um hash SHA-256). Se o conteúdo é o mesmo, não recarrego.
3. Carrego no PostgreSQL arquivo por arquivo, em transações: ou o arquivo entra inteiro, ou nada muda. Nunca fica nada pela metade.
4. Guardo os dados exatamente como vieram. Limpar é outra etapa, que posso refazer sem baixar nada de novo.
5. Dados pessoais do cadastro (nome, e-mail e telefone de responsáveis) ficam de fora.

Resultado:
• 1ª execução: 34 arquivos, 35,2 milhões de linhas, em 3 minutos e 22 segundos
• 2ª execução: 2 segundos. Nada mudou, nada foi baixado
• Contagem no banco igual à dos arquivos originais

A lição: uma boa ingestão é aquela que você pode rodar 100 vezes sem estragar nada.

Próxima etapa: a modelagem. E já encontrei o primeiro problema: linhas duplicadas na fonte oficial.

Para quem trabalha com dados: como vocês evitam carregar o mesmo dado duas vezes?

#EngenhariaDeDados #Python #PostgreSQL #ETL #DadosAbertos
