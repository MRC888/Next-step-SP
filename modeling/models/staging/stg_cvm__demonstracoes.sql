{#-
    Junta as 20 tabelas de demonstrações do raw (DFP/ITR x BPA, BPP, DRE, DFC x consolidado/individual)
    numa só, com os tipos certos e os valores em reais.
    Quais documentos entram vem da variável `docs` (dbt_project.yml).
-#}
{%- set tabelas = [] -%}
{%- for doc in var('docs') -%}
    {%- for dem in ['bpa', 'bpp', 'dre', 'dfc_md', 'dfc_mi'] -%}
        {%- for escopo in ['con', 'ind'] -%}
            {%- do tabelas.append((doc, dem, escopo)) -%}
        {%- endfor -%}
    {%- endfor -%}
{%- endfor -%}

{% for doc, dem, escopo in tabelas %}
    select
        '{{ doc | upper }}' as tipo_doc,
        '{{ dem | upper }}' as demonstracao,
        '{{ escopo }}' as escopo,
        cnpj_cia as cnpj,
        cd_cvm,
        denom_cia as nome_empresa,
        dt_refer::date as dt_refer,
        versao::int as versao,
        ordem_exerc,
        {#- Balanço é uma foto numa data: não tem início de período. -#}
        {% if dem in ['bpa', 'bpp'] %}
            null::date{% else %}
            dt_ini_exerc::date{% endif %} as dt_ini_exerc,
        dt_fim_exerc::date as dt_fim_exerc,
        cd_conta,
        ds_conta,
        -- A CVM informa a escala (MIL ou UNIDADE); convertemos tudo para reais.
        -- Exceção: lucro por ação (3.99) já vem em R$ por ação, mesmo quando o arquivo diz MIL.
        vl_conta::numeric * case when escala_moeda = 'MIL' and cd_conta not like '3.99%' then 1000 else 1 end as valor,
        st_conta_fixa = 'S' as conta_fixa,
        _arquivo
    from {{ source('cvm', doc ~ '_' ~ dem ~ '_' ~ escopo) }}
    {% if not loop.last %}union all{% endif %}
{% endfor %}
