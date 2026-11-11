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

Results are properties of this rule, not of Tension Theory, which is defined only by the Notion page 'Acuerdo — Tension Theory' (https://app.notion.com/p/4157f2846fba81c78d22d0a883e4ad9f).
