# Decision procedure (v1.1.0)

This document describes the mathematics-first decision procedure and how it maps to the certificate fields.
It is a narrative companion to the normative schema: `docs/certificates/schema-v1.md`.

In v1.1.0, OpenGalois targets the 5 transitive subgroups of S₅:

  C5, D5, F20, A5, S5

---

## 0) Input and identity

Input is a degree-5 polynomial over ℚ, represented by coefficients in descending degree order:

  [a5, a4, a3, a2, a1, a0]

The certificate binds the input to a deterministic identity via:

- `input.canonicalization = "jcs-rfc8785"`
- `input.hash_alg = "sha256"`
- `input.hash_scope = "input_v1"`
- `input.hash`

---

## 1) Pre-checks: reducibility over ℚ

### 1.1 Factorization over ℚ (mandatory)

Factor f in ℚ[x].

- If reducible: `result.status = "reducible"`
  - witness: explicit `checks.factorization_QQ.factors`
  - optional: per-factor analysis outputs in `result.factor_results` (envelope only; no global group claim).

- If irreducible: proceed to group classification (`status="ok"` branch).

---

## 2) Canonical basis: depressed monic form

For `status="ok"`, all evidence is interpreted as computed on a canonical polynomial basis
declared by `normalization.basis`.

In v1.1.0:

- `normalization.basis = "depressed_monic_QQ"`

Construction:

1) Monic scaling: divide by a5
2) Tschirnhaus shift: x ↦ x + s (s ∈ ℚ) chosen to eliminate the x⁴ coefficient

The certificate includes:

- `normalization.monic_scale`
- `normalization.tschirnhaus_shift`
- `normalization.poly_coeffs` for the resulting canonical polynomial g(x) = x^5 + b3 x^3 + b2 x^2 + b1 x + b0

A verifier must check that this basis is consistent with the input polynomial.

---

## 3) Invariant: discriminant and parity

Compute Δ(g) exactly and test if it is a square in ℚ.

Certificate:

- `invariants.discriminant.value`
- `invariants.discriminant.is_square`
- witness if square: `invariants.discriminant.sqrt_witness`

This splits candidates:

- If Δ is a square: candidates {A5, C5, D5}
- If Δ is not a square: candidates {S5, F20}

---

## 4) Evidence channels (any subset may appear)

The certificate records the actual path taken in `trace.decision_path`.
Evidence may be provided via one or more of:

- `real_roots` (Sturm count)
- `modp_evidence` (Frobenius cycle types)
- `resolvents` (Dummit f20)
- `dummit_quadratics` (C5 vs D5)

### 4.1 Real root count (Sturm)

Compute the number of real roots of the canonical polynomial g(x).
For irreducible quintics over ℚ:

- if `real_roots.count = 3` then the group is insoluble, hence:
  - Δ square  ⇒ A5
  - Δ non-square ⇒ S5

Certificate section:

- `real_roots.method` (e.g., `"sturm"`)
- `real_roots.count`
- `trace.decision_path` step showing the lemma application

### 4.2 Modular evidence (Frobenius)

Choose primes deterministically subject to “good prime” conditions (e.g., p does not divide Δ and does not collide with denominators).

For each good prime p:

- factor g(x) modulo p in 𝔽_p[x]
- record the degrees of irreducible factors; this encodes a Frobenius cycle type

A decisive witness used in v1.1.0:

- factor degrees [3,2] ⇒ presence of a 3-cycle and a 2-cycle ⇒ transitive group is S5

Certificate section:

- `modp_evidence[]` entries including `p` and `factor_degrees`

### 4.3 Dummit resolvent f20 (solvability decision)

Construct the sextic resolvent f20(t) from the canonical polynomial g(x),
with `construction_method = "dummit_f20_v1"`.

Decision:

- If f20 has no rational root: insoluble
  - Δ square ⇒ A5
  - Δ non-square ⇒ S5
- If f20 has a rational root witness t:
  - solvable by radicals
  - Δ non-square ⇒ F20
  - Δ square ⇒ proceed to C5 vs D5

Certificate section:

- `resolvents.f20.has_rational_root`
- if true: `resolvents.f20.root_witness` and a verifier must check f20(t)=0

Note: in v1.1.0, negative claims (`has_rational_root=false`) carry no negative witness;
a verifier must recompute the decision independently if it relies on the negative claim.

### 4.4 Dummit quadratics (C5 vs D5)

Precondition: solvable by radicals and Δ is a square.

Construct two auxiliary quadratics over ℚ (Dummit’s criterion) and test reducibility in ℚ[x].
Reducibility is certified by a square discriminant witness.

Certificate section:

- `dummit_quadratics.quad1`, `dummit_quadratics.quad2`
- for each: `is_reducible_QQ` plus optional `sqrt_discriminant_witness` when reducible

The reducibility pattern determines C5 vs D5.

---

## 5) Trace: decision path and rejections

For `status="ok"`, the certificate includes:

- `trace.decision_path`: an ordered list of steps taken
- `trace.reject_log`: optional diagnostic records of eliminated candidates

The explanation renderer should be a deterministic projection of these trace objects.
