# OpenGalois v3 Rulesets

This document specifies the structure and semantics of rulesets.
It is normative unless explicitly marked as non-normative.

## 1. Purpose of a ruleset

A **ruleset** is a versioned bundle that defines:

- which facts (predicates) are allowed and their typing,
- which rules are allowed and how to verify them,
- any auxiliary assets needed by those rules.

The active ruleset is selected by `meta.ruleset_id` in the certificate.
The verifier MUST reject certificates referencing unknown rulesets.

Rulesets are part of the trusted computing base (TCB).

---

## 2. Ruleset identifiers and versioning

A ruleset id is a stable, versioned identifier, e.g.:

- `quintic@1`

Rulesets MUST be versioned.
If any change to the ruleset could change acceptance behavior for some certificates, the ruleset version MUST be bumped.

Typical reasons to bump the ruleset version:
- adding/removing predicates in the fact catalog,
- changing object canonicalization requirements,
- changing rule checker behavior,
- changing theorem rules’ premise requirements.

---

## 3. Ruleset contents (normative)

A ruleset MUST include:

1. **Fact catalog**
   - Machine-readable mapping from predicate symbols to argument kinds.
   - Example location: `spec/facts.yaml` (or `rulesets/<id>/facts.yaml`).

2. **Rule catalog**
   - A list of rule definitions with stable ids and verification contracts.
   - Example location: `rulesets/<id>/rules/*.yaml`.

3. **Auxiliary assets**
   - Any data required by rule checkers (rare in the “theorem-rule” design).
   - Examples: constant polynomials or domain parameters.
   - Large global decision tables are discouraged in the core theorem-rule approach.

A ruleset SHOULD be self-contained: a verifier should not need network access or external resources.

---

## 4. Repository layout (recommended)

```text
rulesets/
  quintic@1/
    facts.yaml                 # fact catalog (optional if global spec/facts.yaml is used)
    rules/
      disc.compute@1.yaml
      zz.nonsquare.isqrt@1.yaml
      resolventF20.compute@1.yaml
      noQRoot.ratroot@1.yaml
      irreducible.QQ.deg5_recompute@1.yaml
      galois.quintic.is_S5@1.yaml
      ...
    fixtures/
      ok/
        disc_001.json
        nonsquare_001.json
        s5_001.json
      bad/
        disc_mismatch_001.json
        nonsquare_false_001.json
        s5_missing_premise_001.json
```

The exact layout is not required by the certificate format, but this structure is recommended for
auditable rulesets.

---

## 5. Verifier obligations for rulesets (normative)

A conforming verifier MUST:

1. Load the ruleset identified by `meta.ruleset_id`.
2. Enforce that every `claim.pred` is defined in the ruleset’s fact catalog.
3. Enforce that every `fact_node.rule` is defined in the ruleset’s rule catalog.
4. Type-check each claim’s arguments against the fact catalog.
5. For each rule application:

   * validate premise availability and binding constraints,
   * validate evidence presence/shape if required,
   * execute the rule’s deterministic checker.

If the verifier is configured to support multiple rulesets, it MUST treat each ruleset as a separate
semantic universe. A certificate for `quintic@1` MUST NOT be verified under `quintic@2`.

---

## 6. Ruleset fixture requirements (normative)

For each rule id included in a ruleset, the repository MUST include at minimum:

* one **passing** certificate (fixture) that uses the rule and MUST be accepted,
* one **failing** certificate (fixture) that uses the rule and MUST be rejected.

Fixtures SHOULD be small and isolate the rule being tested.

Fixtures MUST be pinned to a specific ruleset version and schema version.

---

## 7. Backwards/forwards compatibility (non-normative guidance)

* Prefer additive changes within the same ruleset version only if they cannot affect acceptance.
* For any change that may alter acceptance, bump the ruleset version.
* When evolving rules, prefer introducing new rule ids (or versions) rather than changing semantics
  of an existing id.

---
