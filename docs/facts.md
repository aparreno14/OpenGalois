# OpenGalois v3 Facts (Predicate Catalog)

This document defines the *fact language* used by OpenGalois v3 certificates and the initial
predicate catalog for the first ruleset.
It is normative unless explicitly marked as non-normative.

## 1. Facts in v3

A **Fact** is a typed proposition:

- `pred(args...)`

represented in JSON as:

```json
{
  "pred": "SomePredicate",
  "args": [{"ref":"$input"}, {"ref":"int:D"}]
}
```

### 1.1 Normative identity of a fact

The mathematical identity of a fact depends **only** on:

* `pred`
* `args` (including the referenced object values)

Evidence used by a rule does not change the statement being proven; it is computational fuel.

### 1.2 Typing and arity

* The active ruleset defines a **fact catalog** that assigns each `pred`:

  * arity (number of args),
  * expected object kinds per arg,
  * semantic meaning.

The verifier MUST reject any fact whose:

* `pred` is not in the catalog, or
* `args` length/types do not match the catalog.

### 1.3 `$input` typing

Within a ruleset for polynomials over Q, `$input` is treated as an implicit `PolyQQ` object whose
coefficients are given by `input.coeffs_qq`.

Rules may refer to `$input` directly in fact args.

---

## 2. Example facts (JSON)

### Example: discriminant and non-square

```json
{
  "pred": "DiscEq",
  "args": [{"ref":"$input"},{"ref":"int:D"}]
}
```

```json
{
  "pred": "NonSquareZ",
  "args": [{"ref":"int:D"}]
}
```

### Example: final claim

```json
{
  "pred": "IsGaloisGroupS5",
  "args": [{"ref":"$input"}]
}
```

---

---
