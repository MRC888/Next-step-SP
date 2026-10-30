# Next Step SP: comandos do projeto. Rode "make" (ou "make ajuda") para ver a lista.
# Tudo usa o ambiente Python do projeto, fora do OneDrive.

VENV := $(HOME)/.venvs/projeto-sp-data/bin
PY := $(VENV)/python
DBT := cd modeling && $(VENV)/dbt
export PATH := $(HOME)/.docker/bin:$(PATH)

.DEFAULT_GOAL := ajuda
.PHONY: ajuda setup banco ingestao modelagem modelagem-dfp conferir risco pipeline dashboard agente avaliar-agente testes lint docs agendar

ajuda: ## Lista os comandos
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  make %-16s %s\n", $$1, $$2}'

setup: ## Prepara o ambiente do zero (banco, venv, bibliotecas)
	./setup.sh

banco: ## Liga o Docker e o banco
	open -a Docker && docker compose up -d

ingestao: ## Baixa da CVM só o que mudou e carrega no schema raw
	$(PY) ingestion/cvm.py

modelagem: ## Limpa e testa os dados (dbt build, DFP + ITR, ~4 min)
	$(DBT) build

modelagem-dfp: ## Limpa e testa só os balanços anuais (DFP), mais rápido
	$(DBT) build --vars '{docs: [dfp]}'

conferir: ## Confere as métricas do MetricFlow contra o cálculo à mão (raw)
	$(PY) scripts/conferir_metricas.py

risco: ## Treina e avalia o modelo de risco (walk-forward) e grava ml.risco_atual
	$(PY) -W ignore -m ml.treinar

pipeline: ingestao modelagem conferir risco ## Tudo, em ordem: ingestão, modelagem, conferência e risco

dashboard: ## Abre o painel no navegador
	$(VENV)/streamlit run dashboard/app.py

agente: ## Pergunta ao agente: make agente P="Qual a margem líquida da WEG em 2025?"
	$(PY) -m agent.agente "$(P)"

avaliar-agente: ## Roda a prova de 20 perguntas do agente (usa a API, custa ~US$ 2)
	$(PY) -m agent.avaliacao.avaliar

testes: ## Testes automáticos (os que precisam do banco são pulados se ele estiver fora do ar)
	$(VENV)/pytest -q

lint: ## Ruff, SQLFluff e as checagens do pre-commit em todos os arquivos
	$(VENV)/pre-commit run --all-files

docs: ## Gera e abre a documentação do dbt (linhagem dos modelos)
	$(DBT) docs generate && $(VENV)/dbt docs serve --port 8081

agendar: ## Agenda o pipeline toda segunda às 7h (launchd do macOS)
	./scripts/agendar.sh
