# Verification model

This document describes what `verify(certificate)` checks for OpenGalois certificate schema `3.0.0`.

The verifier accepts iff the certificate is schema-conformant, the input identity checks pass, reference integrity holds, proof-order constraints hold, ruleset gates pass, and every fact node verifies under the selected ruleset.

Relevant documents:

- `docs/overview.md`
- `docs/certificate-format.md`
- `docs/objects.md`
- `docs/facts.md`
- `docs/rules.md`
- `docs/ruleset.md`
- `schemas/certificate/3.0.0.json`
- `docs/rulesets/le5-core@1/`
- `rulesets/le5-core@1/facts.yaml`

---

## 1. Scope

This verification model applies to certificates satisfying:

- `meta.schema_version = "3.0.0"`;
- `meta.ruleset_id = "le5-core@1"` for the current public ruleset;
- `input.domain = "Q"`;
- `input.ordering = "descending_degree"`;
- `input.degree` is in `{1, 2, 3, 4, 5}`;
- `proof` and `objects` are normative;
- `summary` is non-normative.

---

## 2. Threat model

The verifier treats the certificate as adversarial data.

It defends against:

- edits to `input`, `objects`, `proof`, `summary`, or evidence payloads;
- replay of a certificate for a different input polynomial;
- dangling object references;
- dangling or forward premise references;
- type confusion between object kinds;
- unknown-rule bypasses;
- attempts to make verification depend on non-normative fields.

Non-goals include foundational proof checking in a proof assistant and denial-of-service protection against arbitrarily large certificates.

---

## 3. Trusted computing base

The verifier assumes correctness of:

- exact integer arithmetic;
- exact rational arithmetic;
- deterministic hashing;
- exact polynomial arithmetic required by the implemented rules;
- the mathematical theorem rules encoded in the active ruleset.

The engine is not trusted.

---

## 4. Verification pipeline

A conforming verifier performs the following checks.

### 4.1 Schema conformance

The certificate is validated against `schemas/certificate/3.0.0.json`.

Schema failure implies `verified = false`.

### 4.2 Input identity

The verifier recomputes `input.hash` from the canonical `input_v1` scope:

```json
{
  "domain": "Q",
  "variable": "x",
  "ordering": "descending_degree",
  "degree": 5,
  "coeffs_qq": ["1", "0", "0", "0", "-1", "-1"]
}
```

The configured canonicalization is `jcs-rfc8785` and the hash algorithm is SHA-256.

Floats are forbidden in the hashed scope.

### 4.3 Canonical rationals

Every rational string consumed by the verifier must be canonical:

- no whitespace;
- no leading zeros except `"0"`;
- no `"-0"`;
- reduced fractions only;
- positive denominators greater than 1 for fractions.

A robust implementation parses the rational and re-encodes it canonically, accepting iff the re-encoding is byte-for-byte equal to the original.

### 4.4 Reserved `$input`

The reference `{"ref": "$input"}` refers to the top-level input polynomial.

`$input` is reserved and must not appear as a key inside `objects`.

### 4.5 Object-store integrity

For every referenced object key:

- the key exists in `objects`;
- the object is a JSON object;
- the object has a non-empty `kind`;
- the payload is canonical for its kind when consumed by a supported rule.

### 4.6 Ruleset gating

The verifier loads the ruleset selected by `meta.ruleset_id`.

It rejects if:

- the ruleset is unknown;
- a predicate is absent from the ruleset fact catalog;
- a rule id is absent from the ruleset rule catalog;
- a rule is listed but not implemented by the verifier.

### 4.7 Proof ordering

For each fact node, every premise id must refer to a fact node that appears strictly earlier in `proof.facts`.

The verifier rejects unknown premise ids and forward references.

### 4.8 Fact typing

For each fact node:

- `claim.pred` must be in the fact catalog;
- the number of arguments must match the catalog;
- each referenced object kind must match the expected kind;
- `$input` is treated as `PolyQQ`.

### 4.9 Rule dispatch

Each node is verified by dispatching to the checker registered for its `rule`.

The checker receives:

- the claim;
- already verified premise claims;
- evidence;
- referenced objects;
- input metadata.

If the checker fails, the certificate is rejected.

### 4.10 Non-normative fields

The verifier must ignore:

- `summary`;
- `statement`;
- `data`;
- rendered Markdown, LaTeX or PDF explanations;
- UI metadata.

---

## 5. Meaning of `verified = true`

If verification succeeds, then:

- the certificate matches the declared schema;
- the input hash matches the canonical input;
- referenced objects are present and canonical as required;
- proof order is valid;
- ruleset gates passed;
- every fact node was accepted by its rule checker.

It does not mean:

- the engine is correct in general;
- the verifier is a proof assistant;
- the certificate says anything about any polynomial other than its exact input.

---

## 6. Extending verification

Adding a new rule requires:

1. a rule id and rule document under `docs/rulesets/<ruleset_id>/`;
2. a machine-readable rule definition under `rulesets/<ruleset_id>/rules/`;
3. a verifier implementation;
4. passing and failing fixtures;
5. tests exercising the rule.

Semantic changes to an existing rule require a new rule version or a new ruleset version.
