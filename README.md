# Projeto SP — Data advanced

Plataforma de dados financeiros ponta a ponta: ingestão automatizada → modelagem → camada semântica → agente de IA → machine learning.

> Em construção. Base de dados em definição (CVM ou IF.data/Banco Central).

## Stack (até agora)
- Python 3.13 (ambiente virtual em `~/.venvs/projeto-sp-data`, fora do OneDrive)
- PostgreSQL 17 em Docker (porta 5433)
- Git + GitHub

## Como rodar
Com o Docker Desktop aberto:
```sh
./setup.sh
```
O script cria o `.env` com uma senha aleatória, inicia o Git, cria o ambiente virtual em `~/.venvs/projeto-sp-data`, instala as bibliotecas, sobe o banco e roda `scripts/check_env.py` para conferir tudo. Pode rodar de novo quando quiser.

Depois, para usar o ambiente no Terminal: `source ~/.venvs/projeto-sp-data/bin/activate`.

## Estrutura
| Pasta | Para quê |
|---|---|
| `ingestion/` | Scripts que buscam os dados na fonte |
| `data/raw/` | Arquivos baixados (não vão para o GitHub) |
| `scripts/` | Utilitários, como a checagem do ambiente |

As próximas pastas (modelagem, camada semântica, agente e ML) entram quando chegarmos nelas.
