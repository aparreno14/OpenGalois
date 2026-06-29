# OpenGalois v3 Rules

This document specifies what a rule is, how rules interact with facts, and what a verifier MUST do
to check rule applications in a v3 certificate.
It is normative unless explicitly marked as non-normative.

## 1. Background: facts vs proved facts

A **Fact** is a statement `pred(args...)` (see `facts.md`).

A **FactNode** is a proved fact:
- `claim`: the Fact being asserted (normative)
- `rule`: the rule identifier used to justify the claim (normative)
- `premises`: ids of earlier fact nodes required by the rule (normative)
- `evidence`: rule-defined computational fuel (normative if required by the rule)
- `statement` / `data`: non-normative explanatory fields

The verifier accepts a fact node only if its referenced rule verifies successfully.

---

## 2. Definition of a rule

A **rule** is a *verifier-known*, versioned checker procedure.

Each rule `R` defines a deterministic function:

```
check_R(claim, premises_claims, evidence, objects, input) -> OK | ERROR
```

A certificate does not transmit rule implementations; it only references rule ids.
The verifier MUST reject any rule id not present in the active ruleset.

### 2.1 Rule id and versioning

A rule id MUST be stable and versioned, e.g.:

- `disc.compute@1`
- `zz.nonsquare.isqrt@1`
- `factorization.QQ.monic@1`
- `galois.quintic.is_S5@1`

If the verifier’s acceptance behavior for a rule changes in any way that could change accept/reject
outcomes for some certificates, the rule version MUST be bumped (e.g. `@1 -> @2`).

---

## 3. Rule interfaces (normative)

Rules MUST specify, as part of the active ruleset:

1. **Claim pattern**: the predicate symbol and argument kinds the rule can justify.
2. **Premise patterns**: required premises and any binding constraints (e.g., “same `f`”).
3. **Evidence schema**: whether evidence is required and, if so, its JSON shape.
4. **Verifier obligations**: deterministic steps the verifier executes.

These specifications must be sufficiently precise for independent verifier implementations.

---

## 4. Evidence semantics (normative)

Evidence is computational fuel for the verifier.

- The mathematical identity of the proved fact depends strictly on `claim.pred` and `claim.args`.
- Evidence MAY vary without changing the proved fact, as long as the verifier accepts.
- If a rule declares evidence required, the verifier MUST reject nodes with missing or ill-typed evidence.

Evidence MUST NOT be used to smuggle non-determinism into verification:
- verifiers MUST NOT perform network I/O,
- MUST NOT depend on time,
- MUST NOT depend on randomized choices.

---

## 5. Proof ordering and premises (normative)

`proof.facts[]` MUST be topologically ordered (see `overview.md`).

For each fact node:
- Every premise id MUST refer to a fact node that appears **strictly earlier** in the array.
- The verifier MUST reject forward references.

Premises are passed to the rule checker as *already-verified claims*.

---

## 6. Rule families (verification styles)

OpenGalois distinguishes two verification styles.

### 6.1 Computational rules

Computational rules verify a claim by performing local deterministic computations over objects.

Two common subcases:

1. **Recompute-and-compare**:
   - The verifier recomputes the claimed value and compares.
   - Evidence is typically not required.
   - Example: `disc.compute@1` verifies `DiscEq(f, D)`.

2. **Verify-evidence**:
   - The verifier checks the evidence with local computations.
   - Evidence is required.
   - Example: a factorization rule verifies that `f = unit * Π factors` by multiplying exactly.

A computational rule MUST define:
- the precise decoding and canonicality requirements of objects it consumes,
- the exact operations to execute,
- the equality notion used for comparisons.

### 6.2 Theorem rules

Theorem rules justify a *fixed theorem conclusion* by checking:
- that required premises are present,
- that premise bindings are consistent (e.g., the same input polynomial),
- that any side-conditions are met (e.g., degree constraints).

Theorem rules MUST NOT implement global decision procedures.
In particular, theorem rules MUST NOT:
- perform searches over a global decision tree,
- consult large classifier tables to “discover” the conclusion,
- factor polynomials as part of classification.

Example: `galois.quintic.is_S5@1` verifies the claim `IsGaloisGroupS5($input)` when provided the
required invariants as premises (e.g., irreducibility, non-square discriminant, resolvent property).

---

## 7. Error handling and determinism (normative)

A verifier MUST:
- reject a certificate upon the first rule failure (it MAY additionally report an error code),
- produce deterministic accept/reject results for a fixed certificate + ruleset.

Rules SHOULD define stable error codes to support reproducible debugging and fixtures.

---

## 8. Rule documentation requirements (normative)

For each rule in a ruleset, the project MUST provide a normative rule document or machine-readable
rule specification that includes:

- Rule id and version
- Claim pattern (predicate + argument kinds)
- Premise patterns and binding constraints
- Evidence requirements (schema)
- Verifier algorithm (step-by-step)
- Failure modes / error codes
- At least one passing fixture and one failing fixture (see `ruleset.md`)

This documentation is part of the ruleset contract and is required for third-party verifier authors.

---
