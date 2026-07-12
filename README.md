<img width="2492" height="156" alt="Tension Theory Identity-selection (4)" src="https://github.com/user-attachments/assets/b94022ad-1caa-4841-b403-adaee9e0e8c0" />


# Tension Theory

**A foundational framework where tension — constrained informational difference — is the pre-mathematical primitive, and time, space, causality, particles, and fields emerge from finite-memory local updates on a dynamic graph.**

Version 0.1 · [Zenodo DOI: 10.5281/zenodo.20420283](https://doi.org/10.5281/zenodo.20420283) · CC BY 4.0 · Author: Roybos Nine

---

## The claim

The universe is not made of objects on a background. There is no background. There are only local states, relations between them, and a single quantity governing how they change: **tension**.

When relations operate under constraint — finite memory, local access, non-zero update cost — tension appears. When tension is reduced locally, stable correlations persist. Persistent correlations are what we call structure. Geometry is not fundamental: it is the most efficient persistent summary of relational structure.

From this, the framework derives its canonical compressions:

| Emergent quantity | Definition in TT |
|---|---|
| Time | Ordered irreversibility |
| Space | Stable relational graph |
| Causality | Dependency under locality and cost |
| Particle | Stable tension loop |
| Field | Large-scale tension gradient |
| Probability | Incomplete local knowledge |
| Observation | Constrained coupling |

```mermaid
graph TD
    A[Tension as primitive] --> B[Local updates under constraint]
    B --> C[Irreversibility]
    C --> D[Emergent time]
    B --> E[Persistent tension balance]
    E --> F[Stable forms]
    F --> G[Particles as stable loops]
    E --> H[Stable relational graph]
    H --> I[Emergent space and geometry]
    B --> J[Tension gradients at scale]
    J --> K[Fields]
```

## The ten postulates

The entire framework rests on ten postulates and nothing else — no assumptions about continuity, probability, or geometry:

1. **Finite Memory** — no global, lossless, or infinite memory exists.
2. **Local State** — no system has access to global configuration, only adjacent states.
3. **Cost of Update** — every state transition has non-zero cost, expressed as tension.
4. **Tension as Primitive** — tension is the fundamental quantity governing evolution.
5. **Discrete Updates** — continuity is an emergent approximation.
6. **Irreversibility** — perfect reversibility requires infinite memory and is excluded.
7. **Relational Structure** — no absolute space; structure arises from relations and persistent gradients.
8. **Emergent Time** — time is the ordering of irreversible updates under finite memory.
9. **Observation as Coupling** — no external observer, no special measurement rule.
10. **Stability via Constraint** — persistent forms are configurations where gradients locally balance.

Full definitions and formal treatment are in the paper (sections 2–4).

## What this is not

**Not metaphor.** The objective is formalization. If the model is wrong, it should fail mathematically. If it is correct, it should produce testable differences from existing frameworks. Validity here means executable prediction, not elegance.

**Not a cellular automaton.** CAs run fixed rules on a fixed lattice with a global clock. TT graphs have dynamic, cost-aware topology, no global tape, and no global synchronization requirement (paper section 6.4).

**Not finished.** Version 0.1 establishes structural emergence. The quantitative mapping to known physics is the open program, and the line between the two is kept explicit throughout.

## Simulator

A minimal reference implementation of the TT update cycle lives in `scripts/tension_graph.py`. It enforces the framework's constraints as code-level invariants: finite memory per node, non-zero cost per update, no global reads or writes inside update logic, bounded fan-out. The update cycle is strictly local: Read → Evaluate → Decide → Apply → Propagate.

Observables are coarse-grained patterns only: persistent subgraphs, stable tension distributions, propagation delays, update frequencies. The headline result to chase is the detection of a persistent subgraph — a particle.

**First experimental observation:** update ordering changes the character of emergent structure. Synchronous node ordering produces oscillating "breathing forms"; asynchronous ordering produces frozen stable structures. This is itself a result about how emergent dynamics depend on update scheduling.

Roadmap: minimal Python prototype → measurable emergence thresholds → real-time generative web-based visualization.

## Open problems

The paper is explicit about what is unsolved (section 10). In priority order:

1. **Formal specification of τ.** The tension function must be local, respect finite memory, and reproduce known limits when coarse-grained. Any candidate must pass all three conditions and run in the reference implementation before being considered serious.
2. **Quantitative, falsifiable predictions.** Structural emergence is established; numbers are not. This is the standard the framework holds itself to.
3. **Bell inequality violations.** TT's stored-correlations account of entanglement faces genuine pressure from Bell. This is treated as a live threat to the framework, not a solved issue.
4. **Emergence thresholds.** At what graph sizes and constraint regimes do stable forms reliably appear?

## Interpretive extensions (beyond the v0.1 core)

The following are directions the framework points toward, clearly separated from what the paper formally claims:

- **Quantum uncertainty** as underconstrained relational states prior to stabilization.
- **Black holes** as extreme relational compression limiting outward propagation of structure.
- **Consciousness** as a local recursive loop of the system observing and constraining itself — the same update dynamics, coupled to themselves.

These are conceptual, not derived. They become claims only when they produce calculations.

## Repository contents

- `paper/` — Tension Theory v0.1 (also on [Zenodo](https://doi.org/10.5281/zenodo.20420283))
- `diagrams/` — structural diagrams of the framework
- `scripts/` — reference simulator and experiments
- `docs/` — postulates, definitions, formal model notes
- `problems/` — open problems and current research state

## Contributing

The framework wants to be stress-tested, not flattered. The most valuable contributions are: candidate τ functions that pass the three conditions, simulator experiments that measure emergence thresholds, and rigorous objections — especially around Bell locality.

## Citation

```
Roybos Nine (2026). Tension Theory v0.1. Zenodo.
https://doi.org/10.5281/zenodo.20420283
```

Licensed under CC BY 4.0.

If the model is wrong, it should fail mathematically.
If it is correct, it should produce testable differences from existing frameworks.

This is an open attempt to derive physics, geometry, and observers from a single principle:
Self-referential information optimizing under constraint.
