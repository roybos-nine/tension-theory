# Parameters of Tension Game of Life rule v0.1

Source: the author's Notion note *Tension Game of Life v0.1* (status: Idea).
The note is a sketch, not a finished specification. This file records the
update as implemented in `sim/`, and it marks every choice the note does not
make.

The code is that note's fixed periodic lattice. `scripts/tension_graph.py` is
not in this repository, and this package is not a reconstruction of it.

## Update

For each cell `(x, y)` on a grid of shape `(W, H)`, indexed `T[x, y]`:

```
neighbours = the 8 Moore cells, indices modulo (W, H)
Δ          = mean(neighbours) − T[x, y]
T_raw      = T[x, y] + alpha * f(Δ)
T'         = min(1, max(0, T_raw))
```

`f` is either

- linear: `f(Δ) = Δ` (the note's default), or
- tanh: `f(Δ) = tanh(k * Δ)`.

Synchronous mode computes every `T'` from the same previous field, then
replaces the field. That is the update in the note's pseudocode.

## Parameters from the note

| Parameter | Source value | Role |
|---|---|---|
| `W`, `H` | 100, 100 | Grid size. |
| `alpha` | 0.2 | Step size in front of `f(Δ)`. |
| `f` | linear | `f(Δ) = Δ`. The note also names `tanh(k Δ)` as an option. |
| `steps` | 1000 | Number of updates. |
| boundaries | periodic | `(x ± 1) mod W`, `(y ± 1) mod H`. |
| neighbourhood | Moore, 8 cells | The center cell is excluded. |
| state | scalar `T` in `[0, 1]` | Clamped after the update. |
| initial field | i.i.d. uniform on the unit interval | The note writes `random_in_range(0.0, 1.0)`. |
| mode | synchronous | `T_next` is filled from `T`, then swapped in. |

## Choices that are not in the source

These are fixed so the run is reproducible. They are not claims about the note.

1. **`seed` is required.** The note draws a random initial field and names no seed and no generator. `run(seed, ...)` has no default seed. The command `python -m sim` refuses to start without `--seed`. The seed initializes `numpy.random.default_rng` (PCG64). The initial field is `Generator.random((W, H))`, which is uniform on `[0, 1)`. That half-open interval is the standard continuous uniform; the note does not say whether `1` can occur. This generator and this seed convention are what reproduce an independent sketch's seed-0 field (mean of `T` = 0.499411, std = 0.289).

2. **`k` defaults to 1.** The note writes `tanh(k * Δ)` and does not give `k`. The default `k = 1` is a choice of this implementation: `Δ` is already `O(1)`, so `k = 1` is a mild saturation (`tanh` is close to the identity on that range) rather than a fitted value. `k` is ignored when `f` is linear. Pass `--k` or `k=` to use another value.

3. **Asynchronous mode.** The note only specifies the synchronous double loop. `mode="async"` is an extension, so the sync/async comparison the README used to state as an observation can be run. One async step is defined here as **one random permutation of all `W*H` cells**: each cell is updated exactly once, in that order, **in place**. A cell updated later in the sweep sees the earlier updates. The permutation is drawn from the same generator as the initial field, after the field has been drawn, so the seed fixes both. "One step = `W*H` single-cell updates" is this permutation sweep, not sampling with replacement. That choice is not in the note.

4. **Recorded trajectory includes step 0.** The CSV has `steps + 1` rows. Row `step = 0` is the initial field, before any update.

5. **Standard deviation is the population standard deviation** (`numpy` `ddof=0`).

6. **Arithmetic is float64.** The synchronous linear update is written as in the note, `T + alpha * (mean(neighbours) − T)`, not rearranged.

## Mean tension

Mean tension at a step is

```
mean |T_i − T_j|
```

over undirected neighbour pairs. With the Moore neighbourhood those pairs are the horizontal edges, the vertical edges, and both diagonal directions, on the periodic grid. Each pair is counted once. There are `4 * W * H` of them.

The orthogonal pairs alone (no diagonals) are a different observable. Both round to 0.337 at seed 0, step 0. At step 1000 they do not agree: full Moore pairs give about `3.99e-4`, orthogonal pairs about `3.27e-4`. An independent sketch quoted `~0.00033` at step 1000. That figure matches the orthogonal subset; the mean and the standard deviation of `T` match the Moore update. This code uses the full Moore pair set, because that is the neighbourhood of the rule. See the seed-0 table below.

## Seed 0, synchronous, linear, 100 × 100, α = 0.2

Clamp activations on this run: 0. For linear `f`, `α ∈ [0, 1]`, and `T ∈ [0, 1]`, the unclamped update is a convex combination, so in exact arithmetic it stays inside `[0, 1]` and the clamp does nothing. The synchronous linear update also preserves the mean of `T`: the Moore averaging operator on a periodic grid is doubly stochastic, and a simultaneous update therefore cannot change the sum. (Float64 moves the mean by much less than `1e-15` on this run.)

| quantity | t = 0 | t = 100 | t = 1000 |
|---|---|---|---|
| mean tension (Moore pairs) | 0.33693410 | 0.00363878 | 0.00039893 |
| mean of `T` | 0.49941066 | 0.49941066 | 0.49941066 |
| std of `T` | 0.28905043 | 0.02098377 | 0.00567252 |

Rounded as in the independent sketch: mean tension `0.337` at `t = 0`, std `0.289 → 0.0057`, mean of `T` `0.499411` conserved. The sketch's `~0.00033` at `t = 1000` is the orthogonal-pair observable (`0.000327`), not the Moore-pair observable used here (`0.000399`).

Asynchronous linear updates do **not** conserve the mean exactly. A single in-place update changes the sum by `α (mean(neighbours) − T)`, and the neighbours are not adjusted at the same moment.

## Commands

```bash
python -m sim --seed 0
python -m sim.figure
```

The first command writes, under `outputs/`:

- `seed0_sync_linear.csv` with columns `step,mean_tension,mean_T,std_T`
- `seed0_sync_linear_final.png`, the final grid drawn on a colour scale of `[0, 1]`
- `seed0_sync_linear_tension.png`, mean tension against step (linear axes)

The second command writes `docs/figures/mean_tension_sync_vs_async.png`: mean tension against step on log-log axes, synchronous and asynchronous, seeds 0 and 1, linear `f`, source defaults. Step 0 is omitted because a logarithmic axis cannot show it. The CSV from the first command still contains step 0.
