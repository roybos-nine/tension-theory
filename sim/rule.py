"""Tension Game of Life rule v0.1.

Source note (status Idea), synchronous case::

    Δ(x, y) = mean(Moore neighbours of (x, y)) − T(x, y)
    T'(x, y) = clip(T(x, y) + α · f(Δ), 0, 1)

Neighbours are the 8 Moore cells, with periodic boundaries. ``f`` is the
identity by default, or ``tanh(k Δ)``. The grid is updated synchronously:
every new value is computed from the previous grid.

Asynchronous mode is not in the source note. One async step is one random
permutation of the cells: each cell is updated once, in place, in that order.
See ``docs/PARAMETERS.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

F_LINEAR = "linear"
F_TANH = "tanh"
MODE_SYNC = "sync"
MODE_ASYNC = "async"

# One representative shift per undirected Moore edge on the periodic grid.
# (1, 0), (0, 1), (1, 1) and (1, −1) cover horizontal, vertical and both
# diagonals exactly once.
PAIR_SHIFTS = ((1, 0), (0, 1), (1, 1), (1, -1))

# Defaults from the source note, except K_DEFAULT (not in the note).
W_DEFAULT = 100
H_DEFAULT = 100
ALPHA_DEFAULT = 0.2
F_DEFAULT = F_LINEAR
K_DEFAULT = 1.0
STEPS_DEFAULT = 1000
MODE_DEFAULT = MODE_SYNC


@dataclass(frozen=True)
class SimulationResult:
    """Trajectory of one run.

    ``step[0]`` is the initial field, before any update. ``grid`` is the
    field after ``steps`` updates. ``mean_tension`` is the mean of
    ``|T_i − T_j|`` over undirected Moore neighbour pairs.
    ``mean_T`` and ``std_T`` are the population mean and standard deviation
    of the field (``ddof=0``). ``clamp_activations`` counts values that fell
    outside ``[0, 1]`` before clipping, summed over every cell update.
    """

    grid: np.ndarray
    step: np.ndarray
    mean_tension: np.ndarray
    mean_T: np.ndarray
    std_T: np.ndarray
    clamp_activations: int


def run(
    seed: int,
    *,
    W: int = W_DEFAULT,
    H: int = H_DEFAULT,
    alpha: float = ALPHA_DEFAULT,
    f: str = F_DEFAULT,
    k: float = K_DEFAULT,
    steps: int = STEPS_DEFAULT,
    mode: str = MODE_DEFAULT,
) -> SimulationResult:
    """Evolve a grid for ``steps`` updates.

    Parameters
    ----------
    seed :
        Required. Initializes ``numpy.random.default_rng`` (PCG64). The note
        does not specify a seed or a generator. The initial field is drawn
        first; in async mode the same generator then draws each step's
        permutation. There is no default.
    W, H :
        Grid width and height. Source default is 100 × 100. The array has
        shape ``(W, H)`` and is indexed ``T[x, y]``, matching the note.
    alpha :
        Response speed. Source value is 0.2.
    f :
        ``"linear"`` (source default, ``f(Δ) = Δ``) or ``"tanh"``
        (``f(Δ) = tanh(k Δ)``).
    k :
        Steepness of the tanh response. **Not in the source note.** Default
        1.0 is a choice of this implementation. Ignored when ``f="linear"``.
    steps :
        Number of updates. Source value is 1000. The recorded trajectory has
        ``steps + 1`` rows because it includes the initial field.
    mode :
        ``"sync"`` (source: ``T_next`` is computed entirely from ``T``) or
        ``"async"`` (not in the source; see ``step_async``).
    """

    seed = _require_nonnegative_int("seed", seed)
    W = _require_positive_int("W", W)
    H = _require_positive_int("H", H)
    alpha = _require_finite_float("alpha", alpha)
    k = _require_finite_float("k", k)
    steps = _require_nonnegative_int("steps", steps)
    if f not in (F_LINEAR, F_TANH):
        raise ValueError(f"f must be {F_LINEAR!r} or {F_TANH!r}, got {f!r}")
    if mode not in (MODE_SYNC, MODE_ASYNC):
        raise ValueError(
            f"mode must be {MODE_SYNC!r} or {MODE_ASYNC!r}, got {mode!r}"
        )

    rng = np.random.default_rng(seed)
    field = rng.random((W, H))

    step = np.arange(steps + 1, dtype=np.int64)
    mean_tension = np.empty(steps + 1, dtype=np.float64)
    mean_T = np.empty(steps + 1, dtype=np.float64)
    std_T = np.empty(steps + 1, dtype=np.float64)
    clamps = 0

    for t in range(steps + 1):
        mean_tension[t], mean_T[t], std_T[t] = field_stats(field)
        if t == steps:
            break
        if mode == MODE_SYNC:
            field, n_clamp = step_sync(field, alpha=alpha, f=f, k=k)
        else:
            n_clamp = step_async(field, rng, alpha=alpha, f=f, k=k)
        clamps += n_clamp

    return SimulationResult(
        grid=field.copy(),
        step=step,
        mean_tension=mean_tension,
        mean_T=mean_T,
        std_T=std_T,
        clamp_activations=clamps,
    )


def step_sync(
    T: np.ndarray,
    *,
    alpha: float = ALPHA_DEFAULT,
    f: str = F_DEFAULT,
    k: float = K_DEFAULT,
) -> tuple[np.ndarray, int]:
    """One synchronous step. Does not modify ``T``.

    Returns the next field and the number of cells whose unclamped value
    lay outside ``[0, 1]``.
    """

    field = np.asarray(T, dtype=np.float64)
    if field.ndim != 2:
        raise ValueError("T must have shape (W, H)")
    alpha = _require_finite_float("alpha", alpha)
    k = _require_finite_float("k", k)
    delta = neighbor_mean(field) - field
    raw = field + alpha * apply_f(delta, f, k)
    clamps = int(np.count_nonzero((raw < 0.0) | (raw > 1.0)))
    np.clip(raw, 0.0, 1.0, out=raw)
    return raw, clamps


def step_async(
    T: np.ndarray,
    rng: np.random.Generator,
    *,
    alpha: float = ALPHA_DEFAULT,
    f: str = F_DEFAULT,
    k: float = K_DEFAULT,
) -> int:
    """One asynchronous step, in place. Returns the clamp count.

    A step is a single random permutation of the ``W * H`` cells. Each cell
    is updated once, using the field as it stands at that moment (earlier
    updates in the same sweep are visible). This definition is not in the
    source note.

    ``rng`` is the generator that also drew the initial field when called
    from ``run``, so one seed fixes both.
    """

    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be numpy.random.Generator")
    if not isinstance(T, np.ndarray) or T.ndim != 2:
        raise ValueError("T must be a 2-dimensional numpy array")
    field = np.ascontiguousarray(T, dtype=np.float64)
    order = rng.permutation(field.size)
    clamps = apply_async_sweep(field, order, alpha=alpha, f=f, k=k)
    if field is not T:
        T[...] = field
    return clamps


def apply_async_sweep(
    T: np.ndarray,
    order: np.ndarray,
    *,
    alpha: float = ALPHA_DEFAULT,
    f: str = F_DEFAULT,
    k: float = K_DEFAULT,
) -> int:
    """Update ``T`` in place at flat indices ``order`` (``index = x*H + y``).

    The inner loop walks a Python list. Per-cell NumPy scalar writes are
    much slower at 100 × 100 × 1000, and the update itself is unchanged.
    """

    field = np.asarray(T)
    if field.ndim != 2 or field.dtype != np.float64 or not field.flags.c_contiguous:
        raise ValueError("T must be a C-contiguous float64 array of shape (W, H)")
    alpha = _require_finite_float("alpha", alpha)
    k = _require_finite_float("k", k)
    if f not in (F_LINEAR, F_TANH):
        raise ValueError(f"f must be {F_LINEAR!r} or {F_TANH!r}, got {f!r}")

    height = field.shape[1]
    grid = field.ravel().tolist()
    clamps = 0
    use_tanh = f == F_TANH
    for raw_index in np.asarray(order).tolist():
        index = int(raw_index)
        x = index // height
        y = index - x * height
        x_minus = (x - 1) % field.shape[0]
        x_plus = (x + 1) % field.shape[0]
        y_minus = (y - 1) % height
        y_plus = (y + 1) % height
        neighbour_sum = (
            grid[x_minus * height + y_minus]
            + grid[x_minus * height + y]
            + grid[x_minus * height + y_plus]
            + grid[x * height + y_minus]
            + grid[x * height + y_plus]
            + grid[x_plus * height + y_minus]
            + grid[x_plus * height + y]
            + grid[x_plus * height + y_plus]
        )
        tension = grid[index]
        delta = neighbour_sum * 0.125 - tension
        response = math.tanh(k * delta) if use_tanh else delta
        updated = tension + alpha * response
        if updated < 0.0:
            updated = 0.0
            clamps += 1
        elif updated > 1.0:
            updated = 1.0
            clamps += 1
        grid[index] = updated
    field[:, :] = np.asarray(grid, dtype=np.float64).reshape(field.shape)
    return clamps


def neighbor_mean(T: np.ndarray) -> np.ndarray:
    """Mean of the 8 periodic Moore neighbours. ``T`` has shape ``(W, H)``."""

    field = np.asarray(T, dtype=np.float64)
    if field.ndim != 2:
        raise ValueError("T must have shape (W, H)")
    total = np.zeros_like(field)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            # The shifts come in ± pairs, so each of the 8 neighbours is
            # included once even though a positive roll reads the opposite
            # index direction.
            total += np.roll(np.roll(field, dx, axis=0), dy, axis=1)
    return total / 8.0


def mean_tension(T: np.ndarray) -> float:
    """Mean ``|T_i − T_j|`` over undirected periodic Moore neighbour pairs."""

    field = np.asarray(T, dtype=np.float64)
    if field.ndim != 2:
        raise ValueError("T must have shape (W, H)")
    total = 0.0
    for dx, dy in PAIR_SHIFTS:
        shifted = np.roll(np.roll(field, dx, axis=0), dy, axis=1)
        total += float(np.abs(field - shifted).sum())
    return total / (len(PAIR_SHIFTS) * field.size)


def field_stats(T: np.ndarray) -> tuple[float, float, float]:
    """Return ``(mean_tension, mean of T, population std of T)``."""

    field = np.asarray(T, dtype=np.float64)
    return mean_tension(field), float(field.mean()), float(field.std(ddof=0))


def apply_f(delta: np.ndarray, f: str, k: float) -> np.ndarray:
    """Response ``f(Δ)``. ``k`` is used only for ``f="tanh"``."""

    if f == F_LINEAR:
        return delta
    if f == F_TANH:
        return np.tanh(k * delta)
    raise ValueError(f"f must be {F_LINEAR!r} or {F_TANH!r}, got {f!r}")


def _require_positive_int(name: str, value: object) -> int:
    number = _require_int(name, value)
    if number < 1:
        raise ValueError(f"{name} must be >= 1")
    return number


def _require_nonnegative_int(name: str, value: object) -> int:
    number = _require_int(name, value)
    if number < 0:
        raise ValueError(f"{name} must be >= 0")
    return number


def _require_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    return int(value)


def _require_finite_float(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.floating, np.integer)):
        raise TypeError(f"{name} must be a real number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number
