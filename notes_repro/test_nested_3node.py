"""Properties of the nested 3-node Laplacian diffusion."""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from notes_repro.nested_3node import MONOTONE_TOL, N_NODES, run


@pytest.fixture(scope="module")
def result():
    return run()


def test_graph_has_nine_nodes_and_twelve_edges(result):
    assert result.graph.number_of_nodes() == 9
    assert result.graph.number_of_edges() == 12


def test_tau_is_non_increasing(result):
    assert np.all(np.diff(result.tau) <= MONOTONE_TOL)


def test_mean_of_phi_is_conserved(result):
    drift = np.max(np.abs(result.phi.mean(axis=1) - result.phi0.mean()))
    assert drift < 1e-6


def test_final_spread_is_small(result):
    assert np.ptp(result.phi[-1]) < 1e-2


def test_lambda2_matches_independent_laplacian(result):
    nodelist = list(range(N_NODES))
    adjacency = nx.to_numpy_array(result.graph, nodelist=nodelist)
    independent = np.diag(adjacency.sum(axis=1)) - adjacency
    spectrum = np.sort(np.linalg.eigvalsh(independent))
    np.testing.assert_allclose(result.eigenvalues[1], spectrum[1], rtol=0, atol=0)
