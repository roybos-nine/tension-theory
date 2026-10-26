"""Command line for one rule-v0.1 run.

``python -m sim --seed 0`` writes a CSV and two PNGs. ``--seed`` is required.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim.rule import (
    ALPHA_DEFAULT,
    F_DEFAULT,
    F_LINEAR,
    F_TANH,
    H_DEFAULT,
    K_DEFAULT,
    MODE_ASYNC,
    MODE_DEFAULT,
    MODE_SYNC,
    STEPS_DEFAULT,
    W_DEFAULT,
    SimulationResult,
    run,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run Tension Game of Life rule v0.1 and write a CSV plus PNGs. "
            "The seed is required because the source note does not specify one."
        )
    )
    parser.add_argument("--seed", type=int, required=True, help="RNG seed (required).")
    parser.add_argument(
        "--width",
        type=int,
        default=W_DEFAULT,
        help="Grid width W. Must be >= 3.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=H_DEFAULT,
        help="Grid height H. Must be >= 3.",
    )
    parser.add_argument("--alpha", type=float, default=ALPHA_DEFAULT, help="Response speed α.")
    parser.add_argument(
        "--f",
        choices=(F_LINEAR, F_TANH),
        default=F_DEFAULT,
        help="Response: linear (default, from the note) or tanh.",
    )
    parser.add_argument(
        "--k",
        type=float,
        default=K_DEFAULT,
        help=(
            "tanh steepness. NOT in the source note; default 1 is a choice "
            "of this implementation. Ignored when --f linear."
        ),
    )
    parser.add_argument("--steps", type=int, default=STEPS_DEFAULT, help="Number of updates.")
    parser.add_argument(
        "--mode",
        choices=(MODE_SYNC, MODE_ASYNC),
        default=MODE_DEFAULT,
        help="sync (source) or async (random permutation sweep; not in the source).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs"),
        help="Directory for the CSV and PNGs.",
    )
    args = parser.parse_args(argv)

    result = run(
        args.seed,
        W=args.width,
        H=args.height,
        alpha=args.alpha,
        f=args.f,
        k=args.k,
        steps=args.steps,
        mode=args.mode,
    )
    stem = f"seed{args.seed}_{args.mode}_{args.f}"
    if args.f == F_TANH:
        stem = f"{stem}_k{args.k:g}"
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / f"{stem}.csv"
    final_path = args.out / f"{stem}_final.png"
    tension_path = args.out / f"{stem}_tension.png"
    hist_path = args.out / f"{stem}_hist.png"
    write_csv(csv_path, result)
    write_final_grid(final_path, result, seed=args.seed, mode=args.mode, f=args.f)
    write_tension_curve(tension_path, result, seed=args.seed, mode=args.mode, f=args.f)
    write_histogram(hist_path, result, seed=args.seed, mode=args.mode, f=args.f)
    print(csv_path)
    print(final_path)
    print(tension_path)
    print(hist_path)


def _format_float(value: float) -> str:
    if not np.isfinite(value):
        return "nan"
    return f"{value:.16g}"


def write_csv(path: Path, result: SimulationResult) -> None:
    """Write one row per recorded step, including the initial field at step 0.

    ``mean_abs_d1`` and ``mean_abs_d2`` are NaN until that lag exists.
    """

    header = (
        "step,mean_tension,mean_T,std_T,mean_abs_d1,mean_abs_d2,spectral_length\n"
    )
    lines = [header]
    for index in range(result.step.size):
        lines.append(
            f"{int(result.step[index])},"
            f"{_format_float(result.mean_tension[index])},"
            f"{_format_float(result.mean_T[index])},"
            f"{_format_float(result.std_T[index])},"
            f"{_format_float(result.mean_abs_d1[index])},"
            f"{_format_float(result.mean_abs_d2[index])},"
            f"{_format_float(result.spectral_length[index])}\n"
        )
    path.write_text("".join(lines))


def write_final_grid(path: Path, result: SimulationResult, *, seed: int, mode: str, f: str) -> None:
    """Save the final field on a fixed colour scale of [0, 1]."""

    grid = result.grid
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    # imshow rows are y, columns are x. origin='lower' puts y upward.
    image = ax.imshow(
        grid.T,
        origin="lower",
        vmin=0.0,
        vmax=1.0,
        cmap="viridis",
        interpolation="nearest",
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        f"final T, rule v0.1, {mode}, f={f}, seed {seed}\n"
        f"values in [{grid.min():.4f}, {grid.max():.4f}] shown on [0, 1]"
    )
    fig.colorbar(image, ax=ax, label="T")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def write_histogram(path: Path, result: SimulationResult, *, seed: int, mode: str, f: str) -> None:
    """Histogram of the final field on 20 equal bins of [0, 1]."""

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.hist(
        result.grid.ravel(),
        bins=np.linspace(0.0, 1.0, 21),
        color="#0072B2",
        edgecolor="white",
        linewidth=0.4,
    )
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("T")
    ax.set_ylabel("cells")
    ax.set_title(f"final histogram, rule v0.1, {mode}, f={f}, seed {seed}")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def write_tension_curve(
    path: Path, result: SimulationResult, *, seed: int, mode: str, f: str
) -> None:
    """Save mean tension against step on linear axes, including step 0."""

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.plot(result.step, result.mean_tension, color="#0072B2", linewidth=1.5)
    ax.set_xlabel("step")
    ax.set_ylabel("mean tension")
    ax.set_title(f"mean tension, rule v0.1, {mode}, f={f}, seed {seed}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
