"""Confere se o ambiente do projeto está pronto. Rode: python scripts/check_env.py"""
import os
import shutil
import subprocess
import sys

ok = True


def check(nome, passou, dica=""):
    global ok
    print(f"[{'OK' if passou else 'FALTA'}] {nome}" + ("" if passou else f"  -> {dica}"))
    ok = ok and passou


check("Python 3.11+", sys.version_info >= (3, 11), "instale Python 3.11 ou mais novo")
check("Ambiente virtual ativo", sys.prefix != sys.base_prefix, "rode: source ~/.venvs/projeto-sp-data/bin/activate")
check("Git", shutil.which("git") is not None, "rode: xcode-select --install")
docker = shutil.which("docker") is not None
check("Docker instalado", docker, "instale o Docker Desktop")
if docker:
    rodando = subprocess.run(["docker", "info"], capture_output=True).returncode == 0
    check("Docker rodando", rodando, "abra o app Docker Desktop")

try:
    from dotenv import load_dotenv
    import psycopg

    load_dotenv()
    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
        connect_timeout=5,
    ) as conn:
        versao = conn.execute("select version()").fetchone()[0]
    check(f"Banco acessível ({versao.split(',')[0]})", True)
except ImportError:
    check("Bibliotecas Python", False, "rode: pip install -r requirements.txt")
except Exception as erro:
    check("Banco acessível", False, f"suba o banco com: docker compose up -d  ({erro.__class__.__name__})")

print("\nTudo pronto!" if ok else "\nAinda falta algo acima.")
