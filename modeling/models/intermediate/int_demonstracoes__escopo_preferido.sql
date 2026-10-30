-- Empresa com controladas publica dois conjuntos: consolidado (grupo inteiro) e individual (só a controladora).
-- Regra de mercado: usar o consolidado quando existe; senão, o individual.
-- A escolha é por documento (empresa + data), para todas as demonstrações do documento seguirem a mesma base.
with escopo_do_documento as (
    select
        tipo_doc,
        cnpj,
        dt_refer,
        case when bool_or(escopo = 'con') then 'con' else 'ind' end as escopo_escolhido
    from {{ ref('int_demonstracoes__deduplicadas') }}
    group by 1, 2, 3
)

select
    d.tipo_doc,
    d.demonstracao,
    d.escopo,
    d.cnpj,
    d.cd_cvm,
    d.nome_empresa,
    d.dt_refer,
    d.versao,
    d.dt_ini_exerc,
    d.dt_fim_exerc,
    d.cd_conta,
    d.ds_conta,
    d.valor,
    d.conta_fixa
from {{ ref('int_demonstracoes__deduplicadas') }} as d
inner join escopo_do_documento as e
    on
        d.tipo_doc = e.tipo_doc
        and d.cnpj = e.cnpj
        and d.dt_refer = e.dt_refer
        and d.escopo = e.escopo_escolhido
