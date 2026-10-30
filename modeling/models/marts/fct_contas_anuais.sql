{{ config(post_hook=[
    "create unique index if not exists fct_contas_anuais_pk on {{ this }} (cnpj, dt_refer)",
]) }}

-- Base da camada semântica: uma linha por empresa e ano (DFP), com as contas que as métricas usam.
--
-- Regra de qualidade (30/10/2026), como numa auditoria:
--   1. Os valores oficiais são os totais que a empresa publicou (o número que ela assina).
--   2. Cada total é conferido com a soma das contas filhas.
--   3. Se algum divergir além da tolerância, o documento fica com dados_consistentes = false,
--      e as métricas usam só os consistentes.
-- Por quê: na fonte há erro dos dois lados. Itapebi 2021 tem o total errado e as filhas certas;
-- Vale 2022 tem o custo com sinal trocado (filha errada, total certo).
-- Escopo: só empresas comerciais e industriais. Bancos e seguradoras usam outro plano de contas na DRE.

with contas as (
    select
        cnpj,
        nome_empresa,
        dt_refer,
        dt_entrega,
        demonstracao,
        cd_conta,
        ds_conta,
        valor
    from {{ ref('fct_demonstracoes') }}
    where
        tipo_doc = 'DFP'
        -- DRE só no período de 12 meses (o ano inteiro); balanço é posição, sem período
        and (demonstracao in ('BPA', 'BPP') or (demonstracao = 'DRE' and meses_periodo = 12))
),

-- O plano de contas é decidido por documento: a conta 3.01 diz se a DRE é de empresa comum
documentos_empresa_geral as (
    select
        cnpj,
        dt_refer
    from contas
    where
        demonstracao = 'DRE'
        and cd_conta = '3.01'
        and ds_conta not ilike '%intermedia%financeira%'
        and ds_conta not ilike '%segur%'
        and ds_conta != 'Receitas das Operações'
),

pivotado as (
    select
        c.cnpj,
        c.dt_refer,
        max(c.nome_empresa) as nome_empresa,
        max(c.dt_entrega) as dt_entrega,

        -- DRE (custos, despesas e impostos vêm negativos da CVM)
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.01') as receita_liquida,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.02') as custo_vendas,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.03') as lucro_bruto,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.04') as despesas_operacionais,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.05') as resultado_operacional,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.06') as resultado_financeiro,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.07') as lucro_antes_ir,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.08') as ir_csll,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.10') as resultado_descontinuado,
        sum(c.valor) filter (where c.demonstracao = 'DRE' and c.cd_conta = '3.11') as lucro_liquido,

        -- Balanço: ativo
        sum(c.valor) filter (where c.demonstracao = 'BPA' and c.cd_conta = '1') as ativo_total,
        sum(c.valor) filter (where c.demonstracao = 'BPA' and c.cd_conta = '1.01') as ativo_circulante,
        sum(c.valor) filter (where c.demonstracao = 'BPA' and c.cd_conta = '1.02') as ativo_nao_circulante,
        sum(c.valor) filter (where c.demonstracao = 'BPA' and c.cd_conta = '1.01.01') as caixa,
        sum(c.valor) filter (where c.demonstracao = 'BPA' and c.cd_conta = '1.01.02') as aplicacoes_financeiras,

        -- Balanço: passivo e patrimônio líquido
        -- A conta 2 (Passivo Total) não é usada nas métricas: na Itapebi 2021 ela veio sem o PL.
        sum(c.valor) filter (where c.demonstracao = 'BPP' and c.cd_conta = '2') as passivo_total_informado,
        sum(c.valor) filter (where c.demonstracao = 'BPP' and c.cd_conta = '2.01') as passivo_circulante,
        sum(c.valor) filter (where c.demonstracao = 'BPP' and c.cd_conta = '2.02') as passivo_nao_circulante,
        sum(c.valor) filter (where c.demonstracao = 'BPP' and c.cd_conta = '2.03') as patrimonio_liquido,
        sum(c.valor) filter (where c.demonstracao = 'BPP' and c.cd_conta = '2.01.04') as emprestimos_curto_prazo,
        sum(c.valor) filter (where c.demonstracao = 'BPP' and c.cd_conta = '2.02.01') as emprestimos_longo_prazo
    from contas as c
    inner join documentos_empresa_geral as d
        on c.cnpj = d.cnpj and c.dt_refer = d.dt_refer
    group by c.cnpj, c.dt_refer
),

-- Cada total oficial ao lado da soma das suas contas filhas
conferencia as (
    select
        *,
        receita_liquida + custo_vendas as lucro_bruto_pelas_filhas,
        lucro_bruto + despesas_operacionais as resultado_operacional_pelas_filhas,
        resultado_operacional + resultado_financeiro as lucro_antes_ir_pelas_filhas,
        lucro_antes_ir + ir_csll + coalesce(resultado_descontinuado, 0) as lucro_liquido_pelas_filhas,
        ativo_circulante + ativo_nao_circulante as ativo_total_pelas_filhas,
        passivo_circulante + passivo_nao_circulante + patrimonio_liquido as passivo_total_pelas_filhas
    from pivotado
)

select
    cnpj,
    nome_empresa,
    dt_refer,
    dt_entrega,
    receita_liquida,
    custo_vendas,
    lucro_bruto,
    despesas_operacionais,
    resultado_operacional,
    resultado_financeiro,
    lucro_antes_ir,
    ir_csll,
    lucro_liquido,
    ativo_total,
    ativo_circulante,
    caixa,
    aplicacoes_financeiras,
    passivo_circulante,
    passivo_nao_circulante,
    patrimonio_liquido,
    passivo_total_informado,
    lucro_bruto_pelas_filhas,
    resultado_operacional_pelas_filhas,
    lucro_antes_ir_pelas_filhas,
    lucro_liquido_pelas_filhas,
    ativo_total_pelas_filhas,
    passivo_total_pelas_filhas,
    extract(year from dt_refer)::int as ano,
    coalesce(emprestimos_curto_prazo, 0) + coalesce(emprestimos_longo_prazo, 0) as divida_bruta,
    -- Tolerância: R$ 1.000 ou 0,1% do valor, o que for maior (empresas grandes publicam em milhões arredondados)
    coalesce(
        {{ diverge('lucro_bruto', 'lucro_bruto_pelas_filhas') }}
        or {{ diverge('resultado_operacional', 'resultado_operacional_pelas_filhas') }}
        or {{ diverge('lucro_antes_ir', 'lucro_antes_ir_pelas_filhas') }}
        or {{ diverge('lucro_liquido', 'lucro_liquido_pelas_filhas') }}
        or {{ diverge('ativo_total', 'ativo_total_pelas_filhas') }}
        or {{ diverge('ativo_total', 'passivo_total_pelas_filhas') }},
        true
    ) = false as dados_consistentes
from conferencia
