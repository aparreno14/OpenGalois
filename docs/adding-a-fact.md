# Adding a Fact (Predicate) — Developer Guide (v3)

This guide explains how to add a new **Fact predicate** to an OpenGalois v3 ruleset.
It is prescriptive and intended to be followed step-by-step.

A "fact" means a predicate symbol used in `FactNode.claim`:
- `claim = { pred: "MyPredicate", args: [...] }`

Facts are part of the **ruleset contract**. Adding or changing a fact can change semantics and may
require a ruleset version bump.

---

## 0) Preconditions (STOP if not true)

Before adding a new predicate, confirm:

1. You know which ruleset you are editing (e.g. `quintic@1`).
2. You can express the intended statement as `pred(args...)` where each arg is an `ObjectRef`.
3. There is (or will be) at least one **rule** that can prove this fact.
4. You understand whether this is a **backwards compatible** addition:
   - Adding a *new* predicate is usually compatible **only if** existing certificates do not depend
     on it and existing rules are unchanged.
   - If you are changing an existing predicate’s meaning/typing/arity, you MUST bump the ruleset version.

---

## 1) Design the predicate (paper step)

Write the predicate in this template:

- **Name**: `MyPredicate`
- **Meaning** (math): one sentence, unambiguous
- **Arguments**:
  - `arg0`: kind `PolyQQ` / `IntZ` / `RatQQ` / `PolyQQList` / ...
  - `arg1`: kind ...
- **Arity**: N
- **Canonicality expectations**:
  - which object kinds must be canonical (usually all)
- **Examples**:
  - 1 valid instance
  - 1 invalid instance (wrong kind or arity)

STOP if any argument cannot be a reference to `$input` or `objects[...]`.

---

## 2) Update the machine-readable catalog (`spec/facts.yaml` or ruleset facts.yaml)

Open `spec/facts.yaml` (or `rulesets/<ruleset_id>/facts.yaml` if you keep it ruleset-local).

Add an entry under `predicates:`.

Example:

```yaml
predicates:
  MyPredicate:
    args: [PolyQQ, IntZ]
    doc: "Unambiguous one-line meaning here."
```

Rules:

* `args` MUST list kinds defined in `docs/spec/v3/objects.md` (or the ruleset’s extended kinds).
* Do not reuse an existing predicate name with a new meaning.

---

## 3) Update the human-readable catalog (`docs/spec/v3/facts.md`)

Add a new subsection documenting:

* Signature: `MyPredicate(f: PolyQQ, n: IntZ)`
* Meaning: exact statement
* Intended proving rules (list rule ids you will implement)
* Any special notes (degree constraints, invariants, etc.)

This doc is normative: write it like a spec, not like a tutorial.

---

## 4) Add or confirm object kinds (if needed)

If your predicate references a new object kind (not already in `objects.md`), STOP and:

1. Add the new kind to `docs/spec/v3/objects.md` with canonical encoding rules.
2. Update any schemas or parsers needed by the verifier for that kind.

Do not introduce "ad hoc payloads" without specifying canonical form.

---

## 5) Add fixtures for typing (recommended)

Even before implementing a rule, add at least one fixture that includes a node with the new predicate
and fails verification (because the rule is missing), but passes schema + type-check.

This ensures:

* schema accepts the new predicate usage,
* fact typing works as expected.

Suggested fixture:

* `fixtures/v3/<ruleset_id>/bad/missing_rule_for_new_fact_001.json`

---

## 6) Versioning rule (IMPORTANT)

* Adding a new predicate MAY require bumping `ruleset_id` if it changes the behavior of existing rules
  or the meaning of previously valid certificates.
* If in doubt: bump the ruleset version.

---

## 7) Final checklist

You are done when:

* [ ] `spec/facts.yaml` contains the new predicate with correct arg kinds.
* [ ] `docs/spec/v3/facts.md` documents the predicate meaning and signature.
* [ ] Any new object kinds are documented canonically in `objects.md`.
* [ ] At least one fixture exists exercising the new predicate structure.
* [ ] You have a plan to implement at least one proving rule (next guide).

---
