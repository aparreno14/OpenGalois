# Explain / Glass-box API

This document describes how OpenGalois derives human-readable explanations from a v3 certificate.

Explanation output is non-normative for certificate acceptance. Verifiers must not rely on rendered explanations.

The explanation layer is designed to be:

- deterministic for a fixed certificate and ruleset;
- derived from the normative proof graph;
- useful for auditing and debugging;
- independent from verification.

Relevant documents:

- `docs/overview.md`
- `docs/certificate-format.md`
- `docs/facts.md`
- `docs/rules.md`
- `docs/rulesets/le5-core@1/`

---

## 1. Inputs and outputs

The explainer takes:

- a v3 certificate;
- the active ruleset referenced by `meta.ruleset_id`;
- optional user query parameters, such as a target fact id.

The explainer may produce:

- a formatted mathematical explanation in Markdown, LaTeX, or PDF;
- a structured explanation graph;
- a debugging trace.

The explainer treats the following fields as non-normative:

- `summary`;
- `statement`;
- `data`;
- `extensions`;
- any cached display strings.

These fields may be used as hints, but never as sources of mathematical truth.

---

## 2. Fact graph

Let `proof.facts` be the ordered list of fact nodes. Each node has:

- `id`;
- `claim`;
- `rule`;
- `premises`.

The explainer treats this as a directed acyclic graph. The proof-order constraint guarantees that every premise appears earlier than the node that uses it.

---

## 3. Explanation subgraph

An explanation for a target fact id `T` is the premise-closed subgraph obtained by following premise edges backwards from `T`.

The output order is the original certificate order restricted to the selected fact ids.

This gives a minimal derivation for the target fact.

---

## 4. Core queries

### `explain_goals()`

If `proof.goals` exists, explain those fact ids in order.

If `proof.goals` is absent, the tool may infer interesting final facts such as:

- `GaloisGroup`;
- `SolvableByRadicals`;
- `NonSolvableByRadicals`;
- `RadicalRoots`.

### `why(fact_id)`

Return the premise-closed explanation subgraph for a specific fact id.

### `explain_step(fact_id)`

Return a single-step explanation containing:

- the claim;
- the rule id;
- the premise ids;
- relevant objects and evidence summaries.

### `why_not(target_property)`

This query is ruleset-dependent. It may be implemented by using explicit exclusion hints supplied by the ruleset or by showing the verified final claim that conflicts with the requested property.

The explainer must not invent mathematical exclusions that are not justified by the ruleset or by verified facts.

---

## 5. Rendering model

A renderer converts explanation subgraphs into text.

A typical narrative has:

1. a statement of the target conclusion;
2. a proof section;
3. relevant invariants, such as irreducibility, discriminant, factorization or resolvent information;
4. the final classification or radical-root step.

The renderer should avoid exposing raw fact ids and rule ids in the main mathematical prose unless the output mode is explicitly technical.

---

## 6. Object pretty-printing

Renderers should provide canonical pretty-printers for:

- `PolyQQ`;
- `MPolyQQ`;
- `RatQQ`;
- `IntZ`;
- `GroupId`;
- `PolyQQList`;
- `RadicalExpr`;
- `RadicalExprList`.

Pretty-printing must be derived from object payloads. Non-normative strings may be used as hints but must not override canonical data.

---

## 7. Example: S5 explanation outline

Given a certificate containing facts such as:

```text
Degree($input, 5)
IrreducibleQQ($input)
Discriminant($input, D)
DiscNonSquareQQ($input)
ResolventQQ(R, $input, p_dummit)
IrreducibleQQ(R)
GaloisGroup($input, S5)
```

a compact explanation may say:

1. The polynomial is irreducible of degree 5, so the Galois group is transitive in `S5`.
2. The discriminant is not a square, so the group is not contained in `A5`.
3. Dummit's sextic resolvent is irreducible, so the group is not contained in the Frobenius subgroup `F20`.
4. The remaining transitive possibility is `S5`.

The precise rule ids and object payloads remain available in the certificate.

---

## 8. Determinism and safety

The explainer:

- must be deterministic for fixed inputs;
- must not perform network I/O;
- must not affect verification;
- should truncate large artifacts in default views;
- should preserve enough detail for audit.
