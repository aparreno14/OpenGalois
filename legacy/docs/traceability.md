# Traceability matrix (issues ↔ artifacts)

This document links:

- GitHub issues (work items),
- documentation artifacts,
- and delivered features / proofs.

Normative reference: `docs/certificates/schema-v1.md` and `docs/certificates/examples-v1.md`.

---

## 1) Core documentation artifacts

| Artifact | Purpose | Notes |
| --- | --- | --- |
| `docs/certificates/schema-v1.md` | Normative certificate semantics (v1.1.0) | Source of truth |
| `docs/certificates/examples-v1.md` | Conformance fixtures (v1.1.0) | Source of truth |
| `docs/spec.md` | Scope, claims, non-claims, determinism | Derived |
| `docs/algorithm.md` | Mathematics-first decision procedure | Derived |
| `docs/verification.md` | Proof obligations / threat model | Derived |
| `docs/dev/backend.md` | Backend portability constraints | Non-normative |

---

## 2) Milestones (math-first)

| Milestone | Mathematical deliverable | Typical evidence sections |
| --- | --- | --- |
| M0 | Contract freeze: schema + fixtures + minimal verify | `input`, `result`, schema validation |
| M1 | Pre-checks: separability (implicit over ℚ for irreducible inputs) + reducibility + factor envelope | `checks.*`, `result.factor_results` |
| M2 | Discriminant parity + at least one decisive witness channel | `invariants.discriminant`, (`real_roots` or `modp_evidence`) |
| M3 | Solvability decision via f20 + (if needed) C5/D5 separation | `resolvents.f20`, `dummit_quadratics` |
| M4 | Glass-box output: decision path + explanation renderer | `trace.decision_path`, `trace.reject_log` |

---

## 3) Issue mapping (high-level)

This repo tracks work primarily via GitHub issues.
The most important links are:

- Schema / certificates: issue #4 (schema), issue #12/#18/#23 (fixtures/goldens)
- Verification model: issue #6 (verification.md), issue #5 (verify implementation)
- Backend boundary (non-normative): issue #7
- Canonicalization / preprocessing: issue #9
- Separability / reducible: issues #10, #11
- Core math nodes: issues #13–#17
- Glass-box rendering: issues #20–#21

If an issue description disagrees with `schema-v1.md`, treat the schema as authoritative.
