#!/bin/bash
# Prepara o ambiente do projeto do zero. Pode rodar quantas vezes quiser: o que já existe é mantido.
set -e
cd "$(dirname "$0")"

# O ambiente Python fica fora do OneDrive (mesmo padrão do Foods and Goods), para não sincronizar as bibliotecas.
VENV="$HOME/.venvs/projeto-sp-data"

# Mac: python3.13 e venv/bin. Windows (Git Bash): launcher "py" e venv/Scripts.
case "$(uname -s)" in
  MINGW* | MSYS* | CYGWIN*)
    PY="py -3.13"
    BIN="$VENV/Scripts"
    ;;
  *)
    PY=$(command -v python3.13 || command -v python3)
    BIN="$VENV/bin"
    ;;
esac
echo "==> Python: $($PY --version)"

if ! command -v docker >/dev/null; then
  echo "ERRO: Docker não encontrado. Instale e abra o Docker Desktop, depois rode este script de novo."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERRO: o Docker está instalado, mas não está rodando. Abra o app Docker Desktop e espere a baleia ficar estável."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  SENHA=$($PY -c 'import secrets; print(secrets.token_urlsafe(18))')
  # -i.bak funciona no sed do Mac e no do Git Bash; o backup é apagado logo depois.
  sed -i.bak "s/troque-esta-senha/$SENHA/" .env && rm .env.bak
  echo "==> .env criado com uma senha aleatória (veja dentro do arquivo .env)"
fi

[ -d .git ] || { git init -b main >/dev/null; echo "==> Repositório Git iniciado"; }

if [ ! -d "$VENV" ]; then
  mkdir -p "$HOME/.venvs"
  $PY -m venv "$VENV"
  echo "==> Ambiente virtual criado em $VENV"
fi
"$BIN/python" -m pip install -q --upgrade pip
"$BIN/python" -m pip install -q -r requirements.txt
echo "==> Bibliotecas instaladas"

docker compose up -d
echo "==> Aguardando o banco ficar pronto..."
for i in $(seq 1 30); do
  # -U com o usuário do projeto; sem ele o pg_isready usa "root" e suja o log com "role root does not exist".
  docker compose exec -T postgres sh -c 'pg_isready -q -U "$POSTGRES_USER"' && break
  sleep 2
done

echo
"$BIN/python" scripts/check_env.py
