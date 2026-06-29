# OpenGalois v3 Rulesets

This document describes the structure and semantics of OpenGalois rulesets.

A ruleset is part of the trusted computing base of a verifier.

---

## 1. Purpose

A ruleset defines:

- which fact predicates are allowed;
- the argument kinds and arities of those predicates;
- which rule ids are allowed;
- how each rule is verified;
- any ruleset-local canonicality constraints.

The active ruleset is selected by `meta.ruleset_id` in the certificate.

The current public ruleset is:

```text
le5-core@1
```

---

## 2. Versioning

Ruleset ids are stable and versioned.

If any change could alter acceptance behavior for existing certificates, the ruleset version must be bumped.

Typical reasons to bump the ruleset version:

- changing a predicate's meaning, arity, or argument kinds;
- removing a predicate;
- changing object canonicality requirements;
- changing a rule checker;
- changing theorem-rule premises;
- changing the interpretation of a group id or radical scheme.

---

## 3. Repository layout

Current layout:

```text
rulesets/
  le5-core@1/
    facts.yaml
    rules/
      disc.QQ.compute@1.yaml
      factorization.QQ.monic@1.yaml
      galois_group.QQ.deg5.S5@1.yaml
      ...

docs/
  rulesets/
    le5-core@1/
      facts.md
      disc.QQ.compute@1.md
      factorization.QQ.monic@1.md
      galois_group.QQ.deg5.S5@1.md
      ...
```

The compiled verifier ruleset lives in Python code under `src/opengalois/rulesets/`.

---

## 4. Ruleset contents

A ruleset contains:

1. **Fact catalog**
   - machine-readable predicate catalog;
   - human-readable documentation.

2. **Rule catalog**
   - machine-readable rule specs where available;
   - human-readable rule documentation;
   - verifier implementations.

3. **Fixtures**
   - at least one passing and one failing fixture per rule where practical.

4. **Auxiliary assets**
   - any deterministic data required by rule checkers.

A verifier should not require network access or external mutable state to support a ruleset.

---

## 5. Verifier obligations

For the selected ruleset, a verifier must:

1. enforce that every predicate is in the fact catalog;
2. enforce predicate arity and argument kinds;
3. enforce that every rule id is allowed and implemented;
4. verify every rule application exactly;
5. reject unknown rules and unsupported rules.

If a verifier supports multiple rulesets, it must treat each ruleset as a separate semantic universe.

A certificate for `le5-core@1` must not be silently interpreted under a different ruleset.

---

## 6. Fixture expectations

For each rule id, public fixtures should include:

- one certificate that must verify;
- one certificate that must fail for a controlled reason.

Fixtures should be small and isolate the rule being tested.

---

## 7. Compatibility guidance

- Prefer adding new rule ids instead of changing existing ones.
- Prefer additive changes only when they cannot affect existing certificate acceptance.
- When in doubt, bump the ruleset version.
