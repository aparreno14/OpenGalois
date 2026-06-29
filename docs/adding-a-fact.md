# Adding a Fact Predicate

This guide explains how to add a new fact predicate to an OpenGalois v3 ruleset.

A fact predicate is the symbol used in a claim:

```json
{
  "pred": "MyPredicate",
  "args": [{"ref": "$input"}]
}
```

Facts are part of the ruleset contract. Adding or changing a predicate may require a ruleset version bump.

---

## 0. Preconditions

Before adding a predicate, confirm:

1. You know which ruleset you are editing, for example `le5-core@1`.
2. You can express the intended statement as `pred(args...)`.
3. Every argument is an `ObjectRef`.
4. There is, or will be, at least one rule that can prove this predicate.
5. You know whether the change is backwards compatible.

Changing the meaning, arity, or argument kinds of an existing predicate requires a new ruleset version.

---

## 1. Design the predicate

Write down:

- **Name**: `MyPredicate`.
- **Meaning**: one unambiguous mathematical sentence.
- **Arguments**:
  - `arg0`: kind `PolyQQ`, `RatQQ`, `IntZ`, `GroupId`, etc.
  - `arg1`: kind if present.
- **Arity**: number of arguments.
- **Canonicality expectations**.
- **Examples**:
  - one valid instance;
  - one invalid instance.

Stop if an argument cannot be expressed as `$input` or a reference to `objects`.

---

## 2. Update the machine-readable catalog

For the current ruleset, update:

```text
rulesets/le5-core@1/facts.yaml
```

Example:

```yaml
predicates:
  MyPredicate:
    args: [PolyQQ, IntZ]
    doc: "Unambiguous one-line meaning."
```

Rules:

- `args` must use object kinds documented in `docs/objects.md` or in the ruleset documentation.
- Do not reuse an existing predicate name with a new meaning.

---

## 3. Update the human-readable catalog

For the current ruleset, update:

```text
docs/rulesets/le5-core@1/facts.md
```

Add a subsection containing:

- signature;
- meaning;
- typical proving rule or rules;
- special notes or constraints.

This document is part of the ruleset contract.

---

## 4. Add object kinds if needed

If the predicate uses a new object kind:

1. document the kind in `docs/objects.md` or in a ruleset-local object document;
2. define its canonical encoding;
3. update decoders and schema checks if required;
4. add tests.

Do not introduce ad hoc payloads without a canonical specification.

---

## 5. Add fixtures

Add at least one fixture that uses the new predicate. Before a proving rule exists, the fixture may be a negative fixture that fails because the rule is missing but passes structural checks.

Suggested location:

```text
fixtures/v3/le5-core@1/bad/
```

---

## 6. Versioning rule

- Adding a predicate may be compatible if no existing certificates or rules change behavior.
- Changing an existing predicate's semantics, arity, or argument kinds requires a ruleset version bump.
- If in doubt, bump the ruleset version.

---

## 7. Checklist

- [ ] `rulesets/le5-core@1/facts.yaml` contains the predicate.
- [ ] `docs/rulesets/le5-core@1/facts.md` documents it.
- [ ] Any new object kind is documented canonically.
- [ ] Fixtures exercise the predicate.
- [ ] At least one rule can prove the predicate, or there is a clear implementation plan.
