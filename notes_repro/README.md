# Nested 3-node subgraphs

Reproduction of the Notion note [Simulate the nested 3-node subgraphs](https://app.notion.com/p/84a7f2846fba8282812f81f2fd39a6f9).

The note calls `G.add_cycle(...)`. NetworkX removed `Graph.add_cycle` in 2.4, so that call raises `AttributeError`. This script adds each triangle with `nx.add_cycle`.

Install once with `pip install -r notes_repro/requirements.txt` (from the repository root).

Run:

```bash
python notes_repro/nested_3node.py
```

Test:

```bash
python -m pytest notes_repro/test_nested_3node.py
```

Printed output:

```
Tau0=3.9927 Tau(t=10)=4.274e-07 mean=-0.0015 final_spread=1.13e-03 lambda2=0.6972
monotone decreasing: True
```

The note says it "reproduces the results provided earlier", but those earlier results are not in the note, so there is no reference output to compare against; the printed values here are the first recorded ones.

## Context

- Monotone decrease of tau is a theorem, not a finding: dτ/dt = −‖Lφ‖² ≤ 0 and the mean of φ is conserved; the test only checks the integrator.
- Spectrum: the eigenvalues of this Laplacian are 0, (5−√13)/2 with multiplicity 2, 3 with multiplicity 3, (5+√13)/2 with multiplicity 2, and 5. So λ2 = (5−√13)/2 ≈ 0.697224, not (7−√13)/2 ≈ 1.697224, which is not an eigenvalue. τ decays like e^{−2λ2 t}: on t ≥ 5, a fit of d(log τ)/dt matches −2λ2 to a relative error of 2.3e-7.
- This is standard Laplacian diffusion / consensus on a graph: R. Olfati-Saber and R. M. Murray, IEEE Trans. Automatic Control 49(9):1520–1533 (2004), https://doi.org/10.1109/TAC.2004.834113.

Results are properties of this rule, not of Tension Theory, which is defined only by the Notion page 'Acuerdo — Tension Theory' (https://app.notion.com/p/4157f2846fba81c78d22d0a883e4ad9f).
