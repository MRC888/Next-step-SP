"""Métricas de avaliação do modelo de risco."""

import numpy as np
import pytest

from ml.treinar import _limitar_extremos, _metricas


def test_limita_razoes_absurdas():
    assert list(_limitar_extremos(np.array([-500.0, 0.5, 1e6]))) == [-10, 0.5, 10]


def test_recall_no_top10_com_nota_continua():
    alvo = np.array([1] + [0] * 19)
    nota = np.linspace(1, 0, 20)  # o único caso real tem a maior nota
    resultado = _metricas(alvo, nota)
    assert resultado["auc"] == pytest.approx(1.0)
    assert resultado["recall_top10"] == pytest.approx(1.0)


def test_recall_vazio_em_regua_de_sim_ou_nao():
    alvo = np.array([1, 0, 0, 1, 0, 0, 0, 0, 0, 0])
    regua = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    assert _metricas(alvo, regua)["recall_top10"] is None
