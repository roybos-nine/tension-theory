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

1. **`seed` is required.** The note draws a random initial field and names no seed and no generator. `run(seed, ...)` has no default seed. The command `python -m sim` refuses to start without `--seed`. The seed initializes `numpy.random.default_rng` (PCG64). The initial field is i.i.d. U[0, 1): `Generator.random((W, H))`, uniform on the half-open interval `[0, 1)`. The note does not say whether `1` can occur. This generator is what matches the rounded seed-0 field from a quick numpy check run by the same Simulaciones agent (mean of `T` = 0.499411, std = 0.289). That check is not in this repo.

2. **`k` defaults to 1.** The note writes `tanh(k * Δ)` and does not give `k`. The default `k = 1` is a choice of this implementation. It is not a claim that `tanh` is close to the identity: `tanh(1) ≈ 0.7616`. `k` is ignored when `f` is linear. Near a uniform field, `tanh(k Δ) = k Δ + O(Δ³)`, so the synchronous linearization has step `α k` in place of `α`. That linearization, not a proved bound on the nonlinear map, is why `α k` near `4/3` matters. At the note's `α = 0.2` the product crosses `4/3` at `k = (4/3) / 0.2 = 20/3 ≈ 6.667`. Pass `--k` or `k=` to use another value.

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

The constant mode has `λ = 1` and `g = 1`, which is why the mean is fixed while the clamp is idle. The step size in this derivation satisfies `α > 0`. At `α = 0` one has `g = 1` for every mode, so the field is frozen. For `α < 0` and `λ < 1`, the product `α (λ − 1)` is positive, so `g > 1` and every non-constant mode grows.

For `α > 0`, `λ ≤ 1` gives `g ≤ 1`. The other side, `g > −1`, is

```
α (1 − λ) < 2
```

Since `λ ≥ −1/2`, this holds for every mode on every grid with `W, H ≥ 3` whenever `0 < α < 4/3`. The note's `α = 0.2` is in that regime: every non-constant mode decays, and the run homogenizes. The bound `α < 4/3` is proved here for linear `f`, unclamped. It is not a proved bound for `tanh`.

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

Linearized about a uniform field, `tanh(k Δ) = k Δ + O(Δ³)`, so the same map has `α` replaced by `α k`. That replacement is a linearization valid only near a uniform field. It is not a proved bound for the nonlinear map. The unclamped synchronous linearization decays for `0 < α k < 4/3`, is marginal at equality on an even-sided grid, and is unstable above it. A pure stripe of amplitude `10^−6` in this code matches that gain. The bound `α < 4/3` above is proved for linear `f`, unclamped.

The nonlinear `tanh` rule does not conserve the mean of `T`. On a one-spike field the change is visible in a single step.

The saturated `tanh` oscillation is not always the clamp. Linear `f` has an unbounded response, so the growing mode keeps going until the clamp. `tanh` is bounded by 1, so it can stop the growth first. Measured, seed 0, `100×100`, 1000 steps, `α = 0.2`, `k = 8` (`α k = 1.6`): mean tension `0.095855`, mean `|T(t)−T(t−2)|` about `6.1×10^−5`, mean `|T(t)−T(t−1)|` about `0.127`, and **zero** clamp activations. That period-2 state is still a step-size artifact. It is not the clamp-saturated state seen for linear `f` at `α = 1.5`.

#### Period-2 stripe

Take a pure stripe `T = μ + A σ` with `σ = (−1)^y`, on an even height, and assume the clamp stays idle. Two of the eight neighbours share the cell's sign (the horizontal pair). The other six have the opposite sign. Their mean is `μ − (A/2) σ`, so

```
Δ = −(3/2) A σ
tanh(k Δ) = −σ tanh(3 k A / 2)
T' = μ + σ [ A − α tanh(3 k A / 2) ]
```

A period-2 cycle flips the stripe, `T' = μ − A σ`, which is the scalar equation

```
2A = α tanh(3 k A / 2)
```

`A = 0` is always a root. A nonzero root exists only when the small-amplitude gain is expanding, `α k > 4/3`. The nonzero root is the amplitude of the cycle. It is set by `α` and `k` (the step), not by a separate physical length. The factor `3/2` is this stencil. For `α = 0.05`, `k = 8` (`α k = 0.4`) the only root is `A = 0`. For `α = 0.2`, `k = 8` the nonzero root is `A = 0.065856966`. One synchronous step of that stripe, `μ = 0.5`, returns the flipped stripe with the clamp idle (checked in `tests/test_rule.py`).

Mean tension of the pure stripe counts four pair directions. Horizontal pairs differ by 0. Vertical pairs and both diagonals differ by `2A`. The mean is `1.5 A = 0.098785`. The random-field run quoted above measures `0.095855`. Those are different fields: the random initial condition is not one global stripe, and domain walls remain. The predicted pure-stripe tension is `0.098785`; the measured random-field tension is `0.095855`.

### Async energy

The synchronous theorem does not say what the in-place sweep does. The following is a separate derivation for one cell, neighbours held fixed, and it was checked against `moore_pair_energy` in the tests.

Let `E = (1/16) Σ (T_i − T_j)^2`, summed once over each undirected Moore pair (`4 W H` pairs). The factor `1/16` is part of the definition. `E` scales with the grid; it is not divided by the number of pairs. Updating cell `i` by `δ = T'_i − T_i` touches eight pairs and changes the sum of squares by `8 δ² − 16 δ Δ`, where `Δ` is that cell's neighbour excess. Dividing by 16 gives

```
dE = (1/2) δ² − δ Δ
```

in any order, because the identity uses only the field at the moment of the update.

Unclamped linear response is `δ = α Δ`, so

```
dE = −α (1 − α/2) Δ²
```

exactly. This was checked, to roundoff, on a near-uniform 8×8 field at `α ∈ {0.2, 1.5, 1.99, 2, 2.05}`.

The equality does **not** hold when the clamp shortens the step. Checked: a cell at `0.98` with neighbours at `0.2` (`Δ = −0.78`) and `α = 1.5` is sent to `0`. The unclamped formula gives `dE = −0.22815`. The actual change is `dE = −0.2842`. Same sign, different value.

What does survive the clamp, for linear `f`, is an inequality. If the cell starts in `[0, 1]` and `α > 0`, the clipped step `δ` has the same sign as `Δ` and `|δ| ≤ α |Δ|`. Write `δ = β Δ` with `0 ≤ β ≤ α`. Then `dE = β (β/2 − 1) Δ²`. For `0 < α ≤ 2` one has `β ≤ 2`, so `dE ≤ 0` for every cell, in any order, including a shortened step. At `α = 2` the unclamped update has `dE = 0`. The endpoint is marginal: energy does not increase, and the field need not homogenize. For `0 < α < 2` a cell with `Δ ≠ 0` has `β = α` when the clamp is idle, and a strictly shorter positive `β` when the clamp only trims the step, so `dE < 0`. On this lattice a non-constant field has some `Δ ≠ 0`, so one full sweep strictly decreases `E`. `E = 0` only for a constant field.

For `tanh`, `δ = α tanh(k Δ)` before the clamp. The inequality `|tanh u| ≤ |u|` gives `|δ| ≤ α k |Δ|`, and the clamp can only make `|δ|` smaller. So the same `β (β/2 − 1)` expression is `≤ 0` whenever `0 < α k ≤ 2`. A small step with `α k > 2` can increase `E` (checked at `α = 0.2`, `k = 12`). This one-cell bound is not a bound on the synchronous map. The synchronous period-2 stripe above sits at `α k = 1.6`.

Seeds 0 and 1, linear async, 32×32, 200 steps: at `α = 1.99` mean tension falls from about `0.33` to about `0.025` and `E` falls below 1; at `α = 2.05` mean tension stays near `0.23` and `E` stays above 10. The same split is visible on 100×100 by step 200 (seed 0: tension about `0.024` at `α = 1.99`, about `0.230` at `α = 2.05`). This is the content of the energy argument. It is not a claim that every `α ≤ 2` run has already homogenized, and it is not a claim that the equality `dE = −α (1 − α/2) Δ²` survives the clamp.

The range `0 < α < 2` is the same numerical range as the relaxation parameter in the Ostrowski–Reich theorem for successive over-relaxation, with a Jacobi sweep on one side and an in-place sweep on the other. That is an analogy. Nothing above is quoted from that theorem.

Linear async, seeds 0 and 1, `100×100`, 1000 steps, remain as previously measured: mean tension at step 1000 is below `10^−3` for every sampled `α` in `{0.2, 1, 4/3, 1.5, 1.9}`. At `α = 1.5`, where sync sits near tension `0.73`, async seed 0 is at about `2×10^−6`. At `α = 2.2` and `α = 2.5` those async runs do not homogenize: mean tension stays near `0.33` and `0.41`, and the clamp fires on a large fraction of updates.

## Mean tension

Mean tension at a step is

```
mean |T_i − T_j|
```

over undirected neighbour pairs. With the Moore neighbourhood those pairs are the horizontal edges, the vertical edges, and both diagonal directions, on the periodic grid. Each pair is counted once. There are `4 * W * H` of them.

The orthogonal pairs alone (no diagonals) are a different observable. Both round to 0.337 at seed 0, step 0. At step 1000 they do not agree: full Moore pairs give about `3.99×10^−4`, orthogonal pairs about `3.27×10^−4`. A quick numpy check run by the same Simulaciones agent, not in this repo, quoted `~0.00033` at step 1000. That figure matches the orthogonal subset. The mean and the standard deviation of `T` match the Moore update. This code uses the full Moore pair set, because that is the neighbourhood of the rule.

## Diagnostics

CSV columns, one row per step including step 0:

| column | definition |
|---|---|
| `mean_tension` | mean `|T_i − T_j|` over undirected Moore pairs |
| `mean_T`, `std_T` | population mean and standard deviation of `T` |
| `mean_abs_d1` | mean over cells of `|T(t) − T(t−1)|`. `nan` at step 0 |
| `mean_abs_d2` | mean over cells of `|T(t) − T(t−2)|`. `nan` at steps 0 and 1 |
| `spectral_length` | spectral length below |

A period-2 oscillation has `mean_abs_d2` near 0 while `mean_abs_d1` stays large. Slow decay of a smooth field has `mean_abs_d2` about twice `mean_abs_d1`. At α = 0.2, seed 0, sync, step 1000, those two means are about `4.3×10^−6` and `8.7×10^−6`.

`spectral_length` is `2π / sqrt(⟨k²⟩_S)`. `S` is the squared modulus of the FFT of the demeaned field, `k` is the angular wave number in radians per cell, and the average skips the zero mode. A constant field returns `nan`. A pure cosine of wavelength `L` cells returns `L`. The stripe `(−1)^y` on an even height returns `2`.

Three limits of this definition:

- A flat spectrum (the white-noise floor) has `⟨k²⟩ = 2π²/3` in the large-grid limit, so the length is `√6 ≈ 2.449`. On a 256×256 frequency grid the same average of `k²`, excluding the zero mode, is already within `0.1%` of `√6`. Seed 0 at step 0, which is one white draw, measures about `2.428`.
- The period-2 stripe returns `2`.
- Domain walls do not turn the length into a domain size, and they do not automatically pin it at one cell. The `k²` moment weights the high-`k` interfacial tail (the Porod tail; Bray, Adv. Phys. 43, 357, 1994). For a fine period-2 pattern that tail is the stripe itself, so the length stays on the lattice scale: the `tanh` `k = 8` seed-0 field at step 1000 has spectral length `2.029`, next to the pure stripe's `2`. An isolated wall is a different spectrum. Two blocks on an `N×N` grid give a length that grows like `√N`: about `10.69` at `N = 32` and about `21.35` at `N = 128`. That is not the lattice scale, and it is not the domain width. The Porod tail dominates the moment, and the length that follows is still set by how dense the walls are.

At α = 0.2, seed 0, sync, linear `f`, the length goes from about `2.43` at step 0 to about `61.8` at step 1000.

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
python -m sim.reproduce
```

The first command writes, under `outputs/`:

- `seed0_sync_linear.csv` with the columns listed above
- `seed0_sync_linear_final.png`, the final grid drawn on a colour scale of `[0, 1]`
- `seed0_sync_linear_tension.png`, mean tension against step (linear axes)
- `seed0_sync_linear_hist.png`, histogram of the final field

The second command writes `docs/figures/mean_tension_sync_vs_async.png`: mean tension against step on log-log axes, synchronous and asynchronous, seeds 0 and 1, linear `f`, α = 0.2. Step 0 is omitted because a logarithmic axis cannot show it.

The third command writes `docs/figures/alpha_sweep_stability.png`: mean tension at step 1000 against `α` (linear `f`, sync and async, seeds 0 and 1) and against `α k` (`tanh`, sync). Seeds are fixed. The dotted vertical line is `α = 4/3`. Panels that include an async series also have a dash-dot line at `α = 2`. The synchronous family that varies `k` at `α = 0.2` is drawn in green and purple, not in the async orange. Non-positive values are omitted; they are not placed at `1e-16`.

`python -m sim.reproduce` is command version `v0.1`. With no flag it runs both of the following, and either can be selected alone:

- `--tanh-k8`: synchronous `tanh`, `k = 8`, `α = 0.2`, seed 0, 100×100, 1000 steps, written under `outputs/reproduce/`.
- `--sweep`: the alpha-sweep figure above, seeds 0 and 1.

The same `tanh` run is also `python -m sim --seed 0 --f tanh --k 8 --alpha 0.2`.
