# Explain / Glass-box API (v3.0.0)

This document specifies how OpenGalois derives human-readable explanations from a v3 certificate.
It is **non-normative** for certificate acceptance: verifiers MUST NOT rely on any output of this layer.

However, the explanation model is designed to be:
- deterministic given (certificate + ruleset),
- derived solely from the **normative** proof graph (facts + premises + rules),
- useful for auditing and debugging.

This document uses the v3 model described in:
- `docs/spec/v3/overview.md`
- `docs/spec/v3/certificate-format.md`
- `docs/spec/v3/facts.md`
- `docs/spec/v3/rules.md`

---

## 1) Inputs and outputs

### Inputs

The explainer takes:
- a v3 certificate (schema `3.0.0`),
- the active ruleset referenced by `meta.ruleset_id`,
- optional user query parameters (see §3).

### Outputs

The explainer produces:
- a structured explanation graph (subset of the fact graph), and/or
- a formatted textual narrative (Markdown), and/or
- a machine-readable trace suitable for UI rendering.

The explainer MUST treat these fields as **non-normative**:
- `summary`
- `fact_node.statement`
- `fact_node.data`
- any `extensions` fields

They may be used as annotations, but never as sources of truth.

---

## 2) Definitions

### Fact graph

Let `facts[]` be the ordered list of fact nodes in `proof.facts[]`.
Each node has:
- `id`
- `claim` (pred + args)
- `rule`
- `premises` (ids of earlier nodes)

The explainer treats this as a DAG.

### Explanation subgraph

An explanation is a subgraph induced by selecting:
- a target fact id `T`, and
- all premises reachable from `T` by following `premises` edges backwards.

This is the minimal derivation needed to justify `T`.

---

## 3) Core explanation queries

The explainer SHOULD implement the following queries.

### 3.1 `explain_goals()`

If `proof.goals` exists:
- return explanations for each goal fact id (in goal order).

If `proof.goals` is absent:
- optionally infer “interesting” end facts (heuristic), or return empty.

### 3.2 `why(fact_id)`

Return the minimal explanation subgraph for `fact_id`.

Normative computation:
- perform a backward traversal from `fact_id` over `premises`,
- collect visited nodes,
- output them in topological order (which is a subsequence of `proof.facts[]` due to ordering constraints).

### 3.3 `why_not(target_property)`

This query is ruleset-dependent. For typical Galois workflows:

- `target_property` may be a group predicate such as `IsGaloisGroupA5($input)`.

Two recommended behaviors:

#### (A) If the certificate contains the target fact and it verifies
Return `why(fact_id_of_target)`.

#### (B) If the certificate contains a *different* verified final group claim
Return a “conflict explanation”:
- show the verified final claim(s),
- show the premises used by the theorem rule,
- and show at least one premise that contradicts the target property according to the ruleset’s exclusion map.

This requires per-ruleset metadata (non-normative but recommended), e.g.:

```yaml
exclusion_hints:
  IsGaloisGroupA5:
    excluded_by:
      - claim: {pred: NonSquareZ, args: ["D_of_input_disc"]}
        reason: "A5 requires square discriminant."
```

The explainer MUST NOT invent mathematical exclusions that are not justified by ruleset-provided hints or by explicit facts in the certificate.

### 3.4 `explain_step(fact_id)`

Return a single-step explanation:

* claim
* rule id
* premises list (ids)
* optional statement/data

This is useful for UI drill-down.

---

## 4) Explanation rendering model

A renderer converts explanation subgraphs into text. Suggested structure:

1. **Result headline** (derived from goals or selected final facts)
2. **Key invariants** (selected premises: discriminant, reducibility, resolvent properties)
3. **Derivation chain** (ordered steps)
4. **Artifacts** (optional): derived objects (e.g., `D`, resolvent polynomial) with compact rendering

### 4.1 Step formatting

Each fact node should render as:

* **Claim**: formatted predicate with pretty-printed objects
* **Justification**: rule id
* **Depends on**: premises
* **Details** (optional): from `statement` and `data`

Example (illustrative):

* Claim: `NonSquareZ(D)`
* By: `zz.nonsquare.isqrt@1`
* Depends on: `F2 (DiscEq($input, D))`
* Details: `isqrt(|D|)=...` (if present in non-normative `data`)

### 4.2 Object pretty-printing

The explainer SHOULD provide a canonical pretty-printer for:

* `PolyQQ` (e.g., `x^5 - x^2 - 1`)
* `IntZ` (decimal)
* `RatQQ` (canonical)
* lists (bounded preview + expand)

Rendering MUST be derived from object payloads (normative).
Non-normative computed strings MAY be used as hints but must never override derived rendering.

### 4.3 “Progressive disclosure”

Renderers SHOULD support:

* compact view (high-level reasoning)
* expanded view (show derived objects and intermediate facts)
* raw view (show node JSON)

---

## 5) Ruleset-specific explanation hooks (recommended)

Rulesets SHOULD ship optional, non-normative metadata for explainers, e.g.:

* human-friendly names for predicates/rules
* recommended display order / grouping
* “key invariant” tags
* short reasons for exclusions (`why_not` support)

Example (non-normative):

```yaml
predicate_labels:
  DiscEq: "Discriminant"
  NonSquareZ: "Discriminant is not a square"
  IrreducibleQQ: "Irreducible over Q"

rule_labels:
  disc.compute@1: "Compute discriminant"
  zz.nonsquare.isqrt@1: "Integer square test"
  galois.quintic.is_S5@1: "Quintic theorem: S5 criterion"
```

The explainer MAY use these labels for nicer output.

---

## 6) Example: `S5` explanation outline

Given a certificate containing:

* `F1: IrreducibleQQ($input)`
* `F2: DiscEq($input, D)`
* `F3: NonSquareZ(D)`
* `F4: ResolventF20Eq($input, R)`
* `F5: NoQRootQQ(R)`
* `F6: IsGaloisGroupS5($input)` via `galois.quintic.is_S5@1` with premises `F1,F3,F5`

`why(F6)` produces the subgraph `{F1,F2,F3,F4,F5,F6}`.

A compact narrative might be:

1. `IrreducibleQQ($input)` ⇒ transitive action on roots (quintic premise)
2. `NonSquareZ(Disc($input))` ⇒ group not contained in `A5`
3. `NoQRootQQ(ResolventF20($input))` ⇒ group not contained in `F20`
4. By theorem `galois.quintic.is_S5@1`, conclude `IsGaloisGroupS5($input)`.

The explainer can then expand to show `D` and `R` as artifacts.

---

## 7) Determinism and safety

* Explanation MUST be deterministic for a fixed (certificate + ruleset).
* Explanation MUST NOT perform network I/O.
* Explanation MUST NOT affect verification results.
* Large artifacts (e.g., high-degree resolvents) SHOULD be truncated in default views.

---
