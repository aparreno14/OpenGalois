# OpenGalois specification (v1.1.0 documentation set)

This document states what OpenGalois is trying to prove, for whom, and under which assumptions.
It is written for a mathematically trained reader.

Normative reference: `docs/certificates/schema-v1.md` (schema version 1.1.0).

---

## 1) Problem and scope

Given a quintic polynomial

  f(x) ∈ ℚ[x],  deg(f)=5

OpenGalois aims to:

1) Decide whether the splitting field extension over ℚ is **solvable by radicals**.
2) In the irreducible case, classify the **transitive Galois group** among the 5 transitive subgroups of S₅:

  C5, D5, F20, A5, S5

This project focuses on producing an auditable, verifiable artifact, not on black-box answers.

---

## 2) Public API semantics

OpenGalois exposes three conceptual operations:

- analyze(f, options) → (result, certificate)
- verify(certificate, options) → verified_result
- explain(certificate) → explanation (derived only from the certificate)

The certificate is designed to be portable and independently verifiable.
Explanations are not proof objects; they are a human-readable rendering of the proof-carrying certificate.

---

## 3) Certificate-first philosophy

The certificate is the primary output. The key design principle is:

  claim + evidence + verifier

A certificate is acceptable if:

- it conforms to the schema,
- every positive claim includes a witness (as required by the schema),
- and an independent verifier can re-check the necessary steps.

This is the core “glass-box” requirement.

---

## 4) Claims and non-claims (by status)

The meaning of the output is determined by `result.status`.

### 4.1 status = ok

The certificate claims:

- the polynomial is irreducible over ℚ,
- and its transitive Galois group is exactly one of {C5, D5, F20, A5, S5}.

Over characteristic 0 (in particular over ℚ), irreducible implies separable, so separability is not reported separately.

The certificate must contain enough evidence for a verifier to accept the claim.

### 4.2 status = reducible

The certificate claims reducibility over ℚ and provides explicit factors (with multiplicities) in `checks.factorization_QQ.factors`.

It does NOT claim a global quintic transitive Galois group.

It may include per-factor subcertificates in `result.factor_results`, but those do not constitute a global group claim.

### 4.3 status = unclassified

The generator could not classify the input with the available evidence.
No transitive group claim is made.

### 4.4 status = error

The generator encountered an error (e.g., unsupported input, invalid options, or internal backend failure).
The generator returns diagnostic information in `result.error`.
No mathematical claim is made.

---

## 5) Determinism and canonical basis

Two determinism layers matter:

1) Deterministic input identity (`input.hash`):
   - canonicalization: JCS RFC8785
   - hash: SHA-256
   - hash scope: `input_v1`

2) Canonical polynomial basis for evidence (`normalization.basis`):
   - v1.1.0 uses `depressed_monic_QQ`
   - evidence is interpreted as computed on the canonical polynomial g(x) derived from f(x) by:
     - monic scaling, and
     - Tschirnhaus translation to eliminate the x⁴ term.

Both are verifier-checkable (see `docs/verification.md`).

---

## 6) Backend stance (mathematics-first)

In v1, SymPy is a reference implementation of algebraic operations.
However, the backend is **non-normative**: the certificate format and its verification obligations define the public meaning.

A future backend change is acceptable if it:

- emits schema-conformant certificates, and
- passes the same golden fixtures (same input/options → same certificate, modulo explicitly non-hashed fields).

Details: `docs/dev/backend.md`.
