-- Tabela, não view: a função de janela sobre milhões de linhas é o passo mais pesado, e o modelo seguinte
-- lê este duas vezes. Como view, o banco refaria o cálculo a cada leitura (causa provável da queda de 21/10).
{{ config(
    materialized='table',
    post_hook="create index if not exists deduplicadas_documento_idx on {{ this }} (tipo_doc, cnpj, dt_refer, escopo)"
) }}

-- 1) Fica só com o exercício atual (ÚLTIMO). O PENÚLTIMO é a coluna de comparação com o ano anterior;
--    o valor oficial daquele período já vem no documento do próprio período.
-- 2) Remove linhas repetidas: a CVM publica algumas linhas duplicadas (ex.: 29 balanços no ITR).
--    Se houver mais de uma, fica a de versão mais recente.
with ranqueado as (
    select
        *,
        row_number() over (
            partition by tipo_doc, demonstracao, escopo, cnpj, dt_refer, dt_ini_exerc, dt_fim_exerc, cd_conta
            order by versao desc, _arquivo desc
        ) as ordem
    from {{ ref('stg_cvm__demonstracoes') }}
    where ordem_exerc = 'ÚLTIMO'
)

select
    tipo_doc,
    demonstracao,
    escopo,
    cnpj,
    cd_cvm,
    nome_empresa,
    dt_refer,
    versao,
    dt_ini_exerc,
    dt_fim_exerc,
    cd_conta,
    ds_conta,
    valor,
    conta_fixa
from ranqueado
where ordem = 1
