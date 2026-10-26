"""Reference implementation of the Tension Game of Life rule v0.1.

The rule is the fixed-lattice update in the note "Tension Game of Life v0.1"
(status: Idea). It is not the dynamic-graph simulator named in older README
text (`scripts/tension_graph.py`), which is not in this repository.

See ``docs/PARAMETERS.md`` for every parameter, including choices that the
source note does not specify.
"""

from sim.rule import SimulationResult, mean_tension, run, step_sync

__all__ = ["SimulationResult", "mean_tension", "run", "step_sync"]
