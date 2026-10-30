{#- Usa o nome do schema como está (staging, intermediate, marts).
    Sem isso, o dbt criaria "public_staging", "public_marts" etc. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
