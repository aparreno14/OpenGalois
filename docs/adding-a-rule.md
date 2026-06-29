# Adding a Rule

This guide explains how to add a new rule to an OpenGalois v3 ruleset.

A rule is a versioned verifier procedure referenced by `FactNode.rule`.

---

## 0. Preconditions

Before adding a rule, confirm:

1. The predicate you want to prove exists in the active fact catalog.
2. Premises will refer only to earlier fact nodes.
3. The verification procedure is deterministic:
   - no network I/O;
   - no time dependence;
   - no randomness.
4. You can specify exact object decoding and exact equality checks.

---

## 1. Specify the rule contract

Write the rule spec before writing code:

- **Rule id**: `my.rule.name@1`.
- **Ruleset**: for example `le5-core@1`.
- **Claim proved**: predicate and argument kinds.
- **Premises required**: predicate patterns and binding constraints.
- **Evidence**: required fields and types, or none.
- **Verification mode**:
  - recompute-and-compare;
  - verify-evidence;
  - theorem rule.
- **Verifier algorithm**: exact steps.
- **Failure modes**: stable error codes.
- **Complexity note**.

Stop if the verifier algorithm is ambiguous.

---

## 2. Add the rule definition file

For the current ruleset, create:

```text
rulesets/le5-core@1/rules/<rule_id>.yaml
```

Minimal shape:

```yaml
id: my.rule.name@1
ruleset: le5-core@1

claim_pattern:
  pred: MyPredicate
  args: [PolyQQ, IntZ]

premise_patterns:
  - pred: SomePremise
    args: [PolyQQ]
    binds: { f: arg0 }

evidence_schema: null

check_mode: recompute

checker:
  steps:
    - "Exact deterministic steps here."

errors:
  - E_TYPE
  - E_MISMATCH
```

The machine-readable rule definition should agree with the human-readable rule document.

---

## 3. Implement the checker

The checker must:

1. validate the claim predicate and arity defensively;
2. decode referenced objects canonically;
3. load already verified premises;
4. enforce binding constraints;
5. validate evidence if required;
6. execute exact deterministic checks;
7. return success or a stable error code.

If the verifier does not implement the rule id, it must reject certificates using it.

---

## 4. Add fixtures

For each new rule id, add at minimum:

```text
fixtures/v3/le5-core@1/ok/<rule_id>_001.json
fixtures/v3/le5-core@1/bad/<rule_id>_fail_001.json
```

The failing fixture should be close to the passing one and contain a single intended defect.

Examples:

- wrong object ref;
- missing premise;
- wrong binding;
- evidence mismatch;
- wrong claimed value;
- wrong group id.

---

## 5. Add rule documentation

Create:

```text
docs/rulesets/le5-core@1/<rule_id>.md
```

The document should contain:

1. rule id;
2. claim;
3. premises;
4. evidence;
5. theoretical justification if relevant;
6. verifier algorithm;
7. failure codes;
8. fixture references.

---

## 6. Versioning

If a rule's acceptance behavior changes, bump the rule version:

```text
my.rule.name@1 -> my.rule.name@2
```

If the ruleset changes in a way that can affect existing certificates, bump the ruleset version.

Never silently change semantics under the same id.

---

## 7. Checklist

- [ ] Rule YAML exists.
- [ ] Verifier implements the rule id.
- [ ] OK and BAD fixtures exist.
- [ ] Rule documentation exists.
- [ ] Tests cover the rule.
- [ ] The ruleset catalog includes the rule.
