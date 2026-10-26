"""Properties of Tension Game of Life rule v0.1."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from sim.rule import (
    apply_async_sweep,
    mean_tension,
    moore_pair_energy,
    neighbor_mean,
    run,
    spectral_length,
    step_sync,
)

# Regression values for seed 0, synchronous linear f, 100×100, α = 0.2.
# Rounded tension 0.337, std 0.289 → 0.0057, and mean of T 0.499411 also
# matched a quick numpy check run by the same Simulaciones agent.
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
        assert np.array_equal(first.spectral_length, second.spectral_length, equal_nan=True)
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
    """Fourier symbol of the 8-cell Moore average, written out in this test."""

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


def test_spectral_length_of_pure_modes():
    side = 32
    x = np.arange(side)[:, None]
    cosine = np.cos(2.0 * np.pi * x / side) * np.ones((1, side))
    assert spectral_length(cosine) == pytest.approx(float(side), rel=1e-6)
    stripe = ((-1.0) ** np.arange(side))[None, :] * np.ones((side, 1))
    assert spectral_length(stripe) == pytest.approx(2.0, rel=1e-6)
    assert np.isnan(spectral_length(np.full((8, 8), 0.3)))


def test_spectral_length_floor_and_domain_wall():
    """Flat-spectrum floor is √6. One wall grows like √N, not the stripe's 2."""

    import math

    side = 256
    kx = 2.0 * math.pi * np.fft.fftfreq(side)
    ky = 2.0 * math.pi * np.fft.fftfreq(side)
    k2 = kx[:, None] ** 2 + ky[None, :] ** 2
    k2 = np.array(k2, copy=True)
    k2[0, 0] = 0.0
    flat = (2.0 * math.pi) / math.sqrt(float(k2.sum()) / (side * side - 1))
    assert flat == pytest.approx(math.sqrt(6.0), rel=1e-3)

    def wall(n: int) -> np.ndarray:
        field = np.zeros((n, n), dtype=np.float64)
        field[: n // 2, :] = 1.0
        return field

    wall_32 = spectral_length(wall(32))
    wall_128 = spectral_length(wall(128))
    assert wall_32 == pytest.approx(10.6852, rel=1e-4)
    assert wall_128 == pytest.approx(21.3473, rel=1e-4)
    assert wall_128 / wall_32 == pytest.approx(math.sqrt(128 / 32), rel=1e-2)
    assert wall_32 > 2.0


def _stripe_amplitude(alpha: float, k: float) -> float:
    """Nonzero root of 2A = α tanh(3 k A / 2), or 0 when that root is absent."""

    if alpha * k <= 4.0 / 3.0:
        return 0.0
    amplitude = 0.05
    slope = 1.5 * k
    for _ in range(30):
        response = np.tanh(slope * amplitude)
        residual = alpha * response - 2.0 * amplitude
        derivative = alpha * slope * (1.0 - response * response) - 2.0
        amplitude -= float(residual / derivative)
    return float(amplitude)


def test_tanh_period2_stripe_amplitude_is_set_by_alpha():
    """Pure stripe: 2A = α tanh(3 k A / 2), and mean tension is 1.5 A."""

    alpha = 0.2
    k = 8.0
    amplitude = _stripe_amplitude(alpha, k)
    assert amplitude == pytest.approx(0.0658569660405754, rel=1e-12)
    assert 2.0 * amplitude == pytest.approx(alpha * np.tanh(1.5 * k * amplitude), rel=1e-12)
    assert _stripe_amplitude(0.05, k) == 0.0
    side = 32
    sigma = ((-1.0) ** np.arange(side))[None, :]
    field = np.full((side, side), 0.5) + amplitude * sigma
    assert mean_tension(field) == pytest.approx(1.5 * amplitude, rel=1e-12)
    assert mean_tension(field) == pytest.approx(0.0987854490608631, rel=1e-12)
    updated, clamps = step_sync(field, alpha=alpha, f="tanh", k=k)
    assert clamps == 0
    assert updated == pytest.approx(np.full((side, side), 0.5) - amplitude * sigma, abs=1e-12)


def _cell_energy_change(field: np.ndarray, x: int, y: int, alpha: float, *, f: str, k: float):
    before = moore_pair_energy(field)
    delta = float(neighbor_mean(field)[x, y] - field[x, y])
    if f == "linear":
        raw = field[x, y] + alpha * delta
    else:
        raw = field[x, y] + alpha * np.tanh(k * delta)
    updated = float(min(1.0, max(0.0, raw)))
    moved = field.copy()
    moved[x, y] = updated
    return moore_pair_energy(moved) - before, delta, updated - float(field[x, y])


def test_unclamped_linear_cell_energy_identity():
    rng = np.random.default_rng(1)
    # Small contrast, so α = 2.05 does not reach the clamp and the equality applies.
    field = 0.5 + 0.01 * rng.random((8, 8))
    for alpha in (0.2, 1.5, 1.99, 2.0, 2.05):
        change, delta, step = _cell_energy_change(field, 3, 4, alpha, f="linear", k=1.0)
        assert 0.0 < field[3, 4] + step < 1.0
        predicted = -alpha * (1.0 - alpha / 2.0) * delta * delta
        assert change == pytest.approx(predicted, abs=1e-12)


def test_clamp_breaks_the_energy_equality_and_keeps_the_sign_up_to_2():
    field = np.full((8, 8), 0.2)
    field[3, 4] = 0.98
    change, delta, step = _cell_energy_change(field, 3, 4, 1.5, f="linear", k=1.0)
    unclamped = -1.5 * (1.0 - 1.5 / 2.0) * delta * delta
    assert step != pytest.approx(1.5 * delta, rel=1e-6)
    assert change < 0.0
    assert change != pytest.approx(unclamped, rel=1e-3)

    near = np.full((8, 8), 0.4)
    near[3, 4] = 0.4 + 1e-4
    small, small_delta, _ = _cell_energy_change(near, 3, 4, 0.2, f="tanh", k=12.0)
    assert small > 0.0
    bounded, _, _ = _cell_energy_change(near, 3, 4, 0.2, f="tanh", k=10.0)
    assert bounded <= 0.0
    assert small_delta != 0.0


def test_async_linear_1_99_decays_and_2_05_does_not():
    """Fixed seeds 0 and 1. α = 1.99 decays; α = 2.05 does not."""

    for seed in (0, 1):
        low = run(seed, W=32, H=32, alpha=1.99, steps=200, mode="async")
        high = run(seed, W=32, H=32, alpha=2.05, steps=200, mode="async")
        assert low.mean_tension[-1] < 0.05
        assert low.mean_tension[-1] < low.mean_tension[0] / 5.0
        assert moore_pair_energy(low.grid) < 1.0
        assert high.mean_tension[-1] > 0.15
        assert high.mean_tension[-1] > high.mean_tension[0] / 2.0
        assert moore_pair_energy(high.grid) > 10.0


def test_nonpositive_alpha_does_not_decay_the_stripe():
    height = 16
    amplitude = 1e-4
    stripe = ((-1.0) ** np.arange(height))[None, :]
    field = 0.5 + amplitude * stripe * np.ones((height, 1))
    frozen, clamps = step_sync(field, alpha=0.0, f="linear", k=1.0)
    assert clamps == 0
    assert frozen == pytest.approx(field)
    grown, grown_clamps = step_sync(field, alpha=-0.1, f="linear", k=1.0)
    assert grown_clamps == 0
    assert abs(float(grown[0, 0] - 0.5)) > amplitude


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
    assert text[0] == "step,mean_tension,mean_T,std_T,mean_abs_d1,mean_abs_d2,spectral_length"
    assert len(text) == 4  # header + steps 0, 1, 2
    initial = text[1].split(",")
    assert initial[4] == "nan"
    assert initial[5] == "nan"
    assert initial[6] != "nan"
    assert (tmp_path / "seed0_sync_linear_final.png").is_file()
    assert (tmp_path / "seed0_sync_linear_tension.png").is_file()
    assert (tmp_path / "seed0_sync_linear_hist.png").is_file()


def test_sweep_omits_nonpositive_values_and_marks_async_alpha_2(tmp_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    from sim.sweep import ASYNC_ALPHA_MARK, _draw, _mark_thresholds, _mask_nonpositive

    masked = _mask_nonpositive([1.0, 0.0, -1.0, 1e-20])
    assert masked[0] == 1.0
    assert np.isnan(masked[1]) and np.isnan(masked[2])
    assert masked[3] == 1e-20

    fig, ax = plt.subplots()
    _mark_thresholds(ax, async_panel=True)
    positions = [float(line.get_xdata()[0]) for line in ax.lines if isinstance(line, Line2D)]
    assert any(abs(position - ASYNC_ALPHA_MARK) < 1e-12 for position in positions)
    assert any(abs(position - 4.0 / 3.0) < 1e-12 for position in positions)
    plt.close(fig)

    rows = []
    for alpha in (0.2, 2.5):
        for seed in (0, 1):
            for mode in ("sync", "async"):
                rows.append(
                    {
                        "seed": seed,
                        "alpha": alpha,
                        "mode": mode,
                        "f": "linear",
                        "k": 1.0,
                        "ak": alpha,
                        "tension": 0.1 if alpha == 2.5 else 0.0,
                        "d1": 0.0,
                        "d2": 1e-18,
                        "clamps": 0,
                    }
                )
            rows.append(
                {
                    "seed": seed,
                    "alpha": alpha,
                    "mode": "sync",
                    "f": "tanh",
                    "k": 1.0,
                    "ak": alpha,
                    "tension": 0.2,
                    "d1": 0.2,
                    "d2": 0.0,
                    "clamps": 0,
                }
            )
            rows.append(
                {
                    "seed": seed,
                    "alpha": 0.2,
                    "mode": "sync",
                    "f": "tanh",
                    "k": alpha / 0.2,
                    "ak": alpha,
                    "tension": 0.2,
                    "d1": 0.2,
                    "d2": 0.2,
                    "clamps": 0,
                }
            )
        rows.append(
            {
                "seed": 0,
                "alpha": alpha,
                "mode": "async",
                "f": "tanh",
                "k": 1.0,
                "ak": alpha,
                "tension": 0.0,
                "d1": 0.1,
                "d2": 0.1,
                "clamps": 0,
            }
        )
    path = tmp_path / "sweep.png"
    _draw(rows, path)
    assert path.is_file()
    assert path.stat().st_size > 0


def test_reproduce_command_names_version_and_seeds():
    completed = subprocess.run(
        [sys.executable, "-m", "sim.reproduce", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    text = completed.stdout
    assert "v0.1" in text
    assert "seed 0" in text
    assert "k=8" in text
    assert "seeds 0 and 1" in text
