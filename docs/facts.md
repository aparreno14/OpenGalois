# OpenGalois v3 Facts

This document describes the generic fact language used by OpenGalois v3 certificates.

Concrete predicate names, arities and argument kinds are defined by the active ruleset. For the current public ruleset, see:

```text
docs/rulesets/le5-core@1/facts.md
rulesets/le5-core@1/facts.yaml
```

---

## 1. Facts

A fact is a typed mathematical proposition:

```text
pred(args...)
```

In JSON, a claim is represented as:

```json
{
  "pred": "SomePredicate",
  "args": [{"ref": "$input"}, {"ref": "some:object"}]
}
```

The verifier does not trust a claim merely because it appears in the certificate. A claim is accepted only when it is the claim of a fact node whose rule application verifies.

---

## 2. Fact identity

The mathematical identity of a fact depends on:

- `pred`;
- `args`, including the referenced object values.

Evidence does not change what is being claimed. Evidence is only computational fuel for the checker of a particular rule application.

---

## 3. Typing and arity

The active ruleset assigns each predicate:

- an arity;
- expected object kinds for each argument;
- a mathematical meaning.

The verifier rejects any claim whose predicate is not in the ruleset catalog, whose arity is wrong, or whose referenced objects have incompatible kinds.

`$input` is treated as an implicit `PolyQQ` object whose coefficients are given by `input.coeffs_qq`.

---

## 4. Examples for `le5-core@1`

### Discriminant

```json
{
  "pred": "Discriminant",
  "args": [{"ref": "$input"}, {"ref": "rat:D"}]
}
```

### Non-square rational

```json
{
  "pred": "NonSquareQQ",
  "args": [{"ref": "rat:D"}]
}
```

### Galois group

```json
{
  "pred": "GaloisGroup",
  "args": [{"ref": "$input"}, {"ref": "group:S5"}]
}
```

### Radical roots

```json
{
  "pred": "RadicalRoots",
  "args": [{"ref": "$input"}, {"ref": "rlist:roots"}]
}
```

---

## 5. Current predicate catalog

The authoritative catalog for the current public ruleset is:

```text
docs/rulesets/le5-core@1/facts.md
```

This generic document should not duplicate every ruleset-local predicate. Its purpose is to explain how facts work structurally.
