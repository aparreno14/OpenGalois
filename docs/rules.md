# OpenGalois v3 Rules

This document describes what rules are and how they interact with facts in v3 certificates.

It is normative unless explicitly marked as non-normative.

---

## 1. Facts vs proved facts

A fact is a statement:

```text
pred(args...)
```

A fact node is a fact plus a justification:

- `claim`: the fact being asserted;
- `rule`: the rule id used to justify the claim;
- `premises`: ids of earlier fact nodes;
- `evidence`: optional rule-defined computational data;
- `statement` and `data`: non-normative explanation fields.

The verifier accepts a fact node only if its rule application verifies successfully.

---

## 2. Rule definition

A rule is a verifier-known, versioned checker procedure.

Conceptually:

```text
check_R(claim, premises, evidence, objects, input) -> OK | ERROR
```

A certificate does not transmit rule implementations. It only references rule ids.

The verifier rejects any rule id that is not present in the active ruleset or not implemented by the verifier.

---

## 3. Rule ids and versioning

Rule ids are stable and versioned, for example:

```text
disc.QQ.compute@1
factorization.QQ.monic@1
nonsquare.QQ.isqrt@2
galois_group.QQ.deg5.S5@1
radical_roots.QQ.deg4.ferrari.depressed_monic@2
```

If a rule's acceptance behavior changes in a way that could change accept/reject outcomes, the rule version must be bumped.

---

## 4. Rule interface

Each rule specifies:

1. **Claim pattern**: predicate and argument kinds it can prove.
2. **Premise patterns**: required premises and binding constraints.
3. **Evidence schema**: whether evidence is required, and its shape.
4. **Verifier obligations**: exact deterministic checks.
5. **Failure codes**: stable diagnostic labels.

These specifications must be precise enough for independent verifier implementations.

---

## 5. Evidence

Evidence is computational fuel.

- Evidence does not change the mathematical identity of the claim.
- Evidence may vary while proving the same claim.
- If a rule requires evidence, missing or ill-typed evidence causes rejection.
- Evidence must not introduce nondeterminism.

---

## 6. Premises and proof order

`proof.facts` must be topologically ordered.

Every premise id of a fact node must refer to a fact node that appears strictly earlier in the array.

The verifier rejects:

- unknown premise ids;
- forward references;
- duplicated fact ids.

---

## 7. Computational rules

Computational rules verify a claim by local exact computation.

Examples:

- `disc.QQ.compute@1`: recompute a discriminant.
- `factorization.QQ.monic@1`: multiply factors and compare.
- `sqrt.QQ.check@1`: verify a rational square root.
- `nonsquare.QQ.isqrt@2`: prove a rational is not a square.

A computational rule must define:

- decoding requirements;
- exact operations;
- exact equality notion;
- evidence requirements, if any.

---

## 8. Theorem rules

Theorem rules justify a fixed mathematical conclusion by checking premises and side conditions.

Examples:

- `galois_group.QQ.deg4.S4@2`;
- `galois_group.QQ.deg5.F20@1`;
- `solvable_by_radicals.QQ.from_galois_group@1`.

A theorem rule must not run an unspecified global decision procedure. It only checks that the required certified premises are present and bound correctly.

---

## 9. Rule documentation

Every rule in a public ruleset should have a document under:

```text
docs/rulesets/<ruleset_id>/<rule_id>.md
```

For `le5-core@1`, this means:

```text
docs/rulesets/le5-core@1/
```

Each rule document should include:

- rule id;
- claim;
- premises;
- evidence;
- theoretical justification where relevant;
- verifier algorithm;
- failure codes;
- fixtures.
