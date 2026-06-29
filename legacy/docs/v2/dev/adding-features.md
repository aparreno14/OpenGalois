# Adding features in OpenGalois (v2.0.0 proof-first workflow)

This document is a **developer guide** for extending OpenGalois while keeping the project **auditable**, **non-fragile**, and mathematically honest.

Target audiences:
- Maintainers and contributors implementing new mathematics (degree ≤4, quintic decision tree, radicals).
- Tooling/automation (including AI agents) that need a deterministic protocol for adding functionality.

This guide is **non-normative** with respect to the certificate standard. The normative specification is:
- `docs/certificates/schema-v2.0.0.md`
- `schemas/certificate/2.0.0.json`
- `docs/verification.md`

---

## 1) The rule of the project: *a feature is a lemma*

OpenGalois v2.0.0 is proof-first. Therefore:

- **Do not** add new “algorithm-specific” top-level certificate fields.
- **Do** add new proof nodes (lemma kinds) and, only when needed, new object kinds.

Every mathematical capability you add must appear as one of:
- a new `proof_node.kind`, or
- a composition (subtree) of existing `kind`s.

If it is not represented in `proof`, it is not part of the mathematical claim.

---

## 2) Before coding: design the lemma contract

A lemma kind is a semantic contract of the form:

    (inputs, witness)  ⟹  outputs

### 2.1 Lemma design template (copy/paste)

Create a file: `docs/lemmas/<KIND>.md`.

Use this template:

---

# Lemma kind: `<KIND>`

## 1) Mathematical statement

State the lemma precisely (short and checkable). If needed, specify preconditions.

## 2) Inputs / outputs

Inputs (normative):
- `inputs`: list of refs
- expected object kinds for each ref (or `$input`)

Outputs (normative):
- `outputs`: list of refs (must be keys in `objects`)
- object kind and canonical encoding expected for each output

## 3) Witness schema

List witness fields and types. Mark which fields are **canonical rationals**.

Rules:
- Witness must be **structured data**, never “explanation text”.
- If a value can be deterministically recomputed, prefer storing a **digest** over storing the full object.

## 4) Verifier obligations

Numbered list of exact checks a verifier MUST replay.

- Every obligation must be **local**: it must depend only on:
  - resolved inputs,
  - the node witness,
  - deterministic recomputation.

## 5) Failure modes

List controlled failure labels (recommended) such as:
- `construction_mismatch`
- `bad_prime`
- `noncanonical_rational`
- `type_mismatch`
- `product_mismatch`
- `not_monic`, `not_depressed`, etc.

## 6) Notes / references

Include bibliographic references if this is a standard lemma (Dummit, resolvents, etc.).

---

### 2.2 Decide where evidence lives: witness vs objects

Rule of thumb (prevents getting lost):

- Put data in **`witness`** if it is:
  - used only within the node,
  - small,
  - not reused by other nodes.

- Put data in **`objects`** if it is:
  - reused by multiple nodes (shared artefact),
  - large (would be duplicated),
  - a “mathematical value” you want to name and reference (polynomial, resolvent, integer invariant, Sturm chain, mod-p factor degrees, …).

If something is reconstructible deterministically, store:
- minimal witness + **digest** (sha256 of a canonical encoding) to detect mismatch.

---

## 3) Object kinds: introduce only what must be shared

Every `objects[id]` must have `kind`. A verifier must treat `kind` as a type tag.

### 3.1 Object design template (copy/paste)

Create a file: `docs/objects/<KIND>.md`.

---

# Object kind: `<KIND>`

## 1) Meaning
Mathematical meaning (e.g., “polynomial in Q[x] with descending coeffs”).

## 2) Canonical encoding
Required fields and invariants.

- fields required by schema/verification
- forbidden encodings (e.g., "-0")
- canonical rational rules (reference `docs/verification.md`)

## 3) Equality
Define equality so independent implementers can compare objects deterministically.

## 4) Notes / edge cases
Zero objects, constant degrees, etc.

---

### 3.2 “Type discipline” (required for non-fragile verification)

For each lemma contract, explicitly state:
- what object kind is expected for each input ref,
- what object kind is produced for each output ref.

A verifier must reject:
- missing references,
- object kind mismatches,
- missing required fields for the expected object kind.

---

## 4) Implementation protocol (3 commits)

This protocol keeps the repo stable and prevents “half-implemented” kinds.

### Commit A — docs + schema allowance (if needed)
- Add lemma docs: `docs/lemmas/<KIND>.md`
- Add object docs (if new object kinds are introduced): `docs/objects/<KIND>.md`
- If the core schema needs a structural extension (rare), update:
  - `schemas/certificate/2.0.0.json`
  - `docs/certificates/schema-v2.0.0.md`
  and add fixtures proving the change.

**Do not merge** any new lemma kind unless its doc exists.

### Commit B — generator (`analyze()`)
- Emit the new proof node(s) with:
  - `kind`
  - correct `inputs`/`outputs`
  - a minimal witness that enables replay
- Add any new `objects` entries deterministically (stable IDs if possible).

### Commit C — verifier + fixtures + tests
- Add lemma checker(s) for the new `kind` in `verify.py` dispatch.
- Add fixtures:
  - at least one `ok-*.json`
  - at least one `tamper-*.json` (schema-valid but must fail verification)
  - optionally `invalid-*.json` (schema-invalid) if relevant
- Add tests that:
  - verify all `ok-*.json` pass
  - verify all `tamper-*.json` fail
  - validate schema conformance for fixtures where intended

**Do not merge** a new lemma kind without a tamper fixture.

---

## 5) Proof structuring conventions (prevents chaos)

### 5.1 Root discipline
- `proof.root.kind` should remain `opengalois.analyze`.
- The root is a container: no witness, no outputs.

### 5.2 Phase discipline
Structure children by phases, each a subtree:

1) Optional normalization subtree:
   - `normalize.*` (degree-5 workflows often use `normalize.depressed_monic_QQ`)

2) Reducibility subtree:
   - either prove reducible via `factorization.*`,
   - or omit and proceed (irreducible is not assumed unless proven by a lemma kind).

3) Degree-based analysis subtree:
   - `degree<=4.*` nodes for degrees 1..4
   - `quintic.*` nodes for degree 5

### 5.3 Locality
Each subtree should be locally interpretable:
- it consumes a polynomial ref,
- it produces derived objects,
- it does not depend on hidden global state.

---

## 6) Naming conventions (stability over cleverness)

### 6.1 Lemma kinds (namespaces)
Use namespaces to keep the project searchable:

- `normalize.*`
- `factorization.*`
- `discriminant.*`
- `sturm.*`
- `modp.*`
- `resolvent.*`
- `dummit.*`
- `radicals.*`

Prefer names that encode field and ring:
- `compute_discriminant.QQ_to_ZZ`
- `is_square.ZZ`
- `factor_degrees.modp`
- `compute_resolvent_f20.QQ`

### 6.2 Object kinds (type tags)
Include ring/encoding in the name:
- `poly_qq_desc`
- `int_zz`
- `poly_fp_desc`
- `factor_degrees_fp`
- `sturm_chain_qq`

---

## 7) Evidence budgeting (the “don’t drown in certificates” section)

This is the primary discipline that keeps the system elegant.

### 7.1 Store minimal, replayable evidence
Evidence is for *replay*, not for “logging”. Therefore:

- If a value is deterministically recomputable from inputs+witness, do not store it fully.
- Store only:
  - the parameters needed to recompute, and
  - a digest to detect mismatches (`sha256` of canonical encoding).

### 7.2 Store large artefacts in objects only when reused
Examples:
- resolvent polynomials,
- Sturm chains,
- mod‑p factor degree lists for many primes,
- auxiliary quadratics.

If not reused, keep it in `witness` or omit entirely.

### 7.3 Use `summary` only for UX (never for verification)
If you want a human-friendly trace, put it in:
- `summary`
or in a renderer output.

Do not add verifier obligations that rely on `summary`.

---

## 8) Fixture policy (what must stay stable)

Fixtures are part of the standardization story. Keep them small and stable.

### 8.1 Naming
- `ok-*.json` : schema-valid and verify-valid
- `tamper-*.json` : schema-valid but must fail verify
- `invalid-*.json` : schema-invalid (CI expects failure)

### 8.2 What fixtures should demonstrate
Every new lemma kind must have:
- at least one “golden” `ok-*` example,
- at least one realistic tamper `tamper-*` example (changes a witness/object/ref).

---

## 9) Checklist for adding a new lemma kind

- [ ] Doc exists: `docs/lemmas/<KIND>.md`
- [ ] All object kinds referenced are documented in `docs/objects/`
- [ ] Generator emits the node deterministically
- [ ] Verifier replays the obligations and is strict on type/kind
- [ ] `ok-*` fixture added
- [ ] `tamper-*` fixture added
- [ ] CI validates schema and fixtures
- [ ] README/index updated if this changes public claims

---

## 10) Example: adding a discriminant channel (sketch)

Proposed lemma set:
- `discriminant.compute.QQ_to_ZZ`: polynomial → integer Δ (object `int_zz`)
- `zz.is_square`: integer → boolean (+ sqrt witness if true)

Objects:
- `int_zz` (canonical decimal string, no leading zeros, "-0" forbidden)

Proof structure:
- root `opengalois.analyze`
  - child `discriminant.compute.QQ_to_ZZ` producing `Δ`
  - child `zz.is_square` consuming `Δ`

The verifier obligations are exact and local (no CAS required for the checks themselves if Δ is recomputed in ℚ[x]).

---

## 11) Policy: strictness and backwards compatibility

- The verifier defaults to **strict** unknown lemma policy: unknown `kind` rejects.
- If you introduce a new lemma kind and the generator starts emitting it, you MUST ship:
  - verifier support,
  - docs,
  - fixtures,
  in the same release.

This prevents “half-verified” certificates from circulating.

---
