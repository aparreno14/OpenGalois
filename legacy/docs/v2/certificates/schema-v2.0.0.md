# OpenGalois Certificate Schema v2.0.0 (Normative Notes)

This document specifies the **normative semantics** of the JSON Schema
**OpenGalois Proof-Carrying Certificate** (schema version **2.0.0**).

Compared to v1.x, v2.0.0 switches from a “fixed, algorithm-specific payload” to a **proof-first** model:

- The certificate’s mathematical meaning is carried by a **derivation tree** (`proof.root`) whose nodes are **typed lemmas** (`proof_node.kind`).
- Intermediate artefacts (polynomials, resolvents, discriminants, mod-p data, etc.) live in an **object store** (`objects`) that forms a DAG via references.

This document is intended to be read like an RFC-style semantics companion to the JSON Schema.

## 1. Scope

This schema is intended for **exact** computation over \(\mathbb{Q}\) and related exact rings/fields used internally by OpenGalois proofs.

It standardizes:
- Input polynomial representation for degrees 1..5 over \(\mathbb{Q}\)
- Deterministic input identity via `input.hash`
- The *structure* of a proof-carrying certificate (tree + object store)

It does **not** standardize:
- The full library of lemma kinds (`proof_node.kind`)
- The payload formats of object kinds (`objects[*].kind`) beyond `kind` itself
- The full semantics of any specific classification theorem (those live in lemma libraries / profiles)

### 1.1 Reducible vs irreducible inputs

Unlike v1.x, v2.0.0 does not encode separate “reducible mode” sections.
Reducibility is established by **lemmas** in the proof tree (e.g., a factorization lemma over \(\mathbb{Q}\)).

### 1.2 Canonical bases / normal forms (important change from v1)

v1 required a particular normalization (“depressed monic” for quintics) as a top-level requirement for `status="ok"`.
v2 makes normalization an **optional lemma**. The core format does not mandate a specific normal form; a lemma library/profile may.

## 2. Top-level structure

A certificate is a JSON object with the following required top-level keys:

- `meta` (object) — provenance + schema version
- `input` (object) — the mathematical input
- `proof` (object) — the derivation tree root

Optional top-level keys:
- `objects` (object) — object store / DAG
- `summary` (object) — non-normative UX output
- `extensions` (object) — namespaced extension point

No additional top-level keys are allowed.

## 3. `meta` (metadata)

`meta` records provenance. It is not part of the mathematical claim, except for the schema version itself.

Required:
- `meta.schema_version` — MUST equal `"2.0.0"`
- `meta.generator` — non-empty string identifying the generator (e.g., `"opengalois"`)
- `meta.backend` — non-empty string describing the computational backend used by the generator (e.g., `"sympy"`)

Optional:
- `meta.generator_version` — version string
- `meta.created_at` — timestamp (recommended to keep optional to preserve determinism policies)
- `meta.options` — free-form runtime options; verifiers MUST treat this as non-normative

**Determinism note (normative intent):**
- A verifier MUST ignore `meta.created_at` and `meta.options` when determining mathematical identity.
- Deterministic identity is established solely via `input.hash` (see §5).

---

## 4. `input` (the mathematical input)

The `input` section defines the polynomial \(f(x)\in\mathbb{Q}[x]\).

Required fields:
- `domain`: MUST equal `"Q"`
- `variable`: MUST equal `"x"`
- `ordering`: MUST equal `"descending_degree"`
- `degree`: integer in `[1,5]`
- `coeffs_qq`: array of canonical rationals `[a_n,…,a_0]`
- `canonicalization`: `"jcs-rfc8785"`
- `hash_alg`: `"sha256"`
- `hash_scope`: `"input_v1"`
- `hash`: 64-hex SHA-256 digest

### 4.1 Degree / coefficient length rule (normative)

`coeffs_qq` MUST have length `degree + 1`:

- degree 1 → 2 coefficients
- degree 2 → 3 coefficients
- …
- degree 5 → 6 coefficients

The first coefficient `a_n` MUST be nonzero (canonical nonzero rational).

### 4.2 Canonical rational encoding for coefficients (normative)

Each coefficient MUST be a canonical rational string per §6.

## 5. Deterministic input identity (`input.hash`) (normative)

The `input.hash` field commits to the mathematical input in a deterministic way, so that:
- verifiers can detect tampering, and
- external systems can index/compare inputs reliably.

### 5.1 Hash algorithm and canonicalization

- Canonicalization MUST be JSON Canonicalization Scheme (JCS) per RFC 8785.
- Hash algorithm MUST be SHA-256 over the UTF-8 bytes of the JCS-serialized “hash scope object” (§5.2).

### 5.2 Hash scope object

The verifier MUST recompute the hash over the following JSON object (and nothing else):

    {
      "domain": "Q",
      "variable": "x",
      "ordering": "descending_degree",
      "degree": 5,
      "coeffs_qq": ["1", "0", "0", "0", "0", "-1"]
    }

In general, the verifier MUST use `degree = input.degree` and `coeffs_qq = input.coeffs_qq` exactly.

**Type restriction (normative):**
- The hashed scope MUST contain only JSON objects, arrays, strings, integers, booleans, and null.
- Floating-point numbers MUST NOT appear in the hashed scope.

### 5.3 Verifier policy

A verifier MUST reject the certificate if the recomputed hash does not equal `input.hash`.

Rationale:
- Hash mismatch indicates either input tampering or a non-conforming generator/verifier.

## 6. Canonical rational strings (normative)

Canonical rationals are encoded as strings:

- Integers: `"0"`, `"7"`, `"-13"`
- Reduced fractions: `"p/q"` where:
  - `q >= 2`
  - `gcd(|p|, q) = 1`
  - `p` may be negative, `q` is positive
  - no leading zeros except `"0"`

Examples:
- `"0"`, `"-1"`, `"17"`, `"3/2"`, `"-5/7"`

Non-examples (MUST NOT appear):
- `"00"`, `"+1"`, `"2/4"`, `"1/-2"`, `"01/2"`

## 7. `objects` (object store / DAG) (normative structure, open semantics)

`objects` is an optional map from **object IDs** to **typed mathematical objects**.
If the `objects` key is omitted from the top-level, a verifier MUST treat it as an empty map `{}`.

- Each entry value MUST be a JSON object containing at least:
  - `kind`: non-empty string

- Additional fields are allowed and are interpreted by the lemma library / verifier.

**Trust model (normative):**
- Entries in `objects` MUST be treated as **untrusted data** until they are validated by successful lemma verification.
- A conforming verifier MUST NOT accept any mathematical property of an object solely because it appears in `objects`.
  The only way an object can acquire verified meaning is via the obligations of recognized `proof_node.kind` rules that
  consume/produce/audit it.

### 7.1 Object IDs

An object ID is the key in the `objects` map. References to objects use the `object_ref` structure (§8.3), which constrains referenced IDs to the pattern:

- `[A-Za-z0-9_.:-]+`

Practical guidance:
- Use stable, human-readable IDs (e.g., `poly.depressed`, `disc.delta`, `resolvent.f20`).
- Treat IDs as part of the public interface of a certificate: changing them breaks references.

### 7.2 The implicit `$input` object

The special reference `$input` refers to the polynomial defined by the `input` section.

Normatively, a verifier must be able to materialize `$input` as a polynomial object equivalent to:

- `domain = Q`, `variable = x`, `ordering = descending_degree`,
- `degree = input.degree`, `coeffs_qq = input.coeffs_qq`.

This prevents duplication: proofs can refer to the input polynomial without storing it inside `objects`.

### 7.3 Typing philosophy

The **core schema does not standardize** object payloads beyond requiring `kind`.

However, to be useful interoperably, OpenGalois SHOULD ship a “standard lemma library” that fixes:
- which object kinds exist,
- what fields they contain,
- and how each lemma verifies them.

A recommended organization is:
- `docs/lemmas/` — normative per-lemma contracts (inputs, outputs, witnesses, checks)
- `docs/objects/` — normative per-object contracts (field meanings + canonical forms)

This keeps the schema minimal while still providing precise mathematical semantics.

---

## 8. `proof` (derivation tree) (normative)

`proof` contains a derivation tree rooted at `proof.root`.

Required:
- `proof.version`: string version of the proof-tree *format* (not the certificate schema)
- `proof.root`: a `proof_node`

No additional fields are allowed under `proof`.

**Version gating (normative):**
- A conforming verifier MUST check `proof.version` before attempting proof checking.
- If `proof.version` is not supported, the verifier MUST reject the certificate immediately.
- `proof.version` SHOULD follow Semantic Versioning as a string (e.g., `"0.1"`, `"1.0.0"`).

### 8.1 `proof_node`

A proof node is a JSON object with required field:

- `kind`: string identifier of the lemma / step

Optional fields:

- `statement`: human-readable mathematical statement (non-normative, for readability)
- `inputs`: list of `object_ref` values (references to input objects)
- `outputs`: list of `object_ref` values (references to output objects)
- `witness`: free-form JSON object; **normative** to the extent the lemma requires it
- `children`: list of child `proof_node` values
- `data`: free-form JSON object; explicitly **non-normative** (pedagogy/audit hints)

### 8.2 Semantics: how the tree is meant to be read

Think of each `proof_node` as a *lemma*:

- The **children** are proofs of premises.
- The node’s lemma (`kind`) states: “Given the inputs, and assuming the children verified, I establish the claim encoded by this lemma, possibly producing outputs.”
- The node may carry a witness that makes the claim checkable.

A certificate’s mathematical claim is therefore:
- “There exists a valid derivation from `$input` to the conclusion encoded by `proof.root` under the recognized lemma set.”

### 8.3 `object_ref`

Objects are referenced via:

    { "ref": "$input" }
    { "ref": "some.object.id" }

Normative requirements for verifiers:

- `$input` is always valid (see §7.2).
- Any other reference MUST resolve to an entry in `objects`.
- A conforming verifier MUST reject the certificate if a reference cannot be resolved.
  (Tools that do not claim full-verifier conformance MAY present a partial/diagnostic view; see §8.4.1.)

### 8.4 Verification model (normative intent)

A conforming verifier MUST implement the following pipeline:

1) **Schema validation** against the JSON Schema for v2.0.0.
2) **Version gating**:
   - MUST check `proof.version` is supported; otherwise MUST reject immediately.
3) **Input identity check**: recompute `input.hash` (see §5).
4) **Reference integrity**:
   - ensure every referenced object exists (`objects[ref]`) and has `kind`,
5) **Proof checking** (recursive, post-order):
   - verify all `children` first,
   - dispatch on `node.kind` to a lemma-specific verifier,
   - if `node.kind` is not recognized by the verifier’s lemma library, the verifier MUST reject,
   - the lemma verifier MUST:
     - parse required objects/witness fields into exact mathematics,
     - recompute/check the local obligation(s),
     - treat all `objects` payloads as untrusted inputs unless validated by the lemma’s checks,
     - (optionally) recompute output objects and check they match the referenced `objects` entries.

A verifier MUST report success only if all steps above succeed.

### 8.4.1 Partial verification (non-normative)

Some applications (e.g., UI inspectors, indexers) may want to distinguish between:

- structural validity (schema + version gating + hash + reference integrity), and
- full mathematical verification (all lemma obligations under a recognized lemma library).

Such applications MAY stop after the structural checks and report a *partial* status, but:

- they MUST NOT present the certificate as mathematically verified, and
- they MUST make any missing support explicit (e.g., “unknown lemma kind”).

In contrast, a **conforming verifier** (as defined in §8.4) MUST reject on:
- unsupported `proof.version`,
- any unresolved reference, and
- any unknown `proof_node.kind`.

### 8.5 Trusted computing base (TCB) (guidance)

The TCB for verification consists of:

- the JSON Schema validator (for structural validation),
- the JCS serializer and SHA-256 implementation (for `input.hash`),
- the lemma library implementation (for mathematical verification).

To keep the TCB small:
- prefer lemma verifiers that recompute obligations directly from exact arithmetic,
- avoid trusting large opaque objects without verifying them.

---

## 9. `summary` (non-normative UX section)

`summary` is optional and **non-normative**. It may contain:
- `status` strings,
- human-readable interpretations,
- performance metadata, etc.

A verifier MUST NOT use `summary` to establish mathematical truth.

## 10. `extensions` (namespaced extension point)

`extensions` is an optional JSON object for forward compatibility.

Guidance:
- Use namespaced keys, e.g., `"opengalois.dev": {...}` or `"mygroup.extra": {...}`.
- Extensions MUST NOT alter the meaning of the core proof unless a verifier explicitly opts into that extension.

## 11. Versioning and interoperability

There are three orthogonal version axes:

1) **Certificate schema version** (`meta.schema_version`) — this document.
2) **Proof-tree format version** (`proof.version`) — structural format of `proof_node` (currently a simple tree with `kind`, refs, etc.).
3) **Lemma library version** — the semantic meaning of particular `proof_node.kind` strings and `objects[*].kind` payloads.

Recommended compatibility discipline:

- Adding new lemma kinds is non-breaking for the schema, but old verifiers will not understand them.
- Never change the meaning of an existing lemma kind without bumping the lemma library version and updating documentation.
- Keep lemma IDs stable and descriptive.

Normative verifier requirements:

- A conforming verifier MUST check `proof.version` and MUST reject certificates whose proof-tree format version it does not support.
- Unknown lemma kinds MUST be treated as verification failure (rejection) by conforming verifiers.

Guidance (in-band declaration of lemma libraries):

- The core schema does not currently include a dedicated field for a lemma-library identifier.
  If you want certificates to declare the intended lemma library/profile, use `extensions` with a namespaced key,
  e.g., `extensions["opengalois.profile"] = "quintic-transitive@1.0.0"`.
- If such an identifier is present, rigorous verifiers SHOULD reject when the declared profile is unsupported.

---

## 12. Minimal example (illustrative, not normative)

A minimal certificate skeleton (values elided):

    {
      "$schema": "https://opengalois.org/schemas/certificate/2.0.0.json",
      "meta": {
        "schema_version": "2.0.0",
        "generator": "opengalois",
        "backend": "sympy"
      },
      "input": {
        "domain": "Q",
        "variable": "x",
        "ordering": "descending_degree",
        "degree": 3,
        "coeffs_qq": ["1", "0", "-1", "1"],
        "canonicalization": "jcs-rfc8785",
        "hash_alg": "sha256",
        "hash_scope": "input_v1",
        "hash": "0000000000000000000000000000000000000000000000000000000000000000"
      },
      "objects": {
        "disc.delta": { "kind": "integer", "value": "-31" }
      },
      "proof": {
        "version": "0.1",
        "root": {
          "kind": "compute_discriminant",
          "inputs": [{ "ref": "$input" }],
          "outputs": [{ "ref": "disc.delta" }],
          "witness": { "method": "resultant_definition" },
          "statement": "Δ(f) = -31."
        }
      },
      "summary": { "status": "unclassified" }
    }

Notes:
- The semantics of `kind="compute_discriminant"` and `objects[*].kind="integer"` are not defined by the core schema.
  They must be defined by the lemma/object documentation shipped with OpenGalois (or a community profile).

---

## 13. What to document next (recommended)

To make this format interoperable, publish:

1) A lemma registry:
   - lemma `kind` strings
   - required inputs/outputs
   - witness formats
   - verification obligations

2) An object registry:
   - object `kind` strings
   - field meanings
   - canonical forms
   - size/performance considerations

3) A conformance profile for each major theorem/pipeline:
   - minimal lemma set required
   - which objects are expected
   - what the root node’s conclusion means

4) Test vectors:
   - small canonical examples
   - adversarial malformed certificates
   - cross-implementation fixtures
