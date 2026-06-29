# Glossary (v2.0.0)

This glossary defines terms as used by OpenGalois **certificate schema v2.0.0**.

Conventions:

- \(\mathbb{Q}\) denotes the field of rationals.
- \(\mathbb{Q}[x]\) denotes the polynomial ring in the variable \(x\) with rational coefficients.
- Coefficients are encoded in **descending degree order** unless stated otherwise.

---

## Certificate
A JSON document that encodes:

- the input polynomial (`input`),
- a proof/derivation (`proof`),
- a shared object store (`objects`),
- a non-normative UX summary (`summary`).

A certificate is *proof-carrying* if every existential claim is accompanied by a witness that enables independent checking.

## Schema conformance
The property that a certificate validates against the JSON Schema file `schemas/certificate/2.0.0.json` (Draft 2020-12).

Schema conformance checks **structure**, not mathematical correctness.

## Proof-first
A design principle: mathematical meaning is carried by `proof` (lemma nodes) and `objects`. Any other section (especially `summary`) is not trusted for correctness.

## Proof (derivation)
The `proof` section contains:

- `version`: proof-format version string (currently `"0.1"`),
- `root`: a `proof_node` representing the root of a derivation tree.

A verifier processes the proof **bottom-up** (post-order), ensuring every lemma obligation is satisfied.

## Proof node
A JSON object representing one step in the derivation.

Key fields:

- `kind`: the lemma identifier (string),
- `inputs`: references to objects or `$input`,
- `outputs`: references to objects produced by this step,
- `witness`: locally-checkable evidence used by the verifier,
- `children`: sub-lemmas that must be verified before the node is verified.

## Lemma kind
The identifier `proof_node.kind`. It names a **semantic contract** (a lemma) specifying:

- expected input object kinds,
- expected output object kinds,
- required witness fields (and canonical formats),
- the exact recomputation obligations for verification.

Lemma contracts live in `docs/lemmas/`.

## Unknown lemma policy (strictness)
The default policy is **strict**: if a verifier encounters a lemma kind it does not recognize, it rejects the certificate.

Rationale: accepting unknown lemmas would allow skipping obligations silently.

## Object store
The `objects` dictionary at the certificate top level. It stores named intermediate artefacts so they can be referenced by multiple proof nodes (deduplication).

## Object kind
The identifier `objects[id].kind`. It names the type/meaning of an object (e.g., `poly_qq_desc`).

Object contracts live in `docs/objects/`.

## DAG (directed acyclic graph)
The conceptual structure formed by proof nodes plus object references. Although `proof` is a tree syntactically, sharing objects across nodes yields a DAG.

## Reference (`ref`)
A string used in `inputs[i].ref` and `outputs[j].ref`.

- If `ref == "$input"`, it denotes the top-level polynomial in `input`.
- Otherwise, it must match a key in `objects` exactly (byte-for-byte).

## `$input` (reserved reference)
A reserved reference string denoting the top-level input polynomial described by `certificate.input`.

- `$input` MUST NOT be a key in `objects`.
- A proof node MUST NOT claim to *produce* `$input` (i.e., outputs must not contain `$input`).

## Witness
The `witness` object inside a proof node. It is evidence enabling local verification.

A witness is not “explanation text”; it is structured data that the verifier can recompute/check.

## Obligation (verifier obligation)
A concrete check a verifier must perform for a lemma. Typical obligations include:

- recomputing a derived polynomial,
- checking a factorization product equals the input,
- checking invariants (monic, depressed, nonzero unit),
- checking canonical forms.

## Canonical rational (string)
Rational numbers are encoded as strings either:

- integer form: `"0"`, `"7"`, `"-3"`
- reduced fraction form: `"p/q"` with `q > 1`, `gcd(|p|, q) = 1`

The string `"-0"` is forbidden.

Canonicality is enforced for `input.coeffs_qq` and for witness rationals in verified lemmas.

## Canonicalization (JCS / RFC 8785)
A deterministic JSON serialization used to define the hashed identity of the input polynomial. OpenGalois uses an RFC 8785 / JSON Canonicalization Scheme equivalent for the `input_v1` scope.

## `input_v1` scope
The exact JSON object whose canonical bytes are hashed to obtain `input.hash`:

    {
      "domain": "Q",
      "variable": "x",
      "ordering": "descending_degree",
      "degree": n,
      "coeffs_qq": [...]
    }

Fields such as `hash_alg`, `hash_scope`, timestamps, and options are not part of this scope.

## Identity hash (`input.hash`)
A SHA-256 digest of the canonical serialization of the `input_v1` scope.

It binds the certificate to a specific mathematical input polynomial.

## Summary (UX-only)
The `summary` section contains non-normative convenience fields (e.g., status labels). Verifiers must ignore summary fields for correctness.

## Verifier
An independent program that checks a certificate.

A verifier MUST:
- validate schema conformance,
- recompute and check `input.hash`,
- enforce reference integrity,
- verify every lemma in the proof bottom-up,
- reject unknown lemma kinds under the strict policy.

## Generator
The program that produces certificates (OpenGalois itself). The generator is not trusted by verification; it is treated as an adversarial source of claims.

## TCB (trusted computing base)
The components assumed correct by the verifier, typically:
- exact integer/rational arithmetic,
- deterministic hashing,
- basic polynomial arithmetic over \(\mathbb{Q}[x]\).

## Conformance set
A human-readable contract describing which lemma kinds (and sometimes which invariants) are required to support a given high-level claim.

A conformance set is **not** a JSON Schema profile; it does not change the core schema.
