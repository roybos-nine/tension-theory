"""Properties of Tension Game of Life rule v0.1."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from sim.rule import apply_async_sweep, run, step_sync

# Precise seed-0 synchronous linear trajectory on a 100×100 grid.
# An independent NumPy sketch reported the same initial field at the
# quoted rounding: mean tension 0.337, std 0.289, mean of T 0.499411.
REFERENCE_MEAN_TENSION_0 = 0.33693409976426275
REFERENCE_MEAN_TENSION_100 = 0.0036387817188235205
REFERENCE_MEAN_TENSION_1000 = 0.00039892833656968895
REFERENCE_STD_0 = 0.28905043243145806
REFERENCE_STD_1000 = 0.0056725176620501735
REFERENCE_MEAN_T = 0.49941066006080853


@pytest.fixture(scope="module")
def seed0_sync():
    return run(0)


def test_mean_of_T_conserved_for_linear_sync_without_clamp(seed0_sync):
    """Linear synchronous updates are a convex combination when the clamp is idle."""

    assert seed0_sync.clamp_activations == 0
    assert np.max(np.abs(seed0_sync.mean_T - seed0_sync.mean_T[0])) < 1e-12
    assert seed0_sync.grid.min() >= 0.0
    assert seed0_sync.grid.max() <= 1.0


def test_uniform_field_is_fixed_and_conserves_its_mean():
    field = np.full((6, 6), 0.4, dtype=np.float64)
    updated, clamps = step_sync(field, alpha=0.2, f="linear", k=1.0)
    assert clamps == 0
    assert np.all(updated == field)


def test_mean_tension_non_increasing_for_linear_sync(seed0_sync):
    increments = np.diff(seed0_sync.mean_tension)
    assert np.max(increments) <= 1e-15


def test_determinism_same_seed_same_output():
    for mode in ("sync", "async"):
        first = run(0, W=24, H=24, steps=4, mode=mode)
        second = run(0, W=24, H=24, steps=4, mode=mode)
        assert np.array_equal(first.grid, second.grid)
        assert np.array_equal(first.mean_tension, second.mean_tension)
        assert np.array_equal(first.mean_T, second.mean_T)
        other = run(1, W=24, H=24, steps=4, mode=mode)
        assert not np.array_equal(first.grid, other.grid)


def test_locality_distant_cell_does_not_affect_one_sync_step():
    """A synchronous step at (x, y) reads only (x, y) and its Moore neighbours."""

    field = np.zeros((12, 12), dtype=np.float64)
    field[5, 5] = 1.0
    updated, clamps = step_sync(field, alpha=0.2, f="linear", k=1.0)
    assert clamps == 0
    assert updated[5, 5] == pytest.approx(0.8)
    assert updated[5, 6] == pytest.approx(0.025)
    assert updated[6, 6] == pytest.approx(0.025)
    # Chebyshev distance 2 is outside the Moore neighbourhood.
    assert updated[5, 7] == 0.0
    assert updated[7, 7] == 0.0

    rng = np.random.default_rng(2)
    base = rng.random((9, 9))
    distant = base.copy()
    distant[0, 0] = 0.0 if base[0, 0] > 0.5 else 1.0
    neighbour = base.copy()
    neighbour[4, 5] = 0.0 if base[4, 5] > 0.5 else 1.0
    base_next, _ = step_sync(base, alpha=0.2, f="linear", k=1.0)
    distant_next, _ = step_sync(distant, alpha=0.2, f="linear", k=1.0)
    neighbour_next, _ = step_sync(neighbour, alpha=0.2, f="linear", k=1.0)
    assert distant_next[4, 4] == base_next[4, 4]
    assert neighbour_next[4, 4] != base_next[4, 4]


def test_reference_seed0_sync_linear(seed0_sync):
    assert seed0_sync.mean_tension[0] == pytest.approx(REFERENCE_MEAN_TENSION_0, abs=1e-12)
    assert seed0_sync.mean_tension[100] == pytest.approx(REFERENCE_MEAN_TENSION_100, abs=1e-12)
    assert seed0_sync.mean_tension[1000] == pytest.approx(REFERENCE_MEAN_TENSION_1000, abs=1e-12)
    assert seed0_sync.std_T[0] == pytest.approx(REFERENCE_STD_0, abs=1e-12)
    assert seed0_sync.std_T[1000] == pytest.approx(REFERENCE_STD_1000, abs=1e-12)
    assert seed0_sync.mean_T[0] == pytest.approx(REFERENCE_MEAN_T, abs=1e-12)
    assert seed0_sync.mean_T[1000] == pytest.approx(REFERENCE_MEAN_T, abs=1e-12)
    # Rounded the way the independent sketch quoted them.
    assert round(float(seed0_sync.mean_tension[0]), 3) == 0.337
    assert round(float(seed0_sync.std_T[0]), 3) == 0.289
    assert round(float(seed0_sync.std_T[1000]), 4) == 0.0057
    assert round(float(seed0_sync.mean_T[0]), 6) == 0.499411


def test_async_sweep_matches_explicit_cell_formula():
    rng = np.random.default_rng(7)
    field = rng.random((5, 6))
    order = rng.permutation(field.size)
    expected = field.copy()
    width, height = expected.shape
    alpha = 0.2
    for index in order:
        x = int(index) // height
        y = int(index) - x * height
        neighbour_sum = 0.0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                neighbour_sum += expected[(x + dx) % width, (y + dy) % height]
        delta = neighbour_sum / 8.0 - expected[x, y]
        updated = expected[x, y] + alpha * delta
        expected[x, y] = min(1.0, max(0.0, updated))

    got = field.copy()
    apply_async_sweep(got, order, alpha=alpha, f="linear", k=1.0)
    assert np.array_equal(got, expected)


def test_tanh_k_changes_the_update():
    field = np.zeros((5, 5), dtype=np.float64)
    field[2, 2] = 1.0
    mild, _ = step_sync(field, alpha=0.2, f="tanh", k=1.0)
    steep, _ = step_sync(field, alpha=0.2, f="tanh", k=8.0)
    assert mild[2, 2] != steep[2, 2]


def test_seed_is_required_and_explicit():
    with pytest.raises(TypeError):
        run()  # type: ignore[call-arg]


def test_cli_requires_seed():
    completed = subprocess.run(
        [sys.executable, "-m", "sim"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "seed" in completed.stderr.lower()


def test_cli_writes_csv_and_pngs(tmp_path: Path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "sim",
            "--seed",
            "0",
            "--steps",
            "2",
            "--width",
            "8",
            "--height",
            "8",
            "--out",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    csv_path = tmp_path / "seed0_sync_linear.csv"
    text = csv_path.read_text().splitlines()
    assert text[0] == "step,mean_tension,mean_T,std_T"
    assert len(text) == 4  # header + steps 0, 1, 2
    assert (tmp_path / "seed0_sync_linear_final.png").is_file()
    assert (tmp_path / "seed0_sync_linear_tension.png").is_file()
