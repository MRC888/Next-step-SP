-- Falha se existir mais de uma linha para a mesma empresa, documento, demonstração, período e conta.
select
    tipo_doc,
    demonstracao,
    cnpj,
    dt_refer,
    dt_ini_exerc,
    dt_fim_exerc,
    cd_conta,
    count(*) as linhas
from {{ ref('fct_demonstracoes') }}
group by 1, 2, 3, 4, 5, 6, 7
having count(*) > 1
