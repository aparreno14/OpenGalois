# Verification model (v2.0.0)

This document specifies what `verify(certificate)` **MUST** do, what it is **allowed** to assume, and what `verified=true` means for **OpenGalois certificate schema v2.0.0**.

It is derived from the normative certificate semantics in:

- `docs/certificates/schema-v2.0.0.md` (schema version **2.0.0**)
- `schemas/certificate/2.0.0.json`

A verifier accepts **iff** the certificate is schema-conformant, the `proof.version` is supported, the input identity checks pass, reference integrity holds, and **every supported lemma obligation** in `proof` verifies successfully **in a strict bottom-up (post-order) traversal** under the stated TCB.

---

## 1) Scope (v2.0.0)

This verification model applies to certificates that satisfy:

- `meta.schema_version = "2.0.0"`
- `input.domain = "Q"` and `input.ordering = "descending_degree"`
- polynomial degree `input.degree ∈ {1,2,3,4,5}`
- proof-first structure: `proof` + `objects` are normative; `summary` is non-normative.

This document defines the **minimum** obligations a verifier must enforce for v2.0.0 **given the lemma kinds it recognizes**. Adding more recognized lemma kinds strengthens verification, but must not weaken the obligations defined here.

---

## 2) Threat model (v2)

The verifier is designed to defend against:

- **Tampering**: edits to `input.coeffs_qq`, `objects`, `proof`, `summary`, or witnesses.
- Mitigation: The verifier MUST treat all entries in the `objects` store as strictly untrusted/adversarial data. An object gains mathematical validity only when explicitly verified by a lemma's internal logic or output check.
- **Replay / context confusion**: using a certificate in a different context or claiming it corresponds to a different input.
  - Mitigation: the mathematical identity is pinned by `input.hash` over the fixed `input_v1` scope (see §4.2).
- **Dangling references / graph corruption**: nodes referencing non-existent objects, cycles disguised as trees, or broken object typing.
  - Mitigation: reference integrity + object kind checks (see §4.3, §4.4).
- **Type confusion attacks**: a node expecting a polynomial but receiving an unrelated object kind (e.g., an integer object).
  - Mitigation: lemma contracts must validate `objects[*].kind` for every referenced input/output.
- **Witness forgery**: presenting a witness that does not satisfy the local obligation of a lemma.
  - Mitigation: exact arithmetic recomputation checks (lemma-by-lemma).
- **Nondeterminism**: certificates varying with timestamps or random choices.
  - Mitigation: identity excludes timestamps/options; determinism is a *generation policy* and is checked only insofar as evidenced by the certificate.

Non-goals (v2.0.0):

- Proving foundational theorems inside the verifier (the verifier checks *obligations*, not the metatheory).
- Preventing denial-of-service from adversarially large certificates (v2 reduces duplication via DAG, but size limits are an implementation policy).
- Verifying lemma kinds that the verifier does not recognize.

---

## 3) Trusted computing base (TCB) (v2)

The TCB is the set of components whose correctness is assumed by the verifier.

### 3.1 Exact rationals and integers (required)

- Unbounded integer arithmetic and exact rationals are in the TCB.
- In the reference verifier, this is `int` + `fractions.Fraction`.

All equality checks in ℚ are **exact**, not floating-point.

### 3.2 Deterministic hashing (required)

- Canonicalization: RFC 8785 / JCS-equivalent serialization for the `input_v1` scope.
- Hash algorithm: SHA-256.
- The verifier must reject floats in the hashed scope (see §4.2).

### 3.3 Polynomial arithmetic over ℚ[x] (required for supported lemma set)

For the lemma kinds currently used in the v2.0.0 fixtures and reference workflow, the verifier must be able to do exact arithmetic in ℚ[x] for polynomials in descending coefficient order, including:

- multiplication
- scalar multiplication
- shifting / translation `f(x) -> f(x + t)` for rational `t`
- powering (small exponents via repeated multiplication)

This can be implemented without a CAS. If a backend CAS is used, it becomes part of the TCB to the extent it is used.

### 3.4 Additional algebra (optional / lemma-dependent)

Future lemma kinds may require:

- factorization in ℚ[x] or degree patterns over 𝔽_p[x],
- discriminants, resolvents, Sturm chains, etc.

In v2.0.0, such operations must appear **only as lemma obligations**; the schema itself remains structural.

---

## 4) Verification pipeline (MUST)

A conforming verifier MUST implement the following pipeline in this order.

### 4.1 JSON Schema conformance (Draft 2020-12)

Step 0: validate the whole certificate against `schemas/certificate/2.0.0.json`.

**Policy**:
- If schema validation fails, the verifier MUST report `verified=false`.
- The verifier MAY continue with best-effort diagnostics, but MUST NOT return `verified=true` if schema validation fails.

### 4.2 Deterministic input identity (`input.hash`)

The verifier MUST recompute `input.hash` exactly as specified by v2.0.0:

- `input.canonicalization = "jcs-rfc8785"`
- `input.hash_alg = "sha256"`
- `input.hash_scope = "input_v1"`

**Hash scope object (normative)**:

    {
      "domain": "Q",
      "variable": "x",
      "ordering": "descending_degree",
      "degree": n,
      "coeffs_qq": [a_n, a_{n-1}, ..., a_0]
    }

Domain restriction (normative for hashing input):

- The `input_v1` object contains only: objects with string keys, arrays, strings, integers, booleans, and null.
- **Floats are forbidden** in the hashed scope.

Reject if the recomputed digest does not match `input.hash`.

### 4.3 Canonical rationals (input and witnesses)

A verifier MUST enforce **strong canonicality** for every rational string that is used in any obligation it checks (at minimum: `input.coeffs_qq`, and all witness rationals in supported lemmas).

Canonical form requirements:

- Integers are encoded as `"0"`, `"7"`, `"-3"` (no leading zeros, no whitespace).
- Non-integers are encoded as reduced fractions `"p/q"` with:
  - `q > 1`
  - `gcd(|p|, q) = 1`
  - the sign is carried by `p`.
- The string `"-0"` is forbidden (must be `"0"`).

Implementation rule (recommended and sufficient):

- Parse the string to an exact rational and re-encode it canonically; accept **iff** the result equals the original string byte-for-byte.

### 4.4 Reserved input reference `$input`

`$input` is a reserved identifier used in `proof_node.inputs[*].ref` and `proof_node.outputs[*].ref`.

Normative meaning:

- `{ "ref": "$input" }` refers to the top-level polynomial described by `input.*`.
- `$input` MUST NOT appear as a key inside `objects`.

Reserved reference constraint (normative):

- `outputs` MUST NOT contain `{ "ref": "$input" }`.
  Rationale: `$input` denotes the immutable top-level input; proof steps may consume it but do not produce it.

### 4.5 Object store integrity (`objects`)

The verifier MUST enforce:

- For every key `k` in `objects`, `objects[k]` is a JSON object containing a non-empty string field `kind`.
- Keys are matched **exactly** (byte-for-byte) when resolving references.
- A certificate MUST be rejected if any reference `ref != "$input"` used in `proof` does not exist as a key in `objects`.

### 4.6 Proof traversal order (post-order / bottom-up)

Because nodes may depend on outputs produced by their descendants, a verifier MUST verify the proof in **post-order** (bottom-up):

- A node MUST NOT be evaluated until all its `children` have been verified successfully.
- If a node fails, the verifier MUST treat the whole certificate as failed (`verified=false`).

### 4.7 Lemma dispatch and strictness policy

Each `proof_node.kind` denotes a lemma contract. For each node:

- The verifier MUST reject the certificate if `kind` is missing or not a non-empty string.
- The verifier MUST apply the lemma checker registered for that `kind`.
- **Unknown lemma kinds**: by default, the verifier MUST reject the certificate if it encounters a `kind` it does not recognize.

Rationale: accepting unknown lemma kinds would allow a generator to “skip” mathematical obligations silently.

(Non-normative note: some applications may additionally report a *partial* status—schema + hash + reference integrity—while still returning `verified=false`.)

---

## 5) Minimal lemma obligations (current supported set)

v2.0.0 is extensible: new lemma kinds can be introduced without changing the core schema. However, **verification meaning** depends on which lemma kinds a verifier implements.

The table below defines the minimal obligations for the lemma kinds currently supported by the reference verifier and fixtures.

### 5.1 Lemma: `opengalois.analyze` (root container)

Purpose: structural root / container node.

Minimal obligations:

- `inputs` is a list of length 1 with a valid `ref` (typically `$input`).
- `outputs` is absent or `[]`.
- `witness` is absent.
- Children may be present.

### 5.2 Lemma: `normalize.depressed_monic_QQ`

Purpose: normalize `f(x)` to a monic depressed polynomial via a rational translation (Tschirnhaus shift) and monic scaling.

Contract (normative for this lemma kind):

- `inputs`: one polynomial ref (often `$input`).
- `outputs`: one polynomial ref to an object of kind `poly_qq_desc`.
- `witness` includes:
  - `tschirnhaus_shift`: canonical rational string
  - `monic_scale`: canonical rational string (must equal the leading coefficient of the input polynomial)

Verifier obligations (minimal):

1. Resolve input polynomial `f` from the input ref.
2. Let `a_n` be the leading coefficient of `f` and `n = deg(f)`.
3. Check `monic_scale == a_n`.
4. Let `f_m = f / a_n` (monic) and `t = (coeff of x^{n-1} in f_m) / n`.
5. Check `tschirnhaus_shift == t`.
6. Recompute the depressed polynomial `g(x) = f_m(x - t)` exactly in ℚ[x].
7. Resolve the output polynomial object and check its coefficients match `g` exactly.
8. Additionally enforce:
   - `g` is monic (`leading coefficient = 1`)
   - the `x^{n-1}` coefficient in `g` is `0`

Note on degrees:

- In the current workflow, this lemma is typically present for degree 5 inputs.
- v2.0.0 does not require it for degrees < 5; whether it appears is a *conformance* choice (not a schema requirement).

### 5.3 Lemma: `factorization.QQ.monic`

Purpose: certify an exact factorization in ℚ[x] using monic factors.

Contract (normative for this lemma kind):

- `inputs`: one polynomial ref.
- `witness` includes:
  - `unit`: canonical non-zero rational string
  - `factors`: list of entries with fields:
    - `ref`: object id of a polynomial object (`kind = poly_qq_desc`)
    - `multiplicity`: positive integer (default 1 if omitted by the schema; verifiers should treat omission as 1)

Verifier obligations (minimal):

1. Resolve input polynomial `f`.
2. Parse `unit` as a non-zero rational.
3. For each factor entry:
   - resolve the factor polynomial `f_i` and check it is non-constant and monic (leading coefficient 1),
   - raise it to its multiplicity,
   - multiply all factors together in ℚ[x].
4. Multiply the product by `unit`.
5. Check exact equality in ℚ[x] with the input polynomial `f`.

The verifier MAY accept factors in any order (commutativity).

---

## 6) Meaning of `verified=true` (and what it does NOT mean)

If `verify()` returns `verified=true`, then all of the following hold:

- the certificate is schema-conformant (v2.0.0),
- `input.hash` matches the canonical `input_v1` scope,
- all checked rational strings were canonical,
- every reference in `proof` was resolved correctly into `objects` or `$input`,
- every node in `proof` was verified bottom-up,
- every encountered lemma kind was recognized and its obligations passed.

It does **not** mean:

- the decision procedure’s theorems are proven inside the verifier,
- the certificate implies anything about any polynomial other than the exact `input_v1` polynomial,
- the generator ran with any particular options beyond what is evidenced in `proof` (options and summaries are non-normative),
- the verifier is DoS-hard for arbitrarily large certificates (size limits are a deployment policy).

---

## 7) Implementation notes (reference verifier)

- Using a different backend for verification than for generation can increase assurance, but is not required.
- A verifier should treat `summary` as UX-only and ignore it for correctness.
- For better auditability, implementations should expose per-check results (e.g., a list of `CheckResult` items) rather than a single boolean.

---

## 8) Extending verification (adding lemma kinds)

To add a new lemma kind `K`:

1. Specify its contract in documentation:
   - expected `inputs` (refs + object kinds),
   - expected `outputs` (refs + object kinds),
   - witness schema (field names and canonical rational requirements),
   - minimal obligations (recomputations / checks).
2. Implement a checker for `K` in the verifier.
3. Add fixtures:
   - at least one `ok-*` fixture demonstrating success,
   - at least one `invalid-*` fixture demonstrating failure for a meaningful tampering case.
4. Optionally define a **conformance set** describing which lemma kinds are required for a given claim.

A conformance set is a semantic contract and is **not** a JSON Schema profile: it does not alter the core schema, it specifies which lemma kinds (and checks) are expected for a particular use-case.
