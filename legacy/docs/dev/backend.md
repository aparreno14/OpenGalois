# Backend portability (non-normative)

This document explains how OpenGalois can switch algebra backends in the future **without changing the public meaning** of the output.

**Normative reference:** the certificate schema semantics in `docs/certificates/schema-v1.md` (schema version **1.1.0**). 

---

## 1) What is normative vs what is not

### Normative (public meaning)

Normative requirements are defined by the certificate semantics and verification obligations:

* the certificate fields and their semantics (schema **v1.1.0**),
* deterministic input identity (`input.hash` over the `input_v1` scope),
* canonical polynomial basis for evidence interpretation (`normalization.basis = "depressed_monic_QQ"`),
* verification obligations for any witness/evidence section that appears in the certificate. 

### Non-normative (implementation details)

Non-normative aspects may change without changing meaning:

* which CAS/library computes gcd/factors/discriminants,
* internal representations (SymPy objects, custom classes, etc.),
* intermediate algorithms used to obtain the witnesses (as long as the emitted witnesses remain correct and verifier-checkable). 

A backend change is acceptable **iff** it preserves the normative layer.

---

## 2) Algebra boundary (minimal operation set)

A backend used by the generator/verifier must be able to perform exact computations in:

* ℚ arithmetic (fractions),
* ℚ[x] polynomial arithmetic,
* 𝔽_p[x] polynomial arithmetic (for mod-p evidence). 

Minimal operations (conceptual):

* parse polynomial from `input.coeffs_qq` into ℚ[x],
* derivative f′,
* gcd(f, f′) in ℚ[x] (for structural checks when needed),
* factorization in ℚ[x] **or** emission of explicit factors plus verifier-side product check,
* discriminant Δ (exact),
* square test in ℤ/ℚ (with sqrt witness when claimed square),
* canonicalization to the canonical basis `"depressed_monic_QQ"`:

  * monic scaling,
  * Tschirnhaus shift to eliminate x⁴, 
* (optional evidence channels) Sturm real-root count, modular reduction and factorization degrees in 𝔽_p[x],
* (later) Dummit’s f20 resolvent construction and auxiliary quadratics when those nodes are implemented. 

The exact internal algorithm is irrelevant as long as the emitted certificate is correct and verifiable.

---

## 3) Concrete boundary in v1: SymPy façade + deterministic polyops

### 3.1 Code-level rule (containment)

In v1, SymPy is the **reference backend**, but it must be contained behind a strict façade. 

**Rule:** SymPy must only be imported inside the façade module:

* `src/opengalois/core/polys.py`

All other modules (decision logic, certificate builder, verifier) must interact with algebra through:

* `opengalois.core.polys` (backend-facing façade), and
* deterministic “by-hand” routines used by the verifier (the project’s `polyops/*`, based on exact `Fraction` arithmetic).

This prevents SymPy object shapes, ordering quirks, or pretty-printing from leaking into the certificate or verifier.

### 3.2 Canonical in-memory representations (v1 engineering convention)

OpenGalois uses a single canonical in-memory model for polynomials:

* ℚ[x] polynomials: `list[Fraction]` in **descending degree order**,
* ℤ[x] polynomials: `list[int]` in **descending degree order**,
* **zero polynomial:** the empty list `[]`.

The façade (`core/polys.py`) is responsible for:

* parsing inputs into this canonical form,
* trimming leading zeros,
* converting SymPy outputs back into canonical lists.

### 3.3 Certificate data model constraint (normative compatibility)

The certificate must contain **no backend-specific artifacts**:

* no Python object dumps,
* no SymPy types,
* only JSON primitives (`str/int/bool/null`), arrays, and objects.

Rational numbers must be serialized canonically (e.g., `"p/q"` or `"p"`).

---

## 4) Determinism rules (required for portable certificates)

Determinism is enforced by policy and tests, not by trusting the backend:

1. **Factor ordering is canonical.**
   The façade must sort ℚ-factorizations deterministically (e.g., by degree + monic coefficient vector), so the same input/options produce the same factor list ordering.

2. **Mod-p factor evidence is canonical.**
   When recording factor degrees over 𝔽_p, degrees must be returned in sorted order.

3. **Non-normative metadata does not affect identity.**
   `meta.created_at` and other non-normative fields must not influence `input.hash`. 

4. **Byte-identical goldens, modulo explicitly non-hashed fields.**
   The portability contract is tested via fixtures, not assumed. 

---

## 5) Verification stance and interaction with the boundary

The verifier is mathematics-first:

* exact ℚ arithmetic is done with `fractions.Fraction` (TCB),
* witness checks are exact equalities in ℚ/ℤ,
* where the generator uses backend computations (e.g., factoring), the verifier checks the **witness obligations** (e.g., product-with-multiplicities matches the claimed polynomial, and cross-field consistency constraints hold). 

The goal is: backend differences cannot change meaning, because meaning is pinned to verifiable witnesses and schema semantics.

---

## 6) Compatibility test: golden fixtures

Backend portability is validated by **golden fixtures**:

* For each canonical input and fixed options:

  * generation must produce the same certificate (byte-identical after removing explicitly non-hashed fields),
  * verification must accept.
* Tampering tests:

  * changing a witness must be rejected,
  * changing the claimed group must be rejected. 

This makes portability a testable property rather than an architectural promise. Fixtures are organized under the v1.1.0 examples set. 

---

## 7) Practical note for the TFG scope

In the thesis scope (v1.1.0), the project implements a single reference backend (SymPy) plus a strict façade so that:

* the public certificate and verification logic never depends on SymPy types,
* the backend can be swapped later *if desired*, driven by golden compatibility and schema-conformance. 

