#!/bin/bash
# Roda o pipeline completo sem ninguém mexer (chamado pelo launchd toda semana).
# Abre o Docker, espera o banco, roda "make pipeline" e guarda um log com data.
set -uo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
LOGS="$HOME/Library/Logs/next-step-sp"
mkdir -p "$LOGS"
LOG="$LOGS/pipeline-$(date +%Y-%m-%d).log"

{
  echo "==> Início: $(date)"
  open -a Docker
  for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 5; done
  docker compose up -d
  for _ in $(seq 1 30); do docker compose exec -T postgres sh -c 'pg_isready -q -U "$POSTGRES_USER"' && break; sleep 2; done
  make pipeline
  echo "==> Fim: $(date) · código de saída: $?"
} >> "$LOG" 2>&1
