\# OpenGalois v3 Certificate Format (Facts/Rules)



This document specifies the on-wire JSON format for schema version `3.0.0`.

It is normative.



\## 1. Top-level structure



A certificate is a JSON object with the following top-level keys:



\- `$schema` (optional): schema URI

\- `meta` (required): generator metadata + ruleset selection

\- `input` (required): the polynomial over Q (degree 1..5) + hash

\- `objects` (optional): object store for shared derived objects

\- `proof` (required): proved facts (topologically ordered)

\- `extensions` (optional): namespaced extension point

\- `summary` (optional): non-normative UX summary



The verifier MUST ignore `summary` and any other non-normative fields for correctness.



---



\## 2. `meta`



`meta` is required and MUST contain:



\- `schema\_version`: MUST equal `"3.0.0"`

\- `generator`: non-empty string

\- `backend`: non-empty string

\- `ruleset\_id`: non-empty string (e.g. `"quintic@1"`)



`ruleset\_id` selects the set of allowed predicates and rules.

The verifier MUST reject certificates referencing unknown rulesets.



---



\## 3. `input`



`input` describes the polynomial over Q. Fields are as in v2:



\- `domain`: MUST be `"Q"`

\- `variable`: MUST be `"x"`

\- `ordering`: MUST be `"descending\_degree"`

\- `degree`: integer in `\[1..5]`

\- `coeffs\_qq`: coefficients `\[a\_n, ..., a\_0]` as canonical Q strings

\- `canonicalization`: MUST be `"jcs-rfc8785"`

\- `hash\_alg`: MUST be `"sha256"`

\- `hash\_scope`: MUST be `"input\_v1"`

\- `hash`: sha256 hex of the scoped canonical input object



\### Coefficient constraints



\- `coeffs\_qq` MUST have length `degree + 1`.

\- The first coefficient (`a\_n`) MUST be nonzero in canonical encoding.



---



\## 4. `objects` (Object store)



`objects` is an optional map from stable object ids to object records.



\### 4.1 Object id



Object ids MUST match:



\- `\[A-Za-z0-9\_.:-]+`



\### 4.2 Object record



Each object record MUST contain:



\- `kind`: non-empty string



It MAY contain additional properties (payload), but their semantics are defined by:

\- the object kind’s canonical encoding rules (spec + ruleset), and

\- the rules that consume the object.



Objects referenced by claims MUST be encoded canonically.



---



\## 5. `proof` (Proved facts)



`proof` MUST contain:



\- `version`: string (format version of the proof container; default `"1.0"`)

\- `facts`: array of fact nodes (minItems = 1)

\- `goals`: optional array of fact node ids (intended final conclusions)



\### 5.1 FactNode



Each element of `proof.facts\[]` is a FactNode with required fields:



\- `id`: unique stable identifier for this node

\- `claim`: a Fact (predicate + object references)

\- `rule`: a versioned rule identifier defined by the ruleset



Optional fields:



\- `premises`: array of fact node ids (default empty)

\- `evidence`: object (rule-defined) (optional unless required by the rule)

\- `statement`: string (non-normative)

\- `data`: object (non-normative)



\#### 5.1.1 `claim` (Fact)



A Fact is an object:



\- `pred`: predicate symbol (string) from the ruleset’s fact catalog

\- `args`: ordered array of object references (`ObjectRef`)



The verifier MUST type-check `pred` and the arity/types of `args` against the ruleset’s fact catalog.



\#### 5.1.2 `rule`



`rule` is a string, e.g.:



\- `"disc.compute@1"`

\- `"factorization.QQ.monic@1"`

\- `"galois.quintic.is\_S5@1"`



The verifier MUST reject unknown rules (not present in the selected ruleset).



\#### 5.1.3 `premises` and ordering (normative)



`proof.facts\[]` MUST be \*\*topologically ordered\*\*.



A fact node MAY ONLY reference in its `premises` the ids of fact nodes that appear \*\*strictly earlier\*\* in the `proof.facts\[]` array.



The verifier MUST reject the certificate immediately if a forward reference is detected.



This rule ensures:

\- the dependency graph is acyclic by construction,

\- a verifier can operate in a single forward pass without building a full dependency graph.



\#### 5.1.4 `evidence` (normative semantics)



Evidence is rule-defined computational fuel.



\- If a rule declares evidence required, then the verifier MUST reject nodes with missing/ill-typed evidence.

\- The mathematical identity of the proved fact depends strictly on `claim.pred` and `claim.args`, not on `evidence`.



\#### 5.1.5 Non-normative fields



\- `statement` and `data` are non-normative and MUST NOT affect acceptance.



---



\## 6. `goals`



`proof.goals` (if present) is a list of fact ids that represent the intended final claims.



\- Verifiers MAY use `goals` to determine which conclusions to report.

\- Correctness MUST NOT depend on `goals`; they are a convenience for tooling.



---



\## 7. `summary` (Non-normative)



`summary` MAY contain UX fields such as:



\- `status`

\- `galois\_group`

\- `transitive\_group\_id`

\- `solvable\_by\_radicals`



The verifier MUST ignore `summary` when deciding acceptance.



---



\## 8. Minimal example certificate (structure only)



```json

{

&nbsp; "meta": {

&nbsp;   "schema\_version": "3.0.0",

&nbsp;   "generator": "opengalois",

&nbsp;   "backend": "sympy",

&nbsp;   "ruleset\_id": "quintic@1"

&nbsp; },

&nbsp; "input": {

&nbsp;   "domain": "Q",

&nbsp;   "variable": "x",

&nbsp;   "ordering": "descending\_degree",

&nbsp;   "degree": 5,

&nbsp;   "coeffs\_qq": \["1","0","0","-1","0","-1"],

&nbsp;   "canonicalization": "jcs-rfc8785",

&nbsp;   "hash\_alg": "sha256",

&nbsp;   "hash\_scope": "input\_v1",

&nbsp;   "hash": "0000000000000000000000000000000000000000000000000000000000000000"

&nbsp; },

&nbsp; "objects": {

&nbsp;   "int:D": {"kind": "IntZ", "value": "-283"}

&nbsp; },

&nbsp; "proof": {

&nbsp;   "version": "1.0",

&nbsp;   "facts": \[

&nbsp;     {

&nbsp;       "id": "F2",

&nbsp;       "claim": {

&nbsp;         "pred": "DiscEq",

&nbsp;         "args": \[{"ref":"$input"},{"ref":"int:D"}]

&nbsp;       },

&nbsp;       "rule": "disc.compute@1",

&nbsp;       "premises": \[]

&nbsp;     }

&nbsp;   ],

&nbsp;   "goals": \["F2"]

&nbsp; }

}



(Note: the `hash` above is placeholder; a real certificate MUST have the correct hash.)



---



\## 9. Required verifier pipeline (normative behavior)



A conforming verifier MUST:



1\. Validate JSON against the schema.

2\. Validate input hash according to `hash\_alg` and `hash\_scope`.

3\. Load the ruleset specified by `meta.ruleset\_id`.

4\. Validate that each claim predicate exists in the ruleset’s fact catalog and type-check its arguments.

5\. Verify `proof.facts\[]` in order:



&nbsp;  \* for each node, validate that all `premises` reference earlier nodes,

&nbsp;  \* dispatch to the referenced rule checker using already-verified premises,

&nbsp;  \* reject immediately on the first failure.

6\. Accept the certificate iff all fact nodes verify successfully.



---

