-- Base do modelo de risco (Marco D): uma linha por empresa e ano, com sinais do balanço e o alvo.
--
-- Alvo: 1 se a empresa entra em dificuldade financeira (recuperação judicial ou extrajudicial, falência,
-- liquidação) em até N meses DEPOIS de entregar aquele balanço à CVM (N = var horizonte_risco_meses, padrão 24).
-- Sem vazamento de futuro: os sinais vêm só do balanço já público (dt_entrega), e anos em que a empresa
-- já estava em dificuldade saem da base.
-- Atenção: o nome da empresa nos documentos NÃO é histórico. A CVM grava o nome atual em todos os anos
-- (ex.: a DFP 2011 da Americanas já aparece "EM RECUPERAÇÃO JUDICIAL"; a recuperação foi em 2023).
-- Por isso o nome não serve como data do evento nem como filtro.
-- Limitação conhecida: o cadastro da CVM só mostra a situação ATUAL. Empresa que entrou em recuperação e
-- depois saiu aparece como saudável (o alvo fica 0 para ela).

with base as (
    select
        f.cnpj,
        f.nome_empresa,
        f.ano,
        f.dt_refer,
        f.dt_entrega,
        d.setor,
        d.dt_inicio_situacao_emissor as dt_evento,
        f.receita_liquida,
        f.lucro_liquido,
        f.resultado_operacional,
        f.ativo_total,
        f.ativo_circulante,
        f.passivo_circulante,
        f.patrimonio_liquido,
        f.divida_bruta,
        coalesce(d.em_dificuldade_financeira, false) as em_dificuldade,
        f.passivo_circulante + f.passivo_nao_circulante as passivo_exigivel,
        coalesce(f.reservas_de_lucros, 0) + coalesce(f.lucros_acumulados, 0) as lucros_retidos,
        lag(f.receita_liquida) over (partition by f.cnpj order by f.dt_refer) as receita_ano_anterior
    from {{ ref('fct_contas_anuais') }} as f
    left join {{ ref('dim_empresa') }} as d on f.cnpj = d.cnpj
    where f.dados_consistentes and f.ativo_total > 0
),

sinais as (
    select
        cnpj,
        nome_empresa,
        ano,
        dt_refer,
        dt_entrega,
        setor,
        dt_evento,
        em_dificuldade,
        ativo_total,
        -- Componentes do Z'' de Altman (versão para empresas não industriais e mercados emergentes)
        (ativo_circulante - passivo_circulante) / ativo_total as x1_capital_de_giro_sobre_ativo,
        lucros_retidos / ativo_total as x2_lucros_retidos_sobre_ativo,
        resultado_operacional / ativo_total as x3_ebit_sobre_ativo,
        patrimonio_liquido / nullif(passivo_exigivel, 0) as x4_patrimonio_sobre_passivo,
        -- Outros sinais
        ativo_circulante / nullif(passivo_circulante, 0) as liquidez_corrente,
        divida_bruta / ativo_total as divida_sobre_ativo,
        lucro_liquido / ativo_total as roa,
        case when receita_liquida > 0 then lucro_liquido / receita_liquida end as margem_liquida,
        case when receita_ano_anterior > 0 then receita_liquida / receita_ano_anterior - 1 end as crescimento_receita,
        ln(ativo_total) as log_ativo,
        (patrimonio_liquido < 0)::int as patrimonio_negativo,
        (lucro_liquido < 0)::int as teve_prejuizo
    from base
)

select
    cnpj,
    nome_empresa,
    ano,
    dt_refer,
    dt_entrega,
    setor,
    x1_capital_de_giro_sobre_ativo,
    x2_lucros_retidos_sobre_ativo,
    x3_ebit_sobre_ativo,
    x4_patrimonio_sobre_passivo,
    liquidez_corrente,
    divida_sobre_ativo,
    roa,
    margem_liquida,
    crescimento_receita,
    log_ativo,
    patrimonio_negativo,
    teve_prejuizo,
    -- Z'' de Altman: abaixo de 1,1 = zona de perigo; acima de 2,6 = zona segura
    6.56 * x1_capital_de_giro_sobre_ativo
    + 3.26 * x2_lucros_retidos_sobre_ativo
    + 6.72 * x3_ebit_sobre_ativo
    + 1.05 * x4_patrimonio_sobre_passivo as z_altman,
    (
        em_dificuldade
        and dt_evento > dt_entrega
        and dt_evento <= dt_entrega + interval '{{ var("horizonte_risco_meses") }} months'
    )::int as alvo,
    -- A janela de N meses já terminou? Se não, o alvo ainda não é conhecido (não entra no treino nem no teste)
    dt_entrega + interval '{{ var("horizonte_risco_meses") }} months' <= current_date as janela_completa
from sinais
where not (em_dificuldade and dt_evento <= dt_entrega)
