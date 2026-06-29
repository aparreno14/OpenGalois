# Adding a Rule — Developer Guide (v3)

This guide explains how to add a new **rule** to an OpenGalois v3 ruleset.
A rule is a versioned verifier procedure referenced by `FactNode.rule`.

This guide is prescriptive: follow the steps in order.

---

## 0) Preconditions (STOP if not true)

Before adding a rule, confirm:

1. The predicate you want to prove already exists in the active fact catalog (`spec/facts.yaml`).
2. The proof ordering constraint will be respected:
   - any `premises` used by your rule will refer only to earlier nodes in `proof.facts[]`.
3. You can specify the verifier’s checks as a deterministic procedure:
   - no network I/O,
   - no time dependence,
   - no randomness.

If any of these are not true, STOP.

---

## 1) Specify the rule contract (paper step)

Write the rule spec in this template:

- **Rule id**: `my.rule.name@1`
- **Ruleset**: `quintic@1` (or your target ruleset)
- **Claim proved**:
  - predicate + argument kinds (from fact catalog)
- **Premises required**:
  - list of predicate patterns and binding constraints (“same f”, “same D”, etc.)
- **Evidence**:
  - required fields and their types, OR `none`
- **Verification mode**:
  - `trivial` (maths axioms/definitions)
  - `recompute` (verifier recomputes and compares), or
  - `verify_evidence` (verifier checks evidence), or
  - `theorem` (premise/binding checks only, fixed conclusion)
- **Verifier algorithm**:
  - step-by-step, exact operations, exact equality checks
- **Failure modes**:
  - list stable error codes and what triggers them
- **Complexity note**:
  - expected runtime bounds (so verifier authors know what they are agreeing to)

STOP if you cannot write an unambiguous verifier algorithm.

---

## 2) Add the rule definition file (`rulesets/<ruleset_id>/rules/*.yaml`)

Create:

- `rulesets/<ruleset_id>/rules/<rule_id>.yaml`

Use this minimal structure (example):

```yaml
id: my.rule.name@1
ruleset: quintic@1

claim_pattern:
  pred: MyPredicate
  args: [PolyQQ, IntZ]

premise_patterns:
  - pred: SomePremise
    args: [PolyQQ]
    binds: { f: arg0 }

evidence_schema: null  # or JSON-schema-like object

check_mode: recompute  # or verify_evidence or theorem

checker:
  steps:
    - "Exact, deterministic steps here"
errors:
  - E_TYPE
  - E_MISMATCH
```

Notes:

* `claim_pattern` MUST match a predicate in the fact catalog.
* Premise `binds` are not just documentation: the verifier MUST enforce them.

---

## 3) Implement the rule in the verifier (code)

In the verifier codebase, add a checker implementation bound to `rule_id`.

The checker MUST:

1. Validate claim predicate and arity (defensive even if typed earlier).
2. Decode referenced objects canonically (`objects.md`).
3. Load and validate premises claims; enforce binding constraints.
4. Validate `evidence` according to `evidence_schema` if required.
5. Execute deterministic checks exactly as specified.
6. Return either OK or a stable error code.

### Hard rule

If the verifier does not implement the rule id, it MUST reject certificates using it.
There is no “skip rule” behavior.

---

## 4) Add fixtures (MANDATORY)

For each new rule id, add at minimum:

1. One **passing** fixture (MUST verify):

   * `fixtures/v3/<ruleset_id>/ok/<rule_id>_001.json`

2. One **failing** fixture (MUST reject):

   * `fixtures/v3/<ruleset_id>/bad/<rule_id>_fail_001.json`

The failing fixture must be “close” to the passing one but with a single intended defect.

### Examples of defects

* Claim references wrong object id
* Claim value mismatches recomputation (e.g., wrong discriminant)
* Missing required evidence field
* Wrong binding (premise refers to different `f`)
* Forward premise reference (should be rejected earlier)

---

## 5) Add rule documentation (MANDATORY)

Add a doc page for the rule:

* `docs/rules/<ruleset_id>/<rule_id>.md`

Template (copy/paste):

1. **Rule id**
2. **Claim**
3. **Premises**
4. **Evidence**
5. **Verifier algorithm** (step-by-step)
6. **Failure codes**
7. **Fixtures**

   * link to ok fixture
   * link to bad fixture

This doc is part of the ruleset contract.

(Recommended: generate these docs from the YAML rule definition; but even if generated,
ensure the result is checked into the repo or reproducible in CI.)

---

## 6) Versioning rules (IMPORTANT)

* If you change the acceptance behavior of an existing rule, you MUST bump its version:

  * `my.rule.name@1` -> `my.rule.name@2`
* If you change the ruleset in a way that affects existing certificates, bump `ruleset_id`:

  * `quintic@1` -> `quintic@2`

Never silently change semantics under the same id.

---

## 7) Final checklist

You are done when:

* [ ] Rule YAML exists under `rulesets/<ruleset_id>/rules/`.
* [ ] Verifier dispatch implements the rule id.
* [ ] At least 1 ok fixture and 1 bad fixture exist.
* [ ] Rule doc exists under `docs/rules/<ruleset_id>/`.
* [ ] CI runs verification on fixtures and passes.

---
