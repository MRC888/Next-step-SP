"""Configuração dos testes.

Testes marcados com @pytest.mark.banco precisam do PostgreSQL do projeto no ar (só no Mac).
Sem banco (ex.: no GitHub Actions), eles são pulados automaticamente.
"""

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _banco_no_ar() -> bool:
    try:
        from agent import ferramentas

        with ferramentas._conectar() as conn:
            conn.execute("select 1")
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    if _banco_no_ar():
        return
    pular = pytest.mark.skip(reason="banco do projeto fora do ar")
    for item in items:
        if "banco" in item.keywords:
            item.add_marker(pular)
