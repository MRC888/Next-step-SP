# Projeto SP — Data advanced

Plataforma de dados financeiros ponta a ponta: ingestão automatizada → modelagem → camada semântica → agente de IA → machine learning.

> Em construção. Base: dados abertos da **CVM** (demonstrações de companhias abertas).

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

## Ingestão (CVM)
```sh
python ingestion/cvm.py                         # tudo
python ingestion/cvm.py --docs dfp --anos 2025  # só um pedaço
```
- Fontes: DFP (anual, desde 2010), ITR (trimestral, desde 2011) e cadastro de companhias, em `dados.cvm.gov.br`.
- Demonstrações carregadas: BPA, BPP, DRE e DFC (consolidado e individual), mais o índice de documentos.
- Destino: schema `raw` do PostgreSQL, com os dados como vieram da fonte (tudo texto), mais `_arquivo` e `_carregado_em`.
- Só baixa e carrega o que mudou na CVM. A tabela `raw._controle_cargas` guarda a data e o hash de cada arquivo.
- Cada arquivo é carregado numa transação: ou entra inteiro, ou nada muda.
- Cadastro: cada versão nova é guardada (histórico de situação das empresas). Dados pessoais dos responsáveis ficam de fora.
- Os ZIPs ficam em `~/.local/share/projeto-sp-data/raw` (fora do OneDrive). Para mudar, defina `RAW_DIR` no `.env`.

## Estrutura
| Pasta | Para quê |
|---|---|
| `ingestion/` | Scripts que buscam os dados na fonte |
| `scripts/` | Utilitários, como a checagem do ambiente |

As próximas pastas (modelagem, camada semântica, agente e ML) entram quando chegarmos nelas.
