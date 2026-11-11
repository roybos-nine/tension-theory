"""Laplacian diffusion on three 3-node cycles joined in an outer cycle.

Reproduces the note "Simulate the nested 3-node subgraphs":
https://app.notion.com/p/84a7f2846fba8282812f81f2fd39a6f9

NetworkX 2.4 removed ``Graph.add_cycle``. Cycles are added with ``nx.add_cycle``.
"""

from __future__ import annotations

from typing import NamedTuple

import networkx as nx
import numpy as np
from scipy.integrate import odeint

SEED = 42
N_NODES = 9
T_END = 10.0
N_TIMES = 100
SUBCYCLES = ((0, 1, 2), (3, 4, 5), (6, 7, 8))
OUTER_EDGES = ((2, 3), (5, 6), (8, 0))
MONOTONE_TOL = 1e-12


class RunResult(NamedTuple):
    t: np.ndarray
    phi: np.ndarray
    phi0: np.ndarray
    tau: np.ndarray
    eigenvalues: np.ndarray
    laplacian: np.ndarray
    graph: nx.Graph


def build_graph() -> nx.Graph:
    graph = nx.Graph()
    for cycle in SUBCYCLES:
        nx.add_cycle(graph, cycle)
    graph.add_edges_from(OUTER_EDGES)
    return graph


def laplacian_matrix(graph: nx.Graph) -> np.ndarray:
    return nx.laplacian_matrix(graph, nodelist=range(N_NODES)).astype(float).toarray()


def initial_state(seed: int = SEED) -> np.ndarray:
    """Random potentials in [-1, 1] from the legacy NumPy seed stream."""
    rng_state = np.random.get_state()
    np.random.seed(seed)
    phi0 = np.random.rand(N_NODES) * 2 - 1
    np.random.set_state(rng_state)
    return phi0


def run(seed: int = SEED) -> RunResult:
    """Integrate dphi/dt = -L phi and return the trajectories and spectrum."""
    graph = build_graph()
    laplacian = laplacian_matrix(graph)
    phi0 = initial_state(seed)
    t = np.linspace(0.0, T_END, N_TIMES)
    phi = odeint(lambda state, _time: -laplacian @ state, phi0, t)
    tau = 0.5 * np.einsum("ti,ij,tj->t", phi, laplacian, phi)
    eigenvalues = np.sort(np.linalg.eigvalsh(laplacian))
    return RunResult(t, phi, phi0, tau, eigenvalues, laplacian, graph)


def format_summary(result: RunResult) -> str:
    line = (
        "Tau0=%.4f Tau(t=10)=%.3e mean=%.4f final_spread=%.2e lambda2=%.4f"
        % (
            result.tau[0],
            result.tau[-1],
            result.phi0.mean(),
            np.ptp(result.phi[-1]),
            result.eigenvalues[1],
        )
    )
    monotone = bool(np.all(np.diff(result.tau) <= MONOTONE_TOL))
    return f"{line}\nmonotone decreasing: {monotone}"


def main() -> None:
    print(format_summary(run()))


if __name__ == "__main__":
    main()
