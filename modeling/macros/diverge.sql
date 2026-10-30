{#- Verdadeiro quando dois valores divergem além da tolerância: R$ 1.000 ou 0,1% do valor oficial, o que for maior.
    Usado na conferência dos totais (fct_contas_anuais e teste totais_conferem). -#}
{% macro diverge(oficial, conferido) -%}
    (abs({{ oficial }} - {{ conferido }}) > greatest(1000, abs({{ oficial }}) * 0.001))
{%- endmacro %}
