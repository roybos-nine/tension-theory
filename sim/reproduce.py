"""Versioned reproduction of the rule v0.1 runs cited in the docs.

Command version ``v0.1`` (``REPRODUCE_VERSION``).

    python -m sim.reproduce
    python -m sim.reproduce --tanh-k8
    python -m sim.reproduce --sweep

``--tanh-k8`` is synchronous ``tanh``, ``k=8``, ``alpha=0.2``, seed 0,
100×100, 1000 steps. ``--sweep`` is the alpha-sweep figure, seeds 0 and 1.
With neither flag, both jobs run.
"""

from __future__ import annotations

import argparse
from pathlib import Path

REPRODUCE_VERSION = "v0.1"
TANH_SEED = 0
TANH_ALPHA = 0.2
TANH_K = 8.0
TANH_STEPS = 1000
TANH_MODE = "sync"
SWEEP_SEEDS = (0, 1)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TANH_OUT = Path("outputs") / "reproduce"
DEFAULT_SWEEP_OUT = ROOT / "docs" / "figures" / "alpha_sweep_stability.png"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            f"Reproduce rule v0.1 runs (command version {REPRODUCE_VERSION}). "
            "With no flag, both jobs run. "
            "--tanh-k8: synchronous tanh, k=8, alpha=0.2, seed 0, "
            "100x100, 1000 steps. "
            "--sweep: alpha-sweep figure, seeds 0 and 1."
        )
    )
    parser.add_argument(
        "--tanh-k8",
        action="store_true",
        help=(
            f"Synchronous tanh, k={TANH_K:g}, alpha={TANH_ALPHA}, "
            f"seed {TANH_SEED}, 100x100, {TANH_STEPS} steps."
        ),
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help=f"Alpha-sweep figure. Seeds {SWEEP_SEEDS[0]} and {SWEEP_SEEDS[1]}.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_TANH_OUT,
        help="Directory for the tanh k=8 CSV and PNGs.",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=DEFAULT_SWEEP_OUT,
        help="PNG path for the alpha sweep.",
    )
    args = parser.parse_args(argv)
    run_tanh = args.tanh_k8 or not args.sweep
    run_sweep = args.sweep or not args.tanh_k8
    # If the user passed neither flag, both booleans above are true.
    # If they passed only one, the other stays false.
    if args.tanh_k8 or args.sweep:
        run_tanh = args.tanh_k8
        run_sweep = args.sweep

    print(f"reproduce {REPRODUCE_VERSION}")
    if run_tanh:
        print(
            f"tanh k={TANH_K:g} alpha={TANH_ALPHA} seed={TANH_SEED} "
            f"mode={TANH_MODE} 100x100 steps={TANH_STEPS}"
        )
        from sim.__main__ import main as sim_main

        sim_main(
            [
                "--seed",
                str(TANH_SEED),
                "--f",
                "tanh",
                "--k",
                str(TANH_K),
                "--alpha",
                str(TANH_ALPHA),
                "--steps",
                str(TANH_STEPS),
                "--mode",
                TANH_MODE,
                "--width",
                "100",
                "--height",
                "100",
                "--out",
                str(args.out),
            ]
        )
    if run_sweep:
        print(f"alpha sweep seeds {SWEEP_SEEDS[0]} and {SWEEP_SEEDS[1]}")
        from sim.sweep import main as sweep_main

        sweep_main(["--out", str(args.figure)])


if __name__ == "__main__":
    main()
