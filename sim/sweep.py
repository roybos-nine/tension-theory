"""Stability sweep for rule v0.1.

``python -m sim.sweep`` writes ``docs/figures/alpha_sweep_stability.png``.

Seeds are fixed at 0 and 1. The linear panel varies α. The tanh panel varies
the product αk, once by changing α at k = 1 and once by changing k at α = 0.2.
Grid, step count, and response are the source defaults except for the parameter
being swept. Nothing here is tuned to produce a spatial structure.

An oscillation above the synchronous threshold is a step-size artifact of this
rule, not a physical form. See ``docs/PARAMETERS.md``.
"""

from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim.rule import F_LINEAR, F_TANH, MODE_ASYNC, MODE_SYNC, SYNC_EVEN_GRID_ALPHA_LIMIT, run

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "figures" / "alpha_sweep_stability.png"

# Brackets the even-grid threshold 4/3, the source value 0.2, and the
# larger steps where async linear runs were checked.
ALPHAS = (0.2, 0.5, 1.0, 1.2, 1.3, 4.0 / 3.0, 1.4, 1.5, 1.7, 1.9, 2.2, 2.5)
SEEDS = (0, 1)

SYNC_COLOR = {0: "#0072B2", 1: "#56B4E9"}
ASYNC_COLOR = {0: "#D55E00", 1: "#E69F00"}


def _measure(spec: tuple[int, float, str, str, float]) -> dict[str, float | int | str]:
    seed, alpha, mode, response, k = spec
    result = run(seed, alpha=alpha, mode=mode, f=response, k=k, steps=1000)
    return {
        "seed": seed,
        "alpha": alpha,
        "mode": mode,
        "f": response,
        "k": k,
        "ak": alpha * k,
        "tension": float(result.mean_tension[-1]),
        "d1": float(result.mean_abs_d1[-1]),
        "d2": float(result.mean_abs_d2[-1]),
        "clamps": result.clamp_activations,
    }


def _jobs() -> list[tuple[int, float, str, str, float]]:
    jobs: list[tuple[int, float, str, str, float]] = []
    for alpha in ALPHAS:
        for seed in SEEDS:
            for mode in (MODE_SYNC, MODE_ASYNC):
                jobs.append((seed, alpha, mode, F_LINEAR, 1.0))
    # Tanh: the linearized threshold depends on the product αk.
    # The α = 0.2, k = 1 point is in both families; keep it once.
    for alpha in ALPHAS:
        for seed in SEEDS:
            jobs.append((seed, alpha, MODE_SYNC, F_TANH, 1.0))
            jobs.append((seed, 0.2, MODE_SYNC, F_TANH, alpha / 0.2))
    for alpha in ALPHAS:
        jobs.append((0, alpha, MODE_ASYNC, F_TANH, 1.0))
    unique: list[tuple[int, float, str, str, float]] = []
    seen: set[tuple[int, float, str, str, float]] = set()
    for spec in jobs:
        if spec not in seen:
            seen.add(spec)
            unique.append(spec)
    return unique


def _select(rows: list[dict], **wanted: object) -> list[dict]:
    chosen = []
    for row in rows:
        if all(row[key] == value for key, value in wanted.items()):
            chosen.append(row)
    return sorted(chosen, key=lambda row: float(row["alpha"] if "alpha" in wanted else row["ak"]))


def _draw(rows: list[dict], path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 7.4))

    ax = axes[0, 0]
    for mode, palette in ((MODE_SYNC, SYNC_COLOR), (MODE_ASYNC, ASYNC_COLOR)):
        for seed in SEEDS:
            series = _select(rows, f=F_LINEAR, mode=mode, seed=seed, k=1.0)
            ax.loglog(
                [row["alpha"] for row in series],
                [row["tension"] for row in series],
                color=palette[seed],
                linestyle="-" if seed == 0 else "--",
                marker="o",
                markersize=3.5,
                linewidth=1.4,
                label=f"{mode}, seed {seed}",
            )
    ax.axvline(SYNC_EVEN_GRID_ALPHA_LIMIT, color="#666666", linewidth=0.8, linestyle=":")
    ax.set_xlabel("alpha")
    ax.set_ylabel("mean tension at step 1000")
    ax.set_title("linear f")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, which="both", alpha=0.3)

    ax = axes[0, 1]
    for mode, palette in ((MODE_SYNC, SYNC_COLOR), (MODE_ASYNC, ASYNC_COLOR)):
        series = _select(rows, f=F_LINEAR, mode=mode, seed=0, k=1.0)
        ax.semilogy(
            [row["alpha"] for row in series],
            [max(float(row["d1"]), 1e-16) for row in series],
            color=palette[0],
            linestyle="-",
            marker="o",
            markersize=3.5,
            label=f"{mode} |T(t)-T(t-1)|",
        )
        ax.semilogy(
            [row["alpha"] for row in series],
            [max(float(row["d2"]), 1e-16) for row in series],
            color=palette[0],
            linestyle=":",
            marker="s",
            markersize=3.5,
            label=f"{mode} |T(t)-T(t-2)|",
        )
    ax.axvline(SYNC_EVEN_GRID_ALPHA_LIMIT, color="#666666", linewidth=0.8, linestyle=":")
    ax.set_xlabel("alpha")
    ax.set_ylabel("mean absolute field change at step 1000")
    ax.set_title("linear f, seed 0 (dotted lag is two steps)")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(True, which="both", alpha=0.3)

    ax = axes[1, 0]
    for seed, marker in ((0, "o"), (1, "s")):
        vary_alpha = _select(rows, f=F_TANH, mode=MODE_SYNC, seed=seed, k=1.0)
        ax.loglog(
            [row["ak"] for row in vary_alpha],
            [row["tension"] for row in vary_alpha],
            color=SYNC_COLOR[seed],
            linestyle="-",
            marker=marker,
            markersize=3.5,
            label=f"sync k=1, seed {seed}",
        )
        vary_k = [row for row in rows if row["f"] == F_TANH and row["mode"] == MODE_SYNC and row["seed"] == seed and row["alpha"] == 0.2]
        vary_k = sorted(vary_k, key=lambda row: float(row["ak"]))
        ax.loglog(
            [row["ak"] for row in vary_k],
            [row["tension"] for row in vary_k],
            color=ASYNC_COLOR[seed],
            linestyle="--",
            marker=marker,
            markersize=3.5,
            label=f"sync alpha=0.2, seed {seed}",
        )
    ax.axvline(SYNC_EVEN_GRID_ALPHA_LIMIT, color="#666666", linewidth=0.8, linestyle=":")
    ax.set_xlabel("alpha * k")
    ax.set_ylabel("mean tension at step 1000")
    ax.set_title("tanh f, synchronous")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(True, which="both", alpha=0.3)

    ax = axes[1, 1]
    async_tanh = sorted(
        [row for row in rows if row["f"] == F_TANH and row["mode"] == MODE_ASYNC and row["seed"] == 0 and row["k"] == 1.0],
        key=lambda row: float(row["alpha"]),
    )
    ax.semilogy(
        [row["alpha"] for row in async_tanh],
        [max(float(row["tension"]), 1e-16) for row in async_tanh],
        color=ASYNC_COLOR[0],
        marker="o",
        markersize=3.5,
        label="async tension, k=1, seed 0",
    )
    sync_tanh = _select(rows, f=F_TANH, mode=MODE_SYNC, seed=0, k=1.0)
    ax.semilogy(
        [row["alpha"] for row in sync_tanh],
        [max(float(row["d2"]), 1e-16) for row in sync_tanh],
        color=SYNC_COLOR[0],
        linestyle=":",
        marker="s",
        markersize=3.5,
        label="sync |T(t)-T(t-2)|, k=1, seed 0",
    )
    ax.axvline(SYNC_EVEN_GRID_ALPHA_LIMIT, color="#666666", linewidth=0.8, linestyle=":")
    ax.set_xlabel("alpha  (k = 1, so alpha * k = alpha)")
    ax.set_ylabel("value at step 1000")
    ax.set_title("tanh f, seed 0")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(True, which="both", alpha=0.3)

    fig.suptitle(
        "Rule v0.1 stability sweep, 100×100, 1000 steps, seeds 0 and 1\n"
        "Dotted vertical line is α = 4/3. Period-2 above that line is a step-size artifact.",
        fontsize=11,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _print_table(rows: list[dict]) -> None:
    print(
        f"{'f':6} {'mode':5} {'seed':4} {'alpha':8} {'k':8} {'ak':8} "
        f"{'tension':12} {'d1':12} {'d2':12} {'clamps':8}"
    )
    for row in sorted(rows, key=lambda item: (str(item["f"]), str(item["mode"]), int(item["seed"]), float(item["ak"]))):
        print(
            f"{row['f']:6} {row['mode']:5} {int(row['seed']):4d} {float(row['alpha']):8.4f} "
            f"{float(row['k']):8.4f} {float(row['ak']):8.4f} {float(row['tension']):12.6g} "
            f"{float(row['d1']):12.6g} {float(row['d2']):12.6g} {int(row['clamps']):8d}"
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sweep alpha and alpha*k for rule v0.1.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output PNG path.")
    args = parser.parse_args(argv)
    jobs = _jobs()
    workers = min(4, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(_measure, jobs))
    _print_table(rows)
    _draw(rows, args.out)
    print(args.out)


if __name__ == "__main__":
    main()
