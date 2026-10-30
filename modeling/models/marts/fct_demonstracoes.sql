{{ config(post_hook=[
    "create index if not exists fct_demonstracoes_empresa_idx on {{ this }} (cnpj, dt_refer)",
    "create index if not exists fct_demonstracoes_conta_idx on {{ this }} (cd_conta, demonstracao)",
]) }}

-- A CVM às vezes registra dois documentos com a mesma versão (ex.: dois envios da DFP 2024, ambos "versão 1").
-- Fica o de entrega mais tardia: para o ML, é a data em que o dado com certeza já estava público.
with documentos as (
    select
        tipo_doc,
        cnpj,
        dt_refer,
        versao,
        dt_entrega,
        row_number() over (
            partition by tipo_doc, cnpj, dt_refer, versao
            order by dt_entrega desc, id_doc desc
        ) as ordem
    from {{ ref('stg_cvm__documentos') }}
)

-- Tabela principal: um valor por empresa, documento, demonstração, período e conta. Já limpa e em reais.
select
    d.tipo_doc,
    d.demonstracao,
    d.escopo,
    d.cnpj,
    d.cd_cvm,
    d.nome_empresa,
    d.dt_refer,
    d.versao,
    doc.dt_entrega,
    d.dt_ini_exerc,
    d.dt_fim_exerc,
    d.cd_conta,
    d.ds_conta,
    d.valor,
    d.conta_fixa,
    -- Quantos meses o valor cobre. No ITR, a DRE traz o trimestre (3) e o acumulado do ano (6, 9).
    -- Balanço é posição numa data, então fica nulo.
    case
        when d.dt_ini_exerc is not null then
            (extract(year from d.dt_fim_exerc) - extract(year from d.dt_ini_exerc)) * 12
            + extract(month from d.dt_fim_exerc) - extract(month from d.dt_ini_exerc) + 1
    end::int as meses_periodo,
    -- Nível da conta na árvore: 3.01 = 2, 3.01.01 = 3.
    array_length(string_to_array(d.cd_conta, '.'), 1) as nivel_conta
from {{ ref('int_demonstracoes__escopo_preferido') }} as d
left join documentos as doc
    on
        d.tipo_doc = doc.tipo_doc
        and d.cnpj = doc.cnpj
        and d.dt_refer = doc.dt_refer
        and d.versao = doc.versao
        and doc.ordem = 1
