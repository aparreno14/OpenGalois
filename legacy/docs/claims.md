# Claims and non-claims (v1.1.0)

This is a **one-page** summary of what OpenGalois outputs mean, for a mathematically trained reader.

Normative references:

- Certificate schema v1.1.0: `docs/certificates/schema-v1.md`
- Certificate examples v1.1.0: `docs/certificates/examples-v1.md`

For fuller narrative context (derived docs):

- `docs/spec.md`
- `docs/algorithm.md`
- `docs/verification.md`

---

## 1) What OpenGalois claims

The meaning of an output is determined by `result.status` in the certificate.

### 1.1 `status = ok`

OpenGalois claims:

- the input polynomial is **irreducible** over ℚ;
- its **transitive Galois group** over ℚ is exactly one of:

  C5, D5, F20, A5, S5

- `result.solvable_by_radicals` correctly reports whether this group is solvable (i.e., whether the quintic is solvable by radicals).

Note: over characteristic 0 (in particular over ℚ), **irreducible ⇒ separable**, so separability is not reported as a separate output status.

This claim is **evidence-backed**: the certificate must contain witnesses and trace elements sufficient for an independent verifier to check the steps (as required by the schema).

### 1.2 `status = reducible`

OpenGalois claims reducibility over ℚ and provides an explicit factorization in `checks.factorization_QQ.factors` (with multiplicities).

For **degree 5 over ℚ**, reducibility implies that all irreducible factors have degree ≤ 4, hence the splitting field is **solvable by radicals**. Therefore the certificate sets:

- `result.solvable_by_radicals = true`.

It does **not** claim a global quintic transitive Galois group in the reducible case. The core field `result.galois_group` is set to `"UNKNOWN"` (placeholder).

Optional subcertificates may appear in `result.factor_results` to document per-factor conclusions, but they do not constitute a global group claim.

### 1.3 `status = unclassified`

OpenGalois makes **no group claim**. This status means the generator did not obtain sufficient evidence to classify the input.

### 1.4 `status = error`

OpenGalois makes **no mathematical claim**. This status indicates an internal error; diagnostic information may be present in `result.error`.

---

## 2) What OpenGalois does *not* claim (v1)

- In the reducible case, no claim is made about the **global** Galois group unless an extension explicitly adds such a witness.
- No claim is made about minimality/optimality of witnesses (only soundness for the claims above).
