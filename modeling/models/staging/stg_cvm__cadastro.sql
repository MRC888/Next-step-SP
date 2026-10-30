-- Última foto do cadastro da CVM, com nomes claros e datas tipadas.
with ultima_carga as (
    select max(_carregado_em) as carregado_em from {{ source('cvm', 'cad_cia_aberta') }}
)

select
    c.cnpj_cia as cnpj,
    c.cd_cvm,
    c.denom_social as razao_social,
    c.denom_comerc as nome_comercial,
    c.setor_ativ as setor,
    c.sit as situacao_registro,
    c.motivo_cancel as motivo_cancelamento,
    c.sit_emissor as situacao_emissor,
    c.tp_merc as tipo_mercado,
    c.categ_reg as categoria_registro,
    c.controle_acionario,
    c.uf,
    c.auditor,
    c._carregado_em as dt_carga_cadastro,
    nullif(c.dt_reg, '')::date as dt_registro,
    nullif(c.dt_cancel, '')::date as dt_cancelamento,
    nullif(c.dt_ini_sit_emissor, '')::date as dt_inicio_situacao_emissor
from {{ source('cvm', 'cad_cia_aberta') }} as c
inner join ultima_carga as u on c._carregado_em = u.carregado_em
