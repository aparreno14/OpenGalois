# End-to-end flow (non-normative overview)

This document is a short overview. It does not define certificate semantics.
For the normative contract, see:

- `docs/certificates/schema-v1.md` (normative)
- `docs/algorithm.md` (decision procedure)
- `docs/verification.md` (verification obligations)

---

## Analyze

1) Parse input (degree-5 polynomial over ℚ).
2) Emit deterministic `input.hash` (JCS RFC8785 + SHA-256).
3) Run pre-checks:
   - factorization over ℚ (explicit factors if reducible)
4) If irreducible:
   - transform to canonical basis (`depressed_monic_QQ`)
   - compute discriminant parity
   - gather decisive evidence (Sturm, mod-p, f20, quadratics)
5) Produce:
   - `result` + `certificate` + `trace.decision_path` (and optional reject log)

## Verify

1) Validate schema conformance.
2) Recompute input hash and core witnesses.
3) Recompute (as needed) the evidence channels present.
4) Accept only if all proof obligations pass.

## Explain

Render a deterministic explanation from:

- `trace.decision_path`
- the evidence objects referenced by those steps
