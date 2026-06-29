# OpenGalois v3 Certificate Format

This document describes the on-wire JSON format for OpenGalois certificates with schema version `3.0.0`.

It is normative for the public schema. Rule-specific mathematical obligations live in the selected ruleset, currently `le5-core@1`.

---

## 1. Top-level structure

A certificate is a JSON object with the following top-level keys:

- `$schema` (optional): schema URI.
- `meta` (required): generator metadata and ruleset selection.
- `input` (required): the polynomial over `Q`.
- `objects` (optional): object store for shared derived objects.
- `proof` (required): proved facts, topologically ordered.
- `extensions` (optional): namespaced extension point.
- `summary` (optional): non-normative UX summary.

The verifier must ignore `summary` and all other non-normative fields when deciding correctness.

---

## 2. `meta`

`meta` is required and contains:

- `schema_version`: must equal `"3.0.0"`.
- `generator`: non-empty string.
- `backend`: non-empty string.
- `ruleset_id`: non-empty string, for example `"le5-core@1"`.

`ruleset_id` selects the set of allowed predicates and rules. The verifier rejects certificates referencing unknown or unsupported rulesets.

---

## 3. `input`

`input` describes the polynomial over `Q[x]`.

Required fields:

- `domain`: must be `"Q"`.
- `variable`: must be `"x"`.
- `ordering`: must be `"descending_degree"`.
- `degree`: integer in `1..5`.
- `coeffs_qq`: coefficients `[a_n, ..., a_0]` as canonical rational strings.
- `canonicalization`: must be `"jcs-rfc8785"`.
- `hash_alg`: must be `"sha256"`.
- `hash_scope`: must be `"input_v1"`.
- `hash`: SHA-256 hex digest of the scoped canonical input object.

Coefficient constraints:

- `coeffs_qq` has length `degree + 1`.
- The first coefficient `a_n` is nonzero in canonical encoding.
- Coefficients are canonical rational strings:
  - `"0"`;
  - nonzero integers such as `"7"` or `"-3"`;
  - reduced fractions such as `"5/2"` or `"-7/10"` with positive denominator greater than 1.

---

## 4. `objects`

`objects` is a map from stable object ids to object records.

Object ids match:

```text
[A-Za-z0-9_.:-]+
```

Each object record contains:

- `kind`: non-empty string.

Payload fields depend on the object kind. Canonical object encodings are specified in `docs/objects.md` and may be tightened by the active ruleset.

Objects referenced by claims must be encoded canonically. A verifier rejects dangling object references.

---

## 5. `proof`

`proof` contains:

- `version`: proof-container version, normally `"1.0"`.
- `facts`: array of fact nodes, with at least one item.
- `goals`: optional array of fact ids representing intended final conclusions.

### 5.1 Fact nodes

Each item of `proof.facts` is a fact node.

Required fields:

- `id`: unique stable identifier for this node.
- `claim`: a fact, namely a predicate and object references.
- `rule`: a versioned rule identifier defined by the active ruleset.

Optional fields:

- `premises`: array of earlier fact ids; default is empty.
- `evidence`: rule-defined object; required only when the rule requires it.
- `statement`: non-normative string.
- `data`: non-normative object.

### 5.2 Claims

A claim has the form:

```json
{
  "pred": "Discriminant",
  "args": [{"ref": "$input"}, {"ref": "rat:disc"}]
}
```

The verifier type-checks `pred` and the arity and kinds of `args` against the active ruleset's fact catalog.

For `le5-core@1`, examples include:

```text
IrreducibleQQ(f)
FactorizationMonicQQ(f, factors, unit)
DepressedMonicEq(f, g)
Degree(f, n)
Discriminant(f, D)
IsSquareQQ(q)
NonSquareQQ(q)
ResolventQQ(R, f, p)
GaloisGroup(f, G)
SolvableByRadicals(f)
NonSolvableByRadicals(f)
RadicalRoots(f, roots)
```

### 5.3 Rules

`rule` is a string such as:

```text
disc.QQ.compute@1
factorization.QQ.monic@1
galois_group.QQ.deg5.S5@1
radical_roots.QQ.deg4.ferrari.depressed_monic@2
```

The verifier rejects unknown rules and rules not supported by the selected ruleset.

### 5.4 Premises and proof order

`proof.facts` must be topologically ordered.

A fact node may only reference, in `premises`, fact ids that appear strictly earlier in `proof.facts`.

The verifier rejects:

- unknown premise ids;
- forward premise references;
- duplicated fact ids.

This makes the proof graph acyclic by construction and permits single-pass verification.

### 5.5 Evidence

Evidence is computational fuel for rule checkers.

If a rule declares evidence required, the verifier rejects nodes with missing or ill-typed evidence.

The mathematical identity of a proved fact depends on `claim.pred` and `claim.args`, not on `evidence`.

### 5.6 Non-normative fields

The fields `statement`, `data`, `summary`, rendered explanations and UI metadata are non-normative. They do not affect verification.

---

## 6. `goals`

`proof.goals`, when present, is a list of fact ids representing the intended final claims.

Tools may use goals to decide what to display, but verification of the fact list itself does not depend on goals.

---

## 7. Minimal structural example

```json
{
  "meta": {
    "schema_version": "3.0.0",
    "generator": "opengalois",
    "backend": "python",
    "ruleset_id": "le5-core@1"
  },
  "input": {
    "domain": "Q",
    "variable": "x",
    "ordering": "descending_degree",
    "degree": 5,
    "coeffs_qq": ["1", "0", "0", "0", "-1", "-1"],
    "canonicalization": "jcs-rfc8785",
    "hash_alg": "sha256",
    "hash_scope": "input_v1",
    "hash": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "objects": {
    "rat:disc": {"kind": "RatQQ", "value": "-283"}
  },
  "proof": {
    "version": "1.0",
    "facts": [
      {
        "id": "F1",
        "claim": {
          "pred": "Discriminant",
          "args": [{"ref": "$input"}, {"ref": "rat:disc"}]
        },
        "rule": "disc.QQ.compute@1",
        "premises": []
      }
    ],
    "goals": ["F1"]
  }
}
```

The hash above is a placeholder. A real certificate must contain the correct input hash.

---

## 8. Required verifier pipeline

A conforming verifier:

1. validates the JSON shape against the certificate schema;
2. recomputes and checks the input hash;
3. loads the ruleset specified by `meta.ruleset_id`;
4. validates object references and object canonicality as required;
5. validates fact predicate arity and argument kinds;
6. checks proof ordering and premise references;
7. verifies each fact node by dispatching to its rule checker;
8. accepts iff all normative checks succeed.
