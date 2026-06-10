# Tension Theory — Agency Analysis

## Purpose

Use Tension Theory as a lens for analyzing agents and the systems they form — individual decisions, strategic interactions, markets, organizations.

An agent is not a rational optimizer.
An agent is a node with finite memory making local state updates based on adjacent state only — under constraint, at cost, irreversibly.
Economics is the study of what happens when many such agents update simultaneously in a shared graph.

---

## Vocabulary

**Agent:** A node with finite memory that selects and executes local state updates based on observable adjacent state. Cannot access global configuration.

**Decision:** An irreversible state update triggered by accumulated local tension that exceeds the cost threshold for action.

**Option:** A candidate update path with an associated cost, required information, and resulting post-update state.

**Information horizon:** The boundary of what an agent can observe; determines which tensions are visible and which remain hidden.

**Stake:** The magnitude of tension being resolved — or created — by a given update.

**Commitment:** A high-cost, irreversible update that forecloses alternative paths. Cannot be undone without further high-cost updates.

**Regret:** Residual tension remaining after an irreversible update. Cannot be resolved by reversing — only by forward updates.

**Uncertainty:** Unresolved tension across multiple candidate update paths. Not fundamental indeterminism — incomplete state access due to finite memory and local observation.

**Deferral:** Accumulation of unresolved tension while awaiting a future trigger. Increases tension and eventual update cost over time.

**Cascade:** A decision that raises tension in neighboring agents, triggering further updates across the graph.

**Price:** Edge tension value in a market graph — the compressed informational difference between supply and demand states at a given moment.

**Market equilibrium:** A stable configuration where local tension gradients approach zero across the agent graph; updates lose urgency.

**Scarcity:** A hard constraint on update paths; limits the transitions available to an agent regardless of tension level.

**Value:** Persistent correlation between agent states — not intrinsic, but relational and dependent on graph structure.

**Competition:** Tension gradient across agents pursuing incompatible update paths toward the same constrained resource.

**Speculation:** An update based on anticipated future tension states rather than current local state.

**Bubble:** Local instability — agents updating based on projected tension that exceeds underlying relational support. Collapses when the projection fails.

**Coordination failure:** Each agent updates locally and rationally, but the aggregate result increases system tension rather than reducing it.

**Market failure:** A stable configuration where local updates consistently generate externalized tension — cost absorbed by non-participating nodes.

---

## Analysis Algorithm

### Step 1 — Identify the Agent Graph

For each agent:

- What is their memory capacity (what history do they hold)?
- What is their information horizon (what can they observe, what is hidden)?
- What update paths are available to them under current constraints?

---

### Step 2 — Map the Option Space

For each candidate update path:

- What state does it produce?
- What tension does it resolve?
- What new tension does it introduce?
- What information does it require to execute safely?

---

### Step 3 — Estimate Update Costs

For each option evaluate:

- Reversibility (can the state be recovered?)
- Time required
- Downstream agents affected (cascade risk)
- Side effects on non-adjacent nodes (externalities)
- Cost of gathering missing information before acting

---

### Step 4 — Model Aggregate Dynamics

When multiple agents update simultaneously ask:

- How do tension signals (prices, norms, reputations) propagate across the graph?
- Who absorbs the cost of each update?
- Who defers and accumulates tension instead of resolving it?
- Are there coordination failures — individually rational updates that increase collective tension?

---

### Step 5 — Classify System Dynamics

Classify:

- Stable (gradients low, updates local, tension resolved efficiently)
- Adaptable (agents update cheaply, new edges form to redistribute tension)
- Fragile (high leverage, thin margins, tension propagates rapidly on any perturbation)
- Near crisis (accumulated deferred tension, blocked update paths, cascade risk)
- Restructuring (active redistribution of stable configurations — roles, rules, or graph topology changing)

---

## Output Format

Always produce:

1. Agent graph (who acts, based on what information, under what constraints)
2. Option map with tension profiles (what each resolves, what each creates)
3. Information horizon per agent (what is visible, what is hidden)
4. Cost, reversibility, and cascade-risk matrix
5. Aggregate dynamics (how do individual updates compose system-wide?)
6. Stability classification and predicted evolution
