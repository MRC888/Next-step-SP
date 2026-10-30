-- Uma linha por empresa (CNPJ), com setor, situação e tipo de plano de contas.
with cadastro as (
    -- Alguns CNPJs aparecem mais de uma vez (registro cancelado e depois reaberto). Fica o ativo, ou o mais recente.
    select
        *,
        row_number() over (
            partition by cnpj
            order by (situacao_registro = 'ATIVO') desc, dt_registro desc nulls last
        ) as ordem
    from {{ ref('stg_cvm__cadastro') }}
),

plano as (
    -- O plano de contas muda conforme o tipo de empresa. A descrição da conta 3.01 (primeira linha da DRE)
    -- revela o tipo: bancos começam por "Receitas da Intermediação Financeira", seguradoras por receitas de seguros.
    select distinct on (cnpj)
        cnpj,
        case
            when ds_conta ilike '%intermedia%financeira%' then 'instituicao_financeira'
            when ds_conta ilike '%segurad%' or ds_conta = 'Receitas das Operações' then 'seguradora'
            else 'empresa_geral'
        end as plano_contas
    from {{ ref('fct_demonstracoes') }}
    where demonstracao = 'DRE' and cd_conta = '3.01'
    order by cnpj asc, dt_refer desc
)

select
    c.cnpj,
    c.cd_cvm,
    c.razao_social,
    c.nome_comercial,
    c.setor,
    p.plano_contas,
    c.situacao_registro,
    c.dt_registro,
    c.dt_cancelamento,
    c.motivo_cancelamento,
    c.situacao_emissor,
    c.dt_inicio_situacao_emissor,
    c.tipo_mercado,
    c.categoria_registro,
    c.controle_acionario,
    c.uf,
    c.auditor,
    -- Candidato a rótulo do ML: empresa em recuperação, falência ou liquidação.
    c.situacao_emissor in (
        'EM RECUPERAÇÃO JUDICIAL OU EQUIVALENTE',
        'EM RECUPERAÇÃO EXTRAJUDICIAL',
        'FALIDA',
        'LIQUIDAÇÃO EXTRAJUDICIAL',
        'EM LIQUIDAÇÃO JUDICIAL'
    ) as em_dificuldade_financeira
from cadastro as c
left join plano as p on c.cnpj = p.cnpj
where c.ordem = 1
