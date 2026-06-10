# Tension Theory — Software System Analysis

## Purpose

Use Tension Theory as a lens for understanding software systems.

Never analyze codebases as static structures.
Always analyze them as evolving networks of constrained state — where every module holds local knowledge, every interface carries tension, and every change incurs irreversible cost.

---

## Vocabulary

**Legacy code:** A persistent structure whose internal tension has been stabilized through historical patches.

**Technical debt:** Accumulated tension where the cost of local updates grows faster than the system's ability to adapt.

**Refactoring:** A high-cost update intended to reduce future tension gradients.

**Bug:** A local state inconsistency producing unresolved tension at runtime.

**API:** A constrained interface defining the allowable update paths between subsystems.

**Architecture:** The persistent relational structure governing which subsystems can directly exchange state.

**Test:** A state snapshot used to detect unintended tension introduced by updates.

**Dependency:** A directed edge requiring one node's state to be valid before another can update.

**Performance bottleneck:** A node or edge where update cost consistently exceeds system tolerance.

**State management:** The policy governing how nodes store, compress, and expire local memory.

---

## Analysis Algorithm

### Step 1 — Map the System Graph

Identify:

- Modules / services (nodes)
- Interfaces / calls / events (edges)
- Data and control flows (information paths)

---

### Step 2 — Determine Memory Constraints

For each relevant module ask:

- What state does it own?
- What does it assume about its neighbors?
- What is its scope of knowledge?
- What does it forget between calls?

---

### Step 3 — Detect Tensions

Search for:

- Circular dependencies
- Implicit shared mutable state
- Inconsistent interface contracts
- Over-coupled modules (change in one forces change in many)
- Deferred error handling
- Accumulated unresolved changes (merge conflicts, flagged workarounds)

---

### Step 4 — Evaluate Update Pathways

For every proposed change evaluate:

- Blast radius (how many nodes are affected)
- Information required to make the change safely
- Reversibility (can it be rolled back?)
- Test coverage of affected paths
- New tensions the change introduces

---

### Step 5 — Classify System Dynamics

Classify:

- Stable (low coupling, clear boundaries, manageable tension)
- Adaptable (well-decoupled, changes stay local)
- Fragile (high implicit coupling, changes propagate unpredictably)
- Near collapse (any change cascades broadly, test suite unreliable)
- Transforming (active refactor or migration in progress)

---

## Output Format

Always produce:

1. Module graph
2. Tension map (high-cost edges, implicit dependencies)
3. Memory constraints per module
4. Proposed update pathways with blast radius and cost estimates
5. Stability classification
6. Refactor priority list (highest tension / lowest update cost first)
