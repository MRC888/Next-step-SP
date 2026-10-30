-- Checagem contábil: Ativo Total (conta 1) tem de ser igual a Passivo Total + PL (conta 2).
-- Tolerância de R$ 1.000 por arredondamento. Aviso, não erro: a fonte pode ter casos com problema.
{{ config(severity='warn') }}

with ativo as (
    select tipo_doc, cnpj, dt_refer, valor from {{ ref('fct_demonstracoes') }}
    where demonstracao = 'BPA' and cd_conta = '1'
),
passivo as (
    select tipo_doc, cnpj, dt_refer, valor from {{ ref('fct_demonstracoes') }}
    where demonstracao = 'BPP' and cd_conta = '2'
)

select a.tipo_doc, a.cnpj, a.dt_refer, a.valor as ativo_total, p.valor as passivo_total, a.valor - p.valor as diferenca
from ativo a
join passivo p using (tipo_doc, cnpj, dt_refer)
where abs(a.valor - p.valor) > 1000
