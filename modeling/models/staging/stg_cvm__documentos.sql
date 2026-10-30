-- Índice dos documentos entregues à CVM. A data de entrega importa para o ML:
-- o modelo só pode "saber" de um balanço depois que ele foi publicado.
{% for doc in var('docs') %}
    select
        '{{ doc | upper }}' as tipo_doc,
        cnpj_cia as cnpj,
        dt_refer::date as dt_refer,
        versao::int as versao,
        id_doc,
        dt_receb::date as dt_entrega,
        link_doc
    from {{ source('cvm', doc ~ '_documentos') }}
    {% if not loop.last %}union all{% endif %}
{% endfor %}
