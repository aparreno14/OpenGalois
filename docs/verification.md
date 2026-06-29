\# Verification model (v3.0.0)



This document specifies what `verify(certificate)` \*\*MUST\*\* do, what it is \*\*allowed\*\* to assume,

and what `verified=true` means for \*\*OpenGalois certificate schema v3.0.0\*\*.



It is derived from the normative certificate semantics in:



\- `docs/spec/v3/overview.md`

\- `docs/spec/v3/certificate-format.md`

\- `docs/spec/v3/objects.md`

\- `docs/spec/v3/facts.md`

\- `docs/spec/v3/rules.md`

\- `docs/spec/v3/ruleset.md`

\- `schemas/certificate/3.0.0.json`

\- the active ruleset referenced by `meta.ruleset\_id` (fact catalog + rule catalog + any assets)



A verifier accepts \*\*iff\*\* the certificate is schema-conformant, the input identity checks pass,

reference integrity holds, the proof order constraints hold, the ruleset gates pass, and \*\*every fact

node verifies successfully\*\* under the stated TCB.



---



\## 1) Scope (v3.0.0)



This verification model applies to certificates that satisfy:



\- `meta.schema\_version = "3.0.0"`

\- `input.domain = "Q"` and `input.ordering = "descending\_degree"`

\- polynomial degree `input.degree ∈ {1,2,3,4,5}`

\- proof-first structure:

&nbsp; - `proof` + `objects` are normative,

&nbsp; - `summary` is non-normative.



This document defines the \*\*minimum\*\* obligations a verifier must enforce for v3.0.0 \*\*for the

specific ruleset(s) it claims to support\*\*.



---



\## 2) Threat model (v3)



The verifier is designed to defend against:



\- \*\*Tampering\*\*: edits to `input.coeffs\_qq`, `objects`, `proof`, `summary`, or evidence payloads.

&nbsp; - Mitigation: the verifier treats all `objects` and all proof nodes as adversarial data, and

&nbsp;   accepts only after rule checks pass.



\- \*\*Replay / context confusion\*\*: using a certificate as if it corresponded to a different input.

&nbsp; - Mitigation: the verifier recomputes `input.hash` over the normative `input\_v1` scope.



\- \*\*Reference corruption\*\*:

&nbsp; - dangling `ObjectRef` to non-existent objects,

&nbsp; - dangling `premises` ids,

&nbsp; - `$input` misuse.

&nbsp; - Mitigation: reference integrity checks and reserved identifier policy.



\- \*\*Type confusion\*\*: a rule expecting `PolyQQ` is fed an `IntZ`, etc.

&nbsp; - Mitigation: rule-level object kind checks + fact-catalog typing checks.



\- \*\*Unknown-rule bypass\*\*: generator attempts to “prove” a fact using an unknown rule.

&nbsp; - Mitigation: strict ruleset gating; unknown rules are rejected.



\- \*\*Forward-reference / cycle tricks\*\*: attempting to hide cyclic dependencies or require a topo-sort.

&nbsp; - Mitigation: proof ordering constraint (premises must refer only to earlier facts).



Non-goals (v3.0.0):



\- Proving the metatheory inside the verifier (the verifier checks obligations, not foundational proofs).

\- Preventing denial-of-service from adversarially large certificates (size limits are deployment policy).

\- Verifying rules outside the supported ruleset(s).



---



\## 3) Trusted computing base (TCB) (v3)



The TCB is the set of components whose correctness is assumed by the verifier.



\### 3.1 Exact integers and rationals (required)



\- Unbounded integer arithmetic and exact rationals are in the TCB.

\- Equality checks in ℚ are \*\*exact\*\*, not floating-point.



\### 3.2 Deterministic hashing (required)



\- Canonicalization: RFC 8785 / JCS-equivalent serialization for the `input\_v1` scope.

\- Hash algorithm: SHA-256.

\- The verifier MUST reject floats in the hashed scope (see §4.2).



\### 3.3 Deterministic polynomial arithmetic over ℚ\[x] (required for common rulesets)



For typical rulesets over Q, the verifier must support exact arithmetic in ℚ\[x], including:



\- addition/subtraction

\- multiplication

\- evaluation at rationals

\- scalar multiplication by rationals



Rulesets MAY require additional operations (e.g., discriminants, resolvents, translations), but those

become part of the TCB \*\*only insofar as the verifier implements the corresponding rules\*\*.



\### 3.4 Integer square root (required if `NonSquareZ` is supported via isqrt)



If a ruleset uses `zz.nonsquare.isqrt@\*`, the verifier must implement:



\- exact integer square root `isqrt(n)` and comparison `isqrt(n)^2 == n` for `n ≥ 0`.



---



\## 4) Verification pipeline (MUST)



A conforming verifier MUST implement the following pipeline in this order.



\### 4.1 JSON Schema conformance (Draft 2020-12)



Step 0: validate the whole certificate against `schemas/certificate/3.0.0.json`.



\*\*Policy\*\*:

\- If schema validation fails, the verifier MUST return `verified=false`.

\- The verifier MAY continue with best-effort diagnostics, but MUST NOT return `verified=true`.



\### 4.2 Deterministic input identity (`input.hash`)



The verifier MUST recompute `input.hash` exactly as specified:



\- `input.canonicalization = "jcs-rfc8785"`

\- `input.hash\_alg = "sha256"`

\- `input.hash\_scope = "input\_v1"`



\*\*Hash scope object (normative)\*\*:



&nbsp;   {

&nbsp;     "domain": "Q",

&nbsp;     "variable": "x",

&nbsp;     "ordering": "descending\_degree",

&nbsp;     "degree": n,

&nbsp;     "coeffs\_qq": \[a\_n, a\_{n-1}, ..., a\_0]

&nbsp;   }



Domain restriction (normative for hashing input):

\- The `input\_v1` object contains only: objects with string keys, arrays, strings, integers, booleans, and null.

\- \*\*Floats are forbidden\*\* in the hashed scope.



Reject if the recomputed digest does not match `input.hash`.



\### 4.3 Canonical rationals (input and objects)



A verifier MUST enforce \*\*strong canonicality\*\* for every rational string it consumes as part of

any rule obligation, at minimum:



\- `input.coeffs\_qq`

\- all rational strings inside any referenced objects (e.g., `PolyQQ.coeffs\_qq`, `RatQQ.value`)

\- all rational strings inside evidence payloads for rules the verifier supports



Canonical form requirements:

\- Integers: `"0"`, `"7"`, `"-3"` (no leading zeros, no whitespace).

\- Fractions: reduced `"p/q"` with:

&nbsp; - `q > 1`

&nbsp; - `gcd(|p|, q) = 1`

&nbsp; - sign carried by `p`

\- `"-0"` is forbidden.



Recommended implementation rule:

\- Parse the string to an exact rational and re-encode canonically; accept \*\*iff\*\*

&nbsp; the result equals the original string byte-for-byte.



\### 4.4 Reserved input reference `$input`



Normative meaning:

\- `{ "ref": "$input" }` refers to the top-level polynomial described by `input.\*`.



Reserved identifier constraint (normative):

\- `$input` MUST NOT appear as a key inside `objects`.



\### 4.5 Object store integrity (`objects`)



The verifier MUST enforce:



\- For every key `k` in `objects`, `objects\[k]` is a JSON object containing a non-empty string field `kind`.

\- Keys are matched \*\*exactly\*\* (byte-for-byte) when resolving references.

\- A certificate MUST be rejected if any `ObjectRef.ref != "$input"` used in any claim refers to a key absent from `objects`.



The verifier MUST enforce canonical encoding rules for any object kind it decodes for supported rules

(see `docs/spec/v3/objects.md` and ruleset tightening).



\### 4.6 Ruleset gating (`meta.ruleset\_id`)



The verifier MUST:



1\. Load the ruleset referenced by `meta.ruleset\_id`.

2\. Reject if the ruleset is unknown or unsupported.

3\. Reject if the certificate uses any predicate not present in the ruleset’s fact catalog.

4\. Reject if the certificate uses any rule id not present in the ruleset’s rule catalog.



\### 4.7 Proof ordering constraint (MUST, streaming-friendly)



`proof.facts\[]` MUST be topologically ordered:



\- Each fact node MAY ONLY reference in `premises` ids of nodes that appear \*\*strictly earlier\*\*

&nbsp; in `proof.facts\[]`.



Verifier obligations:

\- The verifier MUST reject immediately if a premise references an unknown id.

\- The verifier MUST reject immediately if a premise references an id that appears later in the array

&nbsp; (forward reference).



This rule makes cycles impossible by construction and avoids topological sorting in the verifier.



\### 4.8 Fact typing (MUST)



For each fact node:

\- The verifier MUST type-check `claim.pred` and the arity/kinds of `claim.args` against the ruleset’s fact catalog.



Typing checks include:

\- resolving each `ObjectRef`,

\- checking the referenced object’s `kind` matches the expected kind (or `$input` is treated as `PolyQQ`).



\### 4.9 Rule dispatch and strictness (MUST)



Each fact node includes `rule`. For each node, the verifier MUST:



\- Dispatch to the checker registered for that `rule` in the active ruleset implementation.

\- Reject the certificate if the rule checker fails.

\- Reject the certificate if the verifier does not implement that rule (even if the ruleset lists it).



Unknown/unsupported rules MUST be rejected. There is no “skip”.



\### 4.10 Evidence semantics (MUST)



Evidence is rule-defined computational fuel.



\- If the rule declares evidence required, the verifier MUST reject nodes with missing/ill-typed evidence.

\- Acceptance MUST NOT depend on any non-normative field (`statement`, `data`, `summary`).

\- The mathematical identity of the proved fact depends strictly on `claim.pred` and `claim.args`, not on evidence.



---



\## 5) Rule obligations (ruleset-dependent)



In v3, the verifier’s mathematical meaning is ruleset-dependent. A verifier claiming support for a

ruleset MUST implement the rule checkers for all rule ids in that ruleset.



This section defines the \*\*minimum\*\* expectations for typical rule families. Concrete step-by-step

contracts live in the ruleset’s rule documentation (one per rule id).



\### 5.1 Computational rules (recompute-and-compare)



Typical shape:

\- claim asserts a computed value (e.g., discriminant, resolvent polynomial).

\- verifier recomputes exactly and compares with the referenced object.



Verifier MUST:

\- decode inputs canonically,

\- recompute deterministically,

\- compare exact equality in the appropriate domain (ℤ or ℚ\[x]).



\### 5.2 Computational rules (verify-evidence)



Typical shape:

\- claim asserts a property (e.g., “no rational roots”, “factorization equals f”).

\- evidence provides structured data for local checking.



Verifier MUST:

\- validate evidence schema,

\- perform local checks only (no external I/O, no randomness),

\- reject on any mismatch.



\### 5.3 Theorem rules



Typical shape:

\- claim is a fixed theorem conclusion (e.g., `IsGaloisGroupS5($input)`).

\- premises provide the certified invariants required by the theorem rule.



Verifier MUST:

\- check that required premises are present,

\- check binding consistency (premises refer to the same relevant objects, typically `$input` and shared derived objects),

\- check any side conditions (e.g., degree constraints),

\- accept the fixed claim if and only if the rule contract holds.



Theorem rules MUST NOT implement global decision procedures.



---



\## 6) Meaning of `verified=true` (and what it does NOT mean)



If `verify()` returns `verified=true`, then all of the following hold:



\- the certificate is schema-conformant (v3.0.0),

\- `input.hash` matches the canonical `input\_v1` scope,

\- all consumed rationals/objects were canonical as required,

\- every `ObjectRef` and every `premises` reference was resolved correctly,

\- the proof ordering constraint was enforced (no forward references),

\- the ruleset gates passed (predicates/rules exist and are supported),

\- every fact node was verified successfully by its rule checker.



It does \*\*not\*\* mean:



\- the engine is correct,

\- the verifier is DoS-hard for arbitrarily large certificates (size limits are a deployment policy),

\- any claim holds for any polynomial other than the exact `input\_v1` polynomial.



---



\## 7) Implementation notes (non-normative)



\- Verifiers should expose a structured trace of checks (per-node pass/fail + error codes),

&nbsp; not just a boolean.

\- Generators SHOULD emit minimal objects and minimal evidence needed to support verification.

\- Tooling MAY use `proof.goals` to report results, but correctness must not depend on goals.



---



\## 8) Extending verification (rulesets and rules)



To add a new ruleset `X@k`:



1\. Define/ship:

&nbsp;  - `facts.yaml` (predicate catalog),

&nbsp;  - rule definitions (one per rule id),

&nbsp;  - fixtures: at least one `ok-\*` and one `bad-\*` per rule.

2\. Implement rule checkers in the verifier for all rule ids in the ruleset.

3\. Update documentation and CI to enforce coverage (docs + fixtures).



To add a new rule within an existing ruleset version:

\- Only do so if it cannot change acceptance behavior for existing certificates.

\- Otherwise bump the ruleset version (and/or the rule version).



---

