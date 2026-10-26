"""Log-log comparison of sync and async mean tension for seeds 0 and 1.

``python -m sim.figure`` writes ``docs/figures/mean_tension_sync_vs_async.png``.
The curves use the source defaults (100 × 100, α = 0.2, linear f, 1000 steps).
Nothing here is tuned to produce spatial structure.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim.rule import MODE_ASYNC, MODE_SYNC, run

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "figures" / "mean_tension_sync_vs_async.png"

# Colour distinguishes the update mode. Line style distinguishes the seed.
STYLES = {
    (MODE_SYNC, 0): ("#0072B2", "-", "sync, seed 0"),
    (MODE_SYNC, 1): ("#56B4E9", "--", "sync, seed 1"),
    (MODE_ASYNC, 0): ("#D55E00", "-", "async, seed 0"),
    (MODE_ASYNC, 1): ("#E69F00", "--", "async, seed 1"),
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Plot mean tension vs step on log-log axes for sync and async, seeds 0 and 1."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output PNG path.")
    args = parser.parse_args(argv)

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    for mode in (MODE_SYNC, MODE_ASYNC):
        for seed in (0, 1):
            result = run(seed, mode=mode)
            colour, linestyle, label = STYLES[(mode, seed)]
            # Step 0 cannot be placed on a logarithmic axis.
            ax.loglog(
                result.step[1:],
                result.mean_tension[1:],
                color=colour,
                linestyle=linestyle,
                linewidth=1.6,
                label=label,
            )
            print(
                f"{mode} seed {seed}: "
                f"t0={result.mean_tension[0]:.8f} "
                f"t100={result.mean_tension[100]:.8f} "
                f"t1000={result.mean_tension[1000]:.8f} "
                f"mean_T0={result.mean_T[0]:.8f} "
                f"mean_T1000={result.mean_T[1000]:.8f} "
                f"std0={result.std_T[0]:.8f} "
                f"std1000={result.std_T[1000]:.8f}"
            )
    ax.set_xlabel("step")
    ax.set_ylabel("mean tension")
    ax.set_title("Rule v0.1, linear f, α = 0.2, 100×100")
    ax.legend(frameon=False)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160)
    plt.close(fig)
    print(args.out)


if __name__ == "__main__":
    main()
