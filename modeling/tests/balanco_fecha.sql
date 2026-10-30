-- Checagem contábil: Ativo Total (conta 1) tem de ser igual a Passivo Total + PL (conta 2).
-- Tolerância de R$ 1.000 por arredondamento. Aviso, não erro: a fonte pode ter casos com problema.
-- Casos já investigados ficam em seeds/excecoes_conhecidas.csv (com motivo e evidência) e não geram aviso.
{{ config(severity='warn') }}

with ativo as (
    select
        tipo_doc,
        cnpj,
        dt_refer,
        valor
    from {{ ref('fct_demonstracoes') }}
    where demonstracao = 'BPA' and cd_conta = '1'
),

passivo as (
    select
        tipo_doc,
        cnpj,
        dt_refer,
        valor
    from {{ ref('fct_demonstracoes') }}
    where demonstracao = 'BPP' and cd_conta = '2'
),

excecoes as (
    select
        tipo_doc,
        cnpj,
        dt_refer
    from {{ ref('excecoes_conhecidas') }}
    where teste = 'balanco_fecha'
)

select
    a.tipo_doc,
    a.cnpj,
    a.dt_refer,
    a.valor as ativo_total,
    p.valor as passivo_total,
    a.valor - p.valor as diferenca
from ativo as a
inner join passivo as p
    on a.tipo_doc = p.tipo_doc and a.cnpj = p.cnpj and a.dt_refer = p.dt_refer
left join excecoes as e
    on a.tipo_doc = e.tipo_doc and a.cnpj = e.cnpj and a.dt_refer = e.dt_refer
where abs(a.valor - p.valor) > 1000 and e.cnpj is null
