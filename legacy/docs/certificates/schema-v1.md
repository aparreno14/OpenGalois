# OpenGalois Certificate Schema v1.1.0 (Normative Notes)

This document specifies the **normative semantics** of the JSON Schema
`OpenGalois Proof-Carrying Certificate` (schema version **1.1.0**) for
**degree-5 polynomials over Q**.

The JSON Schema constrains structure and many logical implications, but a portable
standard also requires **canonicalization rules** for hashing and for interpreting
coefficients and witnesses. This document defines those rules.

---

## 1. Scope

This certificate format applies to:

* Polynomials `f(x) ∈ Q[x]` with **degree 5**
* Variable name: `x`
* Coefficient order: **descending degree**: `[a5,a4,a3,a2,a1,a0]`
* Classification of the **transitive Galois group** among the 5 transitive subgroups of `S5` **only when the input is irreducible**.

This format is **proof-carrying** in the sense that every *existential claim*
included in a certificate must provide a **witness** usable by an independent
verifier, except where explicitly stated otherwise (e.g., negative claims in v1).

### 1.1 Characteristic-0 note (separability)

Over `Q` (characteristic 0), every irreducible polynomial is separable. Therefore,
v1.1.0 **does not** expose a standalone `non_separable` status.

Polynomials with multiple roots (i.e., not squarefree) are represented by
**Q-factorization with multiplicities** and are handled under `status="reducible"`.

---

## 2. Top-level structure

A certificate is a JSON object with required fields:

* `meta`
* `input`
* `result`

Other sections are present depending on `result.status` and the evidence path:

* `normalization` (required for `status="ok"`)
* `checks` (required for `status="ok"` and `status="reducible"`)
* `invariants` (required for `status="ok"`)
* `trace` (required for `status="ok"`, recommended for others)
* Evidence channels (optional, depending on proof path):

  * `real_roots`
  * `modp_evidence`
  * `resolvents`
  * `dummit_quadratics`
* Optional extension point:

  * `extensions`

**Additional properties policy (normative):**

* All core objects are `additionalProperties: false` **except**:

  * `meta.options` (free-form)
  * `extensions` (free-form, namespaced)
  * `trace.reject_log[*]` (diagnostic payload; may include extra keys)

---

## 3. Status semantics (`result.status`)

The `result.status` field determines what the certificate claims and what must
be present.

### 3.1 `status = "ok"`

This means the certificate claims a **complete classification** of the transitive
Galois group for an irreducible quintic over `Q`.

Normatively, `status="ok"` requires:

* `checks.factorization_QQ.is_irreducible = true`
* `normalization` present (basis fixed in §6)
* `invariants.discriminant` present with nonzero `value`
* `trace.decision_path` non-empty
* A complete group classification:

  * `result.transitive_group_id ∈ {5T1,5T2,5T3,5T4,5T5}`
  * `result.galois_group ∈ {C5,D5,F20,A5,S5}` consistent with `transitive_group_id`
  * `result.solvable_by_radicals` consistent with the group (see §8.2)
* At least one evidence channel is present:

  * `real_roots` OR `modp_evidence` OR `resolvents`

### 3.2 `status = "reducible"`

This means the input polynomial is reducible over `Q` **or** not squarefree
(multiple roots), which is represented via repeated factors.

The schema requires:

* `checks.factorization_QQ.is_irreducible = false`
* `checks.factorization_QQ.unit` present (canonical nonzero rational; §11)
* `checks.factorization_QQ.factors` present (explicit factor list in `Q[x]` with multiplicities; §11)
* `result.factor_results` MUST be present (may be an empty array; §12)

No transitive group classification is provided at the top level (deterministic non-claim encoding):

* `result.transitive_group_id = null` (MUST be present)
* `result.galois_group = "UNKNOWN"` (MUST be present)

**Solvable-by-radicals for reducible (normative v1.1.0 rule):**

* `result.solvable_by_radicals` MUST be present.
* In v1.1.0, for `status="reducible"`, it MUST be `true` (fixed value).
* Verifiers MUST reject reducible certificates with `solvable_by_radicals != true`.

Rationale (non-normative): for degree-5 reducible polynomials over `Q`, the extension is solvable; v1.1.0 encodes this as a fixed `true` to keep reducible envelopes simple and deterministic.

### 3.3 `status = "unclassified"`

This means the generator cannot classify the polynomial (insufficient evidence).

No transitive group classification is provided (deterministic non-claim encoding):

* `result.transitive_group_id = null` (MUST be present)
* `result.galois_group = "UNKNOWN"` (MUST be present)
* `result.solvable_by_radicals = null` (MUST be present)

### 3.4 `status = "error"`

This means the generator failed operationally.

* `result.error` with `code` and `message` must be present.

No transitive group classification is provided (deterministic non-claim encoding):

* `result.transitive_group_id = null` (MUST be present)
* `result.galois_group = "UNKNOWN"` (MUST be present)

Recommended verifier policy for v1.1.0:

* Verifiers SHOULD reject any certificate with `status="error"` unless the consumer
  explicitly supports error-report artifacts.
* If accepted as an artifact, it MUST NOT be interpreted as a mathematical claim.

---

## 4. Rational encoding (`Q` elements)

All rationals are encoded as **strings**.

### 4.1 Accepted lexical forms

A rational is represented as:

* `"0"`
* a nonzero integer in base 10: `"7"`, `"-12"`
* a nonzero fraction `"p/q"` with integers `p` and `q`, `q ≥ 2`

### 4.2 Canonical value semantics (normative)

Verifiers MUST interpret each rational string as the mathematical rational number it denotes.

**Determinism rule (normative):** Producers MUST emit rationals in **reduced form**:

* `gcd(|p|, q) = 1`, `q > 0`
* sign carried by `p` only (e.g., `-1/2`, never `1/-2`)
* zero MUST be `"0"` (never `"0/7"`)

**Verifier robustness (recommended):**

* Verifiers MAY accept non-reduced encodings in a “lax” mode by reducing internally.
* Verifiers SHOULD provide a “strict” mode that rejects non-reduced encodings.

Verifiers MUST reject syntactically invalid encodings (including denominator `0`).

---

## 5. Witness rules (proof-carrying constraints)

The schema enforces a witness/claim discipline.

### 5.1 Discriminant square witness

In `invariants.discriminant`:

* If `is_square = true`, then `sqrt_witness` MUST be present.
* If `is_square = false`, then `sqrt_witness` MUST be absent.

Verifier MUST check:

* `sqrt_witness^2 == discriminant.value` in `Q`.

### 5.2 Resolvent root witness

In `resolvents.f20`:

* If `has_rational_root = true`, then `root_witness` MUST be present.
* If `has_rational_root = false`, then `root_witness` MUST be absent.

Verifier MUST check (for `has_rational_root = true`):

* the claimed witness is a root of the constructed resolvent polynomial under the
  declared `construction_method = "dummit_f20_v1"`.

Negative claim note (v1.1.0):

* If `has_rational_root = false`, the schema carries **no negative witness**.
  A verifier that relies on this claim MUST recompute/decide it independently.

### 5.3 Dummit quadratic witness

In each `dummit_quadratics.quad{1,2}`:

* If `is_reducible_QQ = true`, then `sqrt_discriminant_witness` MUST be present.
* If `is_reducible_QQ = false`, then `sqrt_discriminant_witness` MUST be absent.

Verifier MUST check:

* `sqrt_discriminant_witness^2 == disc(quad)` in `Q`,
  where `disc(ax^2+bx+c)=b^2-4ac`.

---

## 6. Canonical polynomial basis (`normalization`)

For `status="ok"`, invariants and evidence are computed on a **canonical basis**
declared in `normalization`.

### 6.1 Basis name

In v1.1.0:

* `normalization.basis = "depressed_monic_QQ"`

### 6.2 Meaning (normative)

Let the input polynomial be:

`f(x) = a5 x^5 + a4 x^4 + a3 x^3 + a2 x^2 + a1 x + a0` with `a5 ≠ 0`.

The depressed monic form is obtained by:

1. Making the polynomial monic by scaling:

* `f_monic(x) = (1/a5) f(x)`

2. Applying a Tschirnhaus translation (shift) to remove the quartic term:

* `g(x) = f_monic(x - s)` for `s ∈ Q` chosen so that the coefficient of `x^4` is `0`.

The certificate provides:

* `tschirnhaus_shift = s`
* `monic_scale = a5` (the scale used to monic-ize; i.e., divide by `a5`)
* `poly_coeffs = [1, 0, b3, b2, b1, b0]` for `g(x)`

Verifier MUST check that `poly_coeffs` matches the polynomial obtained by the above transformation.

All invariants and evidence in v1.1.0 are interpreted as being computed on this canonical polynomial `g(x)`.

---

## 7. Deterministic input identity (`input.hash`)

### 7.1 Canonicalization

`input.canonicalization = "jcs-rfc8785"`

This refers to **RFC 8785 JSON Canonicalization Scheme (JCS)**.

### 7.2 Hash algorithm

`input.hash_alg = "sha256"`

### 7.3 Hash scope (`hash_scope = "input_v1"`)

Normatively, the hash is computed over the JCS canonicalized JSON object:

```
{
  "domain": "Q",
  "variable": "x",
  "ordering": "descending_degree",
  "degree": 5,
  "coeffs_qq": [a5, a4, a3, a2, a1, a0]
}
```

The `input_v1` hash preimage is **exactly** the object above (no additional keys).
Its value domain is restricted to the JSON types needed by v1:

* `domain`, `variable`, `ordering` are strings
* `degree` is an integer
* `coeffs_qq` is a list of strings (canonical rationals per §4)

Producers and verifiers MUST reject floats and other JSON number forms in the hash preimage.

Metadata fields such as `input.canonicalization`, `input.hash_alg`, `input.hash_scope`, `meta.options`,
and any extensions MUST NOT affect the `input_v1` hash.

The digest is:

* `sha256( JCS(bytes_of_object_above) )` encoded as lowercase hex.

`meta.options` MUST NOT affect the hash.

---

## 8. Transitive group classification (only for `status="ok"`)

### 8.1 Normative key: `transitive_group_id`

OpenGalois uses the transitive group database label as the **normative** identifier:

* `5T1` = `C5`
* `5T2` = `D5`
* `5T3` = `F20`
* `5T4` = `A5`
* `5T5` = `S5`

The schema enforces consistency between `transitive_group_id` and `galois_group` in both directions.

### 8.2 Solvable-by-radicals consistency

The schema enforces:

* `5T1, 5T2, 5T3` ⇒ `solvable_by_radicals = true`
* `5T4, 5T5` ⇒ `solvable_by_radicals = false`

---

## 9. Evidence channels and minimal implications

A `status="ok"` certificate must include at least one of the evidence channels:
`real_roots`, `modp_evidence`, or `resolvents`.

Additionally, the schema encodes key mathematical implications.

### 9.1 `real_roots.count = 3` forces `S5`

If `status="ok"` and `real_roots.count = 3`, then:

* `result.transitive_group_id = 5T5`
* `result.galois_group = S5`
* `result.solvable_by_radicals = false`
* `invariants.discriminant.is_square = false`

### 9.2 Discriminant square excludes 3 real roots (v1 rule)

If `status="ok"` and `invariants.discriminant.is_square = true`, then:

* `real_roots.count ∈ {1, 5}` (i.e., not 3)

### 9.3 Mod-p evidence semantics (normative)

Each entry in `modp_evidence` contains:

* `p` (prime candidate)
* `is_good_prime` (boolean; see below)
* `factor_degrees` as a **canonical partition of 5**, non-decreasing

#### 9.3.1 Polynomial reduced mod p (normative)

In v1.1.0, `modp_evidence` MUST be interpreted as factorization data of the following polynomial over `F_p`:

1. Start from `normalization.poly_coeffs` (the depressed monic polynomial `g(x) ∈ Q[x]`).
2. Clear denominators to obtain an integer polynomial `G(x) ∈ Z[x]`.
3. Divide by the content of `G` (gcd of coefficients) to obtain a primitive polynomial.
4. If needed, multiply by `-1` so that the leading coefficient is positive.

Call the resulting primitive integer polynomial `G_prim(x)`.

The factorization degrees in `factor_degrees` are those of `G_prim(x) mod p` in `F_p[x]`.

#### 9.3.2 Good prime policy (normative)

For v1.1.0, a verifier MUST independently decide whether a prime is “good” for the above reduction, and MUST reject a `modp_evidence` entry that asserts `is_good_prime=true` when the verifier determines it is not good.

Recommended v1 definition:

* `p` MUST be prime.
* `p` is “good” iff `p` does not divide the discriminant of `G_prim` (equivalently: the reduction is separable / unramified at `p` for the Frobenius cycle-type test).

#### 9.3.3 Minimal witness patterns enforced by the schema

In v1.1.0, the schema uses `modp_evidence` to enforce minimal witness patterns:

* `5T5 (S5)` ⇒ contains a good prime with `factor_degrees = [2,3]` OR `real_roots.count=3`
* `5T4 (A5)` ⇒ contains a good prime with `factor_degrees = [1,1,3]`

### 9.4 Resolvent evidence constraints

If `resolvents.f20.has_rational_root = true` (with witness), then the transitive group must be one of:

* `5T1`, `5T2`, `5T3`

If `dummit_quadratics` is present, then the transitive group must be:

* `5T1` or `5T2`

---

## 10. Resolvent digest (`resolvents.f20.poly_hash`) — normative

This section defines the **portable, verifier-friendly meaning** of `resolvents.f20.poly_hash`.

### 10.1 Which resolvent polynomial is being hashed

For v1.1.0:

* `resolvents.f20.construction_method = "dummit_f20_v1"`

The resolvent polynomial `F20(x)` is constructed deterministically from the canonical polynomial declared in `normalization`:

* Start from `normalization.poly_coeffs` (the depressed monic quintic `g(x) ∈ Q[x]`).
* Apply the Dummit construction corresponding to `"dummit_f20_v1"` to produce a degree-6 resolvent polynomial `F20(x) ∈ Q[x]`.

### 10.2 Canonical coefficient list for hashing

Let the resolvent be:

`F20(x) = c6 x^6 + c5 x^5 + c4 x^4 + c3 x^3 + c2 x^2 + c1 x + c0` in `Q[x]`, with `c6 ≠ 0`.

Define the canonical coefficient list:

* `coeffs_qq = [c6,c5,c4,c3,c2,c1,c0]` in descending degree
* each coefficient encoded as a canonical rational string as in §4
* producers MUST emit reduced form (verifier MAY accept lax)

### 10.3 Hash preimage and algorithm

The hash preimage is the JCS canonicalization (RFC 8785) of the JSON object:

```
{
  "construction_method": "dummit_f20_v1",
  "coeffs_qq": [c6, c5, c4, c3, c2, c1, c0]
}
```

Then:

* `resolvents.f20.poly_hash = sha256( JCS(preimage) )` encoded as lowercase hex.

### 10.4 Verifier obligations

A conforming verifier MUST:

1. Reconstruct `g(x)` from `input` + `normalization` (§6).
2. Recompute `F20(x)` using the `"dummit_f20_v1"` construction on `g(x)`.
3. Build the coefficient list `[c6..c0]` and compute the digest per §10.3.
4. Reject if the recomputed digest does not equal `resolvents.f20.poly_hash`.

If `has_rational_root = true`, the verifier MUST additionally check that `root_witness` is a root of `F20(x)`.

---

### 11. Reducible factor lists (`checks.factorization_QQ`) — normative

When `status="reducible"`, the Q-factorization evidence is explicit and consists of:

* `unit`: a canonical nonzero rational `u ∈ Q*`
* `factors`: a list of monic, non-constant polynomials in `Q[x]` with multiplicities

The intended meaning is:

* `f(x) = u * ∏_i (f_i(x) ^ multiplicity_i)`,

where `f(x)` is the input polynomial from `input.coeffs_qq`.

Each factor item contains:

* `coeffs_qq`: polynomial coefficients in descending degree over `Q`
* `multiplicity`: integer ≥ 1 (REQUIRED in v1.1.0)

#### 11.1 Factor normalization (normative)

To make product checking deterministic over `Q[x]`, producers MUST normalize factors as follows:

* Each non-constant factor MUST be **monic** (leading coefficient = `"1"`).
* Coefficients MUST be canonical rationals per §4.
* Constant unit factors (`±1`) and any overall rational scalar MUST NOT be included as factors; the overall scalar is represented solely by `checks.factorization_QQ.unit`.

Verifiers MUST reject factor lists that violate monicity or include constant polynomials.

`checks.factorization_QQ.unit` MUST be a canonical nonzero rational per §4 (zero is forbidden).

#### 11.2 Verifier obligation (normative)

Verifier MUST check that the exact product-with-multiplicities equality holds in `Q[x]`:

* Parse `unit = u ∈ Q*` and each factor polynomial `f_i(x)`.
* Compute `P(x) = u * ∏_i (f_i(x) ^ multiplicity_i)` using exact rational arithmetic.
* Require `P(x) == f(x)`, where `f(x)` is reconstructed from `input.coeffs_qq`.

This check is the core “proof” of reducibility and also subsumes “not squarefree” via repeated factors (`multiplicity > 1`).

---

## 12. Reducible per-factor results (`result.factor_results`) — normative minimal structure

For `status="reducible"`, `result.factor_results` is an array of per-factor artifacts.

In v1.1.0, each element of `result.factor_results` MUST be an object with:

* `factor_index` (integer ≥ 0): index into `checks.factorization_QQ.factors` (0-based)
* `status` (string): one of `"ok"`, `"unclassified"`, `"error"`, `"skipped"`

Additionally:

* If `status ∈ {"ok","unclassified","error"}`, then the entry MUST include **exactly one** of:

  * `certificate_ref` (string): relative path or URI to a separate certificate-like artifact
  * `certificate_inline` (object): embedded certificate-like object (format not required to match the quintic schema)

* If `status = "skipped"`, then:

  * `reason` (string, non-empty) MUST be present, and
  * `certificate_ref` and `certificate_inline` MUST be absent

### 12.1 Consistency rules (normative)

* `factor_index` MUST be < `len(checks.factorization_QQ.factors)`.
* Consumers MUST NOT interpret `factor_results` as a claim about a single “global Galois group” for the reducible polynomial.

Rationale (v1.1.0):

* This gives a fixed, verifier-friendly envelope for reducible cases without forcing a single universal schema for all factor subproblems.

The `"skipped"` status exists to allow generators to acknowledge factors that are out of scope for v1.1.0 while keeping the reducible envelope deterministic.

---

## 13. Trace

`trace.decision_path` is a non-empty list of symbolic decision labels taken by the classifier. It is intended for auditability and reproducibility.

`trace.reject_log` is optional and may contain additional diagnostic information. Entries may include extra fields.

Trace data is normative for presence (in `status="ok"`), but not normative for exact wording.

Recommended (determinism):

* `decision_path` ordering MUST be stable for a fixed `(input, options)`.
* `reject_log` ordering SHOULD be stable.

---

## 14. Extensions

`extensions` is the only supported valve for non-standard or experimental data.

* All experimental fields MUST live under `extensions`.
* Producers MUST NOT introduce new top-level keys outside `extensions` in v1.x.

---

## 15. Verifier responsibilities (summary)

A conforming verifier MUST:

1. Validate JSON against the JSON Schema v1.1.0.
2. Parse rationals as exact elements of `Q` and enforce arithmetic equalities for all witnesses.
3. Recompute `input.hash` using JCS (RFC 8785) + sha256 over the `input_v1` scope.
4. For `status="ok"`:

   * reconstruct the canonical polynomial `normalization.poly_coeffs` from the input using `monic_scale` and `tschirnhaus_shift`,
   * interpret `modp_evidence` using the reduction semantics in §9.3.1 and apply the verifier’s “good prime” decision per §9.3.2,
   * recompute `resolvents.f20.poly_hash` per §10 and validate `root_witness` when present,
   * check mathematical implications relevant to the evidence path (including those encoded in the schema), and reject if any witness fails.
5. For `status="reducible"`:

   * verify factor normalization and the exact equality `unit * ∏ f_i^{m_i} == input` (§11),
   * enforce top-level non-claims (`galois_group="UNKNOWN"`, `transitive_group_id=null`),
   * enforce `result.solvable_by_radicals = true` (v1.1.0 fixed rule).

---

## 16. Security and determinism notes

* `meta.created_at` and `meta.options` are non-normative and MUST NOT affect the input identity hash.
* Certificates are intended to be deterministic with respect to `(input, algorithm options that affect math)`.
* Any nondeterministic runtime data MUST live under `meta.options` or `extensions` and MUST be excluded from any hashed scope.

