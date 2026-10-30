-- Auditoria: lista os documentos em que algum total oficial não bate com a soma das contas filhas.
-- Aviso, não erro: são erros da fonte. Esses documentos ficam com dados_consistentes = false e saem das métricas.
-- O aviso serve para acompanhar se o número de casos muda a cada carga.
{{ config(severity='warn') }}

select
    cnpj,
    nome_empresa,
    dt_refer
from {{ ref('fct_contas_anuais') }}
where not dados_consistentes
