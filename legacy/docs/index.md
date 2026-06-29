# OpenGalois documentation

This folder is organized to keep the project **mathematics-first** and to avoid contradictions.

## 1) Source of truth (normative)

These two documents define the certificate contract for v1.1.0. Other documentation must not contradict them.

- `docs/certificates/schema-v1.md`
- `docs/certificates/examples-v1.md`

## 2) Read next (derived but authoritative narrative)

- `docs/claims.md` — 1-page claims / non-claims summary
- `docs/certificate_v1.md` — entry point to the certificate contract (links to schema/examples)
- `docs/spec.md` — scope, claims, non-claims, determinism
- `docs/algorithm.md` — decision procedure (math-first) aligned with the certificate
- `docs/verification.md` — verification obligations and threat model
- `docs/traceability.md` — mapping from issues to artifacts

## 3) Planning

- `docs/plan.md` — math-first milestones (what is delivered and why)
- `docs/dev/plan.md` — engineering plan (non-normative)

## 4) Developer notes (non-normative)

- `docs/dev/backend.md` — “algebra boundary” and how to swap backends without changing the public meaning of the certificate

## 5) Rule for resolving conflicts

If a derived document disagrees with `schema-v1.md`, the derived document is wrong and must be updated.
