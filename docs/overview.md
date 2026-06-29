# OpenGalois v3: Objects, Facts and Rules

This document gives a conceptual overview of the OpenGalois certificate model for schema version `3.0.0`.

It is normative unless explicitly marked as non-normative.

---

## Goals

OpenGalois certificates aim to be:

1. **Proof-carrying**: correctness must not depend on the engine that produced the certificate.
2. **Glass-box**: the certificate must support an auditable derivation of the conclusions.
3. **Small trusted base**: verification is performed by exact arithmetic plus a versioned ruleset.
4. **Stable and auditable**: certificates use canonical encodings and stable rule ids.
5. **Streaming-friendly**: verification can proceed in one forward pass over `proof.facts`.

## Non-goals

- The certificate format does not prescribe how the engine discovers facts.
- The format does not require proofs to be pedagogical.
- The format is not a Lean or Coq proof object, although it is designed to be more transparent than a black-box CAS result.

---

## Trust model

- **Engine**: untrusted generator. It constructs objects and proposes fact nodes.
- **Verifier**: trusted checker. It checks canonical encodings, proof order, facts, rules, premises and evidence.
- **Ruleset**: versioned semantic contract. It defines which predicates and rules exist, and how rules are checked.

If the verifier accepts, each proved fact is accepted relative to the mathematics encoded by the active ruleset.

---

## Core entities

### Object

An object is a typed mathematical value stored in the certificate's object store.

Examples:

- a polynomial over `Q`;
- a rational number;
- a multivariate resolvent invariant;
- a factor list;
- a group identifier;
- a radical expression.

Objects are immutable once referenced and must be encoded canonically.

### ObjectRef

A reference is either:

- `"$input"`, the top-level input polynomial;
- an object-store key such as `"rat:disc"` or `"poly:resolvent"`.

### Fact

A fact is a typed proposition:

```text
pred(args...)
```

where `pred` is a predicate from the active ruleset and each argument is an object reference.

Examples for `le5-core@1`:

```text
IrreducibleQQ($input)
Discriminant($input, rat:disc)
NonSquareQQ(rat:disc)
ResolventQQ(poly:R, $input, mpoly:p)
GaloisGroup($input, group:S5)
RadicalRoots($input, rlist:roots)
```

Facts are statements. They are not trusted until justified by a verified rule application.

### Fact node

A fact node is a fact plus a concrete justification:

- `claim`: the fact being asserted;
- `rule`: the rule id used to justify it;
- `premises`: ids of earlier fact nodes used by the rule;
- `evidence`: optional rule-defined data;
- `statement` and `data`: optional non-normative annotations.

A certificate is a sequence of fact nodes forming a directed acyclic derivation graph.

---

## Evidence

Evidence is computational fuel for the rule checker.

The mathematical identity of a proved fact depends on:

- `claim.pred`;
- `claim.args`.

Different evidence values may prove the same claim, provided the verifier accepts the rule application.

Evidence must not introduce non-determinism. A verifier must not use network access, time, or randomness to verify a certificate.

---

## Rules

A rule is a verifier-known, versioned checker procedure.

Conceptually:

```text
check(rule_id, claim, premises, evidence, objects, input) -> OK | ERROR
```

Rules are not transmitted by the certificate. The certificate only references `rule_id`. The verifier rejects any rule id not supported by the active ruleset.

Rules commonly fall into two categories:

1. **Computational rules**: the verifier recomputes or locally checks a property. Examples: discriminant computation, factorization verification, square tests.
2. **Theorem rules**: the verifier checks required premises and binding constraints, then accepts a fixed mathematical conclusion. Examples: group-classification rules once the required invariants are verified.

---

## Ruleset

A ruleset is a versioned bundle defining:

- the fact catalog;
- the rule catalog;
- object-kind constraints beyond the core schema;
- verifier obligations for each rule.

The current core ruleset is:

```text
le5-core@1
```

The certificate declares a `ruleset_id`, and the verifier enforces that only facts and rules from that ruleset are used.

---

## Normative vs non-normative fields

A certificate is accepted or rejected solely from normative fields:

- `input`;
- `objects`;
- `proof.facts`;
- rule-defined evidence;
- the declared `ruleset_id`.

Non-normative fields do not affect acceptance:

- `summary`;
- `statement`;
- `data`;
- rendered explanations;
- UI metadata.

---

## Proof ordering

`proof.facts` must be topologically ordered.

A fact node may only reference in its premises fact ids that occur strictly earlier in the array.

This guarantees:

- no cycles;
- no need for a topological sort in the verifier;
- reproducible single-pass verification.

---

## Example: a typical S5 quintic outline

A typical irreducible quintic `S5` proof may contain facts like:

```text
F1: Degree($input, int:5)
F2: IrreducibleQQ($input)
F3: Discriminant($input, rat:D)
F4: DiscNonSquareQQ($input)
F5: ResolventQQ(poly:R, $input, mpoly:p_dummit)
F6: IrreducibleQQ(poly:R)
F7: GaloisGroup($input, group:S5)
```

The final group rule checks that the relevant premises are present and correctly bound to the same input polynomial and resolvent objects.

---

## What "glass-box" means operationally

Given the fact sequence, an explanation tool can:

- select the premise-closed subgraph for a target fact;
- render the relevant mathematical objects;
- narrate the proof in human-readable form;
- keep the certificate as the source of truth.

Explanation is derived; it is not trusted input.
