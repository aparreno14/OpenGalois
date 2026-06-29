# Certificate contract (v1.1.0)

This document is a **thin entry point** to the certificate contract.

**Normative source of truth:**

- `docs/certificates/schema-v1.md` (OpenGalois Proof-Carrying Certificate, v1.1.0)
- `docs/certificates/examples-v1.md` (v1.1.0 examples: valid/invalid + interpretation)

This file intentionally avoids duplicating the schema text to prevent contradictions.

---

## 1) What the certificate is

A certificate is a JSON artifact that encodes:

- the input polynomial identity (including a deterministic hash),
- the claimed result status and (when applicable) the transitive Galois group,
- the evidence objects (witnesses) used to justify the claim,
- and a trace (`decision_path`) that describes which steps were taken.

The schema enforces required fields by status and witness presence rules.

---

## 2) How to read it

Read in this order:

1) `meta` — schema version and generator identifiers
2) `input` — polynomial coefficients over ℚ and `input.hash`
3) `result` — status and (when `status=ok`) group identifiers
4) `checks` / `normalization` / `invariants` / evidence sections — depends on status
5) `trace` — decision path and optional reject log

For the exact field definitions and invariants, see `docs/certificates/schema-v1.md`.

---

## 3) Verification

The certificate is designed to be independently verifiable.

See `docs/verification.md` for the verification model and proof obligations.
