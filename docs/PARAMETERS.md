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

`W` and `H` must each be at least 3. Below that, the offsets `+1` and `−1`
land on the same cell, so the eight Moore terms are not eight distinct cells.

## Parameters from the note

| Parameter | Source value | Role |
|---|---|---|
| `W`, `H` | 100, 100 | Grid size. This code requires both `≥ 3`. |
| `alpha` | 0.2 | Step size in front of `f(Δ)`. |
| `f` | linear | `f(Δ) = Δ`. The note also names `tanh(k Δ)` as an option. |
| `steps` | 1000 | Number of updates. |
| boundaries | periodic | `(x ± 1) mod W`, `(y ± 1) mod H`. |
| neighbourhood | Moore, 8 cells | The center cell is excluded. |
| state | scalar `T` in `[0, 1]` | Clamped after the update. |
| initial field | i.i.d. U[0, 1) | The note writes `random_in_range(0.0, 1.0)`. |
| mode | synchronous | `T_next` is filled from `T`, then swapped in. |

## Choices that are not in the source

These are fixed so the run is reproducible. They are not claims about the note.

1. **`seed` is required.** The note draws a random initial field and names no seed and no generator. `run(seed, ...)` has no default seed. The command `python -m sim` refuses to start without `--seed`. The seed initializes `numpy.random.default_rng` (PCG64). The initial field is i.i.d. U[0, 1): `Generator.random((W, H))`, uniform on the half-open interval `[0, 1)`. The note does not say whether `1` can occur. This generator is what matches the rounded seed-0 field from a quick independent numpy check run by the Simulaciones agent (mean of `T` = 0.499411, std = 0.289). That check is not in this repo.

2. **`k` defaults to 1.** The note writes `tanh(k * Δ)` and does not give `k`. The default `k = 1` is a choice of this implementation. It is not a claim that `tanh` is close to the identity: `tanh(1) ≈ 0.7616`. `k` is ignored when `f` is linear. It matters for the synchronous `tanh` rule when the product `α k` is near `4/3`, because that is the linear stability threshold derived below. At the note's `α = 0.2` this product crosses `4/3` at `k = (4/3) / 0.2 = 20/3 ≈ 6.667`. Pass `--k` or `k=` to use another value.

3. **Asynchronous mode.** The note only specifies the synchronous double loop. `mode="async"` is an extension. One async step is defined here as **one random permutation of all `W*H` cells**: each cell is updated exactly once, in that order, **in place**. A cell updated later in the sweep sees the earlier updates. The permutation is drawn from the same generator as the initial field, after the field has been drawn, so the seed fixes both. "One step = `W*H` single-cell updates" is this permutation sweep, not sampling with replacement. That choice is not in the note.

4. **Recorded trajectory includes step 0.** The CSV has `steps + 1` rows. Row `step = 0` is the initial field, before any update. The lag columns are `nan` until the lag exists.

5. **Standard deviation is the population standard deviation** (`numpy` `ddof=0`).

6. **Arithmetic is float64.** The synchronous linear update is written as in the note, `T + alpha * (mean(neighbours) − T)`, not rearranged.

7. **Spectral length `ξ`.** A review asked for a spatial scale `ξ(t)` or a spectrum `S(k)` and did not fix a formula. The definition used here is below.

## If the mean of `T` must be conserved

Synchronous linear updates conserve the mean when the clamp is idle. The async update implemented here does not. One in-place cell update changes the sum by `α (mean(neighbours) − T)` and does not apply a compensating change to the neighbours. Synchronous `tanh` updates do not conserve the mean either: `tanh` is nonlinear, so the sum of `tanh(k Δ_i)` is not identically zero.

If `T` has to be a conserved quantity under asynchronous updates, that needs a different rule, for example symmetric exchanges along pairs. Choosing that rule is a decision for the author. This code does not add a conservative async scheme, and it does not change the update that is already implemented.

## Synchronous stability

This is a property of the discrete rule, not a physical prediction.

### Linear `f`, clamp idle

The synchronous linear update is the linear map

```
T  ↦  (I + α (A − I)) T
```

where `A` is the Moore averaging operator on the periodic grid. Its Fourier symbol is

```
λ(p, q) = [ cos(2π p/W) + cos(2π q/H) + 2 cos(2π p/W) cos(2π q/H) ] / 4
```

For every real frequency, `λ ∈ [−1/2, 1]`. The code's `neighbor_mean` matches this symbol to about `10^−14` on the grids that were checked. Mode `(p, q)` is multiplied each step by

```
g = 1 + α (λ − 1)
```

The constant mode has `λ = 1` and `g = 1`, which is why the mean is fixed while the clamp is idle. Because `λ ≤ 1`, one has `g ≤ 1`. The other side, `g > −1`, is

```
α (1 − λ) < 2
```

Since `λ ≥ −1/2`, this holds for every mode on every grid with `W, H ≥ 3` whenever `α < 4/3`. The note's `α = 0.2` is in that regime: every non-constant mode decays, and the run homogenizes.

The bound is sharp when at least one side is even. The stripe of wavelength 2 along that side (frequency `π` in one coordinate and `0` in the other) has `λ = −1/2` and

```
g = 1 − (3/2) α
```

- `α < 4/3`: the stripe decays, and so does every other mode.
- `α = 4/3`: `g = −1`. That component is a persistent period-2 oscillation of constant amplitude. Other modes still decay.
- `α > 4/3`: `|g| > 1`. The stripe grows until a bound stops it.

When both sides are odd, `π` is not a grid frequency, so `λ_min > −1/2` and the threshold `2 / (1 − λ_min)` is strictly above `4/3`. On a `15×15` grid the most negative symbol is about `−0.4836` and the threshold is about `1.348`. `α < 4/3` is therefore sufficient on every grid; it is necessary only for grids that attain `λ = −1/2`.

In the long-wave limit, `λ = 1 − (3/8) |k|² + O(|k|⁴)`, with `k` in radians per cell. One step is forward Euler for `∂T/∂t = (3α/8) ∇² T`. The `4/3` bound is the exact discrete condition above, not this continuum estimate. The growing stripe for `α > 4/3` is the same kind of failure as a forward-Euler step that is too large.

### What the runs do once a bound is hit

The growth statement above is for the unclamped linear map. The saturated oscillation is a numerical finding.

Linear `f`, `α = 1.5`, `100×100`, 1000 steps:

| seed | mean tension | mean `|T(t)−T(t−1)|` | mean `|T(t)−T(t−2)|` |
|---|---:|---:|---:|
| 0 | 0.729119 | 0.964304 | 2.24×10^−4 |
| 1 | 0.734477 | 0.974157 | 2.34×10^−4 |

The field occupies the clamp: millions of cell updates hit 0 or 1. This is a clamp-saturated period-2 oscillation. It is a numerical-instability artifact of the rule, not a physical form.

At the marginal value `α = 4/3`, linear sync, seed 0, 100×100, 1000 steps: mean tension about `0.00599`, mean `|T(t)−T(t−1)|` about `0.00692`, mean `|T(t)−T(t−2)|` about `5.8×10^−6`, and 7 clamp activations. That is the non-growing period-2 of the stripe, not the clamp-saturated state.

### `tanh`

Linearized about a uniform field, `tanh(k Δ) = k Δ + O(Δ³)`, so the same map has `α` replaced by `α k`. The unclamped synchronous linearization decays for `α k < 4/3`, is marginal at equality on an even-sided grid, and is unstable above it. A pure stripe of amplitude `10^−6` in this code matches that gain.

The nonlinear `tanh` rule does not conserve the mean of `T`. On a one-spike field the change is visible in a single step.

The saturated `tanh` oscillation is not always the clamp. Linear `f` has an unbounded response, so the growing mode keeps going until the clamp. `tanh` is bounded by 1, so it can stop the growth first. Measured, seed 0, `100×100`, 1000 steps, `α = 0.2`, `k = 8` (`α k = 1.6`): mean tension `0.09585`, mean `|T(t)−T(t−2)|` about `6×10^−5`, mean `|T(t)−T(t−1)|` about `0.127`, and **zero** clamp activations. That period-2 state is still a step-size artifact. It is not the clamp-saturated state seen for linear `f` at `α = 1.5`.

### Async, measured only

The theorem above is for the synchronous map. It does not say what the in-place sweep does.

Linear async, seeds 0 and 1, `100×100`, 1000 steps: mean tension at step 1000 is below `10^−3` for every sampled `α` in `{0.2, 1, 4/3, 1.5, 1.9}`. At `α = 1.5`, where sync sits near tension `0.73`, async seed 0 is at about `2×10^−6`. At `α = 2.2` and `α = 2.5` those async runs do not homogenize: mean tension stays near `0.33` and `0.41`, and the clamp fires on a large fraction of updates. That is a numerical finding. There is no async stability theorem in this file.

## Mean tension

Mean tension at a step is

```
mean |T_i − T_j|
```

over undirected neighbour pairs. With the Moore neighbourhood those pairs are the horizontal edges, the vertical edges, and both diagonal directions, on the periodic grid. Each pair is counted once. There are `4 * W * H` of them.

The orthogonal pairs alone (no diagonals) are a different observable. Both round to 0.337 at seed 0, step 0. At step 1000 they do not agree: full Moore pairs give about `3.99×10^−4`, orthogonal pairs about `3.27×10^−4`. A quick independent numpy check run by the Simulaciones agent, not in this repo, quoted `~0.00033` at step 1000. That figure matches the orthogonal subset. The mean and the standard deviation of `T` match the Moore update. This code uses the full Moore pair set, because that is the neighbourhood of the rule.

## Diagnostics

CSV columns, one row per step including step 0:

| column | definition |
|---|---|
| `mean_tension` | mean `|T_i − T_j|` over undirected Moore pairs |
| `mean_T`, `std_T` | population mean and standard deviation of `T` |
| `mean_abs_d1` | mean over cells of `|T(t) − T(t−1)|`. `nan` at step 0 |
| `mean_abs_d2` | mean over cells of `|T(t) − T(t−2)|`. `nan` at steps 0 and 1 |
| `xi` | spectral length below |

A period-2 oscillation has `mean_abs_d2` near 0 while `mean_abs_d1` stays large. Slow decay of a smooth field has `mean_abs_d2` about twice `mean_abs_d1`. At α = 0.2, seed 0, sync, step 1000, those two means are about `4.3×10^−6` and `8.7×10^−6`.

`ξ` is `2π / sqrt(⟨k²⟩_S)`. `S` is the squared modulus of the FFT of the demeaned field, `k` is the angular wave number in radians per cell, and the average skips the zero mode. A constant field returns `nan`. A pure cosine of wavelength `L` cells returns `L`. The stripe `(−1)^y` on an even height returns `2`. At α = 0.2, seed 0, sync, `ξ` goes from about `2.43` at step 0 to about `61.8` at step 1000.

The CLI also writes a histogram of the final field: 20 equal bins of `[0, 1]`.

## Seed 0, synchronous, linear, 100 × 100, α = 0.2

Clamp activations on this run: 0. For linear `f`, `α ∈ [0, 1]`, and `T ∈ [0, 1]`, the unclamped update is a convex combination, so in exact arithmetic it stays inside `[0, 1]` and the clamp does nothing. The synchronous linear update also preserves the mean of `T`: `A` is doubly stochastic on a periodic grid, and a simultaneous update therefore cannot change the sum. (Float64 moves the mean by much less than `10^−15` on this run.) This conservation does not extend to async, and it does not extend to `tanh`.

| quantity | t = 0 | t = 100 | t = 1000 |
|---|---|---|---|
| mean tension (Moore pairs) | 0.33693410 | 0.00363878 | 0.00039893 |
| mean of `T` | 0.49941066 | 0.49941066 | 0.49941066 |
| std of `T` | 0.28905043 | 0.02098377 | 0.00567252 |

Rounded as in the Simulaciones agent's check (not in this repo): mean tension `0.337` at `t = 0`, std `0.289 → 0.0057`, mean of `T` `0.499411` conserved. That check's `~0.00033` at `t = 1000` is the orthogonal-pair observable (`0.000327`), not the Moore-pair observable used here (`0.000399`).

## Commands

```bash
python -m sim --seed 0
python -m sim.figure
python -m sim.sweep
```

The first command writes, under `outputs/`:

- `seed0_sync_linear.csv` with the columns listed above
- `seed0_sync_linear_final.png`, the final grid drawn on a colour scale of `[0, 1]`
- `seed0_sync_linear_tension.png`, mean tension against step (linear axes)
- `seed0_sync_linear_hist.png`, histogram of the final field

The second command writes `docs/figures/mean_tension_sync_vs_async.png`: mean tension against step on log-log axes, synchronous and asynchronous, seeds 0 and 1, linear `f`, α = 0.2. Step 0 is omitted because a logarithmic axis cannot show it.

The third command writes `docs/figures/alpha_sweep_stability.png`: mean tension at step 1000 against `α` (linear `f`, sync and async, seeds 0 and 1) and against `α k` (`tanh`, sync). Seeds are fixed. The vertical line is `α = 4/3`.
