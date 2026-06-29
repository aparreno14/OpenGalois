# Milestones (math-first)

This file provides a mathematics-first milestone view of the project.
It is intentionally light on software architecture. Engineering details live in `docs/dev/plan.md`.

Normative reference: `docs/certificates/schema-v1.md` (v1.1.0).

---

## M0 — Contract freeze

Deliver:

- certificate schema v1.1.0 + normative notes
- conformance fixtures (valid/invalid)
- verifier skeleton (schema validation + input hash checks)

---

## M1 — Structural classification: irreducible / reducible

Deliver:

- separability is implicit over ℚ for irreducible inputs; no explicit witness in v1.1
- exact factorization envelope over ℚ and reducible status
- per-factor envelope `result.factor_results` (no global group claim)

---

## M2 — Discriminant parity + decisive witnesses (early exits)

Deliver:

- discriminant Δ(g) on canonical basis and square test witness
- at least one decisive witness channel:
  - Sturm real-root count shortcut, and/or
  - modular Frobenius witness (e.g., (3,2) cycle type ⇒ S5)

---

## M3 — Solvability decision (Dummit)

Deliver:

- Dummit f20 resolvent construction and rational-root witness (when present)
- group decisions:
  - A5/S5 when insoluble
  - F20 when solvable with Δ non-square
  - C5/D5 via auxiliary quadratics when solvable with Δ square

---

## M4 — Glass-box output

Deliver:

- `trace.decision_path` and `trace.reject_log`
- explanation renderer derived only from trace/evidence
- stable CLI surface (analyze/verify/explain) for demonstrations

---

## Where the real work is tracked

For the concrete tasks, see GitHub issues (especially #4, #6, #7, #9, #11, #16 and the goldens issues).
