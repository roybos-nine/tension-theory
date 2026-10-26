"""Properties of Tension Game of Life rule v0.1."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from sim.rule import apply_async_sweep, correlation_length, run, step_sync

# Regression values for seed 0, synchronous linear f, 100×100, α = 0.2.
# Rounded tension 0.337, std 0.289 → 0.0057, and mean of T 0.499411 also
# matched a quick independent numpy check run by the Simulaciones agent.
# That check is not in this repo. The t = 1000 tension ~0.00033 quoted
# there is the orthogonal-pair observable; this suite uses Moore pairs.
# See docs/PARAMETERS.md.
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
        assert np.array_equal(first.mean_abs_d1, second.mean_abs_d1, equal_nan=True)
        assert np.array_equal(first.mean_abs_d2, second.mean_abs_d2, equal_nan=True)
        assert np.array_equal(first.xi, second.xi, equal_nan=True)
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
    # Rounded figures from the Simulaciones agent's check named above.
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


def _moore_symbol(wx: float, wy: float) -> float:
    """Fourier symbol of the 8-cell Moore average. Independent of sim.rule."""

    return (
        np.cos(wx) + np.cos(wy) + 2.0 * np.cos(wx) * np.cos(wy)
    ) / 4.0


def test_fourier_mode_decays_at_the_analytic_rate():
    """One long-wave cosine is an eigenmode of the synchronous linear rule."""

    width = height = 32
    wx = 2.0 * np.pi / width
    lam = _moore_symbol(wx, 0.0)
    alpha = 0.2
    gain = 1.0 + alpha * (lam - 1.0)
    assert abs(gain) < 1.0
    amplitude = 0.02
    x = np.arange(width)[:, None]
    field = 0.5 + amplitude * np.cos(wx * x) * np.ones((1, height))
    got = field
    for _ in range(10):
        got, clamps = step_sync(got, alpha=alpha, f="linear", k=1.0)
        assert clamps == 0
    expected = 0.5 + amplitude * (gain ** 10) * np.cos(wx * x) * np.ones((1, height))
    assert got == pytest.approx(expected, abs=1e-12)


def test_even_grid_stripe_changes_stability_at_four_thirds():
    """λ = −1/2 for a period-2 stripe, so the unclamped gain crosses −1 at α = 4/3."""

    lam = -0.5
    assert 2.0 / (1.0 - lam) == pytest.approx(4.0 / 3.0)
    height = 16
    amplitude = 1e-4
    stripe = ((-1.0) ** np.arange(height))[None, :]
    field = 0.5 + amplitude * stripe * np.ones((height, 1))
    below_alpha = 4.0 / 3.0 - 0.05
    above_alpha = 4.0 / 3.0 + 0.05
    below, below_clamps = step_sync(field, alpha=below_alpha, f="linear", k=1.0)
    above, above_clamps = step_sync(field, alpha=above_alpha, f="linear", k=1.0)
    assert below_clamps == 0 and above_clamps == 0
    gain_below = 1.0 + below_alpha * (lam - 1.0)
    gain_above = 1.0 + above_alpha * (lam - 1.0)
    assert abs(gain_below) < 1.0 < abs(gain_above)
    assert float(below[0, 0] - 0.5) == pytest.approx(amplitude * gain_below, abs=1e-14)
    assert float(above[0, 0] - 0.5) == pytest.approx(amplitude * gain_above, abs=1e-14)


def test_tanh_small_stripe_is_controlled_by_alpha_times_k():
    height = 16
    amplitude = 1e-6
    field = 0.5 + amplitude * ((-1.0) ** np.arange(height))[None, :] * np.ones((height, 1))
    alpha = 0.2
    k = 3.0
    lam = -0.5
    gain = 1.0 + alpha * k * (lam - 1.0)
    got, clamps = step_sync(field, alpha=alpha, f="tanh", k=k)
    assert clamps == 0
    assert float(got[0, 0] - 0.5) == pytest.approx(amplitude * gain, abs=1e-15)


def test_odd_grid_has_a_milder_most_negative_symbol():
    """Both sides odd: π is not a grid frequency, so λ_min > −1/2."""

    side = 15
    wy = 2.0 * np.pi * 7 / side
    lam = _moore_symbol(0.0, wy)
    assert lam > -0.5
    assert 2.0 / (1.0 - lam) > 4.0 / 3.0
    amplitude = 1e-4
    alpha = 0.2
    profile = np.cos(wy * np.arange(side))
    field = 0.5 + amplitude * profile[None, :] * np.ones((side, 1))
    got, clamps = step_sync(field, alpha=alpha, f="linear", k=1.0)
    assert clamps == 0
    gain = 1.0 + alpha * (lam - 1.0)
    expected = 0.5 + amplitude * gain * profile[None, :] * np.ones((side, 1))
    assert got == pytest.approx(expected, abs=1e-12)


def test_sync_above_threshold_is_a_period_two_oscillation():
    result = run(0, W=32, H=32, alpha=1.5, steps=80, mode="sync")
    assert result.mean_tension[-1] > 0.5
    assert result.mean_abs_d1[-1] > 0.5
    assert result.mean_abs_d2[-1] < 0.02
    assert result.clamp_activations > 0


def test_async_linear_update_does_not_conserve_the_mean():
    field = np.full((4, 4), 0.2, dtype=np.float64)
    field[1, 1] = 0.8
    total = float(field.sum())
    apply_async_sweep(field, np.array([1 * 4 + 1]), alpha=0.5, f="linear", k=1.0)
    assert abs(float(field.sum()) - total) > 1e-6


def test_tanh_sync_does_not_conserve_the_mean():
    field = np.zeros((6, 6), dtype=np.float64)
    field[2, 2] = 1.0
    updated, _ = step_sync(field, alpha=0.2, f="tanh", k=1.0)
    assert abs(float(updated.mean() - field.mean())) > 1e-4


def test_correlation_length_of_pure_modes():
    side = 32
    x = np.arange(side)[:, None]
    cosine = np.cos(2.0 * np.pi * x / side) * np.ones((1, side))
    assert correlation_length(cosine) == pytest.approx(float(side), rel=1e-6)
    stripe = ((-1.0) ** np.arange(side))[None, :] * np.ones((side, 1))
    assert correlation_length(stripe) == pytest.approx(2.0, rel=1e-6)
    assert np.isnan(correlation_length(np.full((8, 8), 0.3)))


def test_grid_sides_must_be_at_least_3():
    with pytest.raises(ValueError, match=">= 3"):
        run(0, W=2, H=8, steps=0)
    with pytest.raises(ValueError, match=">= 3"):
        step_sync(np.zeros((8, 2)))


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
    assert text[0] == "step,mean_tension,mean_T,std_T,mean_abs_d1,mean_abs_d2,xi"
    assert len(text) == 4  # header + steps 0, 1, 2
    initial = text[1].split(",")
    assert initial[4] == "nan"
    assert initial[5] == "nan"
    assert initial[6] != "nan"
    assert (tmp_path / "seed0_sync_linear_final.png").is_file()
    assert (tmp_path / "seed0_sync_linear_tension.png").is_file()
    assert (tmp_path / "seed0_sync_linear_hist.png").is_file()
