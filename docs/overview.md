# OpenGalois v3: Facts + Objects + Rules (Overview)

This document defines the conceptual model for OpenGalois certificates in schema v3.0.0.
It is normative unless explicitly marked as non-normative.

## Goals

OpenGalois certificates aim to be:

1. **Proof-carrying**: correctness must not depend on the engine (generator) being correct.
2. **Glass-box**: the certificate must support an explainable derivation of conclusions.
3. **Small trusted base**: verification is performed by a small, deterministic verifier plus a versioned ruleset.
4. **Stable & auditable**: certificates are deterministic under canonical encodings and ruleset versioning.
5. **Streaming-friendly verification**: verification can be implemented as a single forward pass over the proof array.

## Non-goals

- This spec does not prescribe the engine algorithms used to produce evidence.
- This spec does not require proofs to be "pretty". Certificates can be minimal; pedagogy is optional.
- This spec does not attempt to encode full formal proofs in a proof assistant format (Lean/Coq). It is compatible with exporting to such systems.

---

## Trust model

- **Engine (untrusted)**: constructs `objects` and proposes proved facts in `proof.facts[]`.
- **Verifier (trusted)**: checks the certificate deterministically using:
  - canonical object decoding rules,
  - schema constraints,
  - a versioned **ruleset** of allowed rules and their verification procedures (including any auxiliary assets shipped with the ruleset).

If the verifier accepts, each proved fact is correct relative to the mathematics encoded by the active ruleset.

---

## Core entities

### Object

An **object** is a typed mathematical value stored in the certificate's object store.

- Examples: a polynomial over Q, an integer, a list of polynomials.
- Objects MUST be encoded in a canonical representation specified by the spec and/or the active ruleset.
- Objects are immutable once referenced.

### ObjectRef

A reference to either:
- `"$input"` (the input polynomial), or
- an object store key (e.g., `"int:D"`, `"poly:R_f20"`).

### Fact (Claim)

A **fact** is a typed proposition of the form:

- `pred(args...)`

where:
- `pred` is a predicate symbol defined by the ruleset’s fact catalog,
- each argument is an `ObjectRef`.

Facts are *statements*; they are not automatically trusted.

Examples (illustrative):
- `IrreducibleQQ($input)`
- `DiscEq($input, int:D)`
- `NonSquareZ(int:D)`
- `ResolventF20Eq($input, poly:R)`
- `NoQRootQQ(poly:R)`
- `IsGaloisGroupS5($input)`

### FactNode (Proved fact)

A **fact node** is a fact plus a concrete justification:

- `claim`: the fact being asserted (normative)
- `rule`: the rule identifier used to justify the claim (normative)
- `premises`: references to earlier fact nodes required by the rule (normative)
- `evidence`: optional, rule-defined data required for local checking (normative if required by the rule)
- `statement`/`data`: optional, non-normative annotations for glass-box explanation

A certificate is a sequence of fact nodes forming a derivation DAG.

### Evidence is computational fuel (normative)

The mathematical identity of a proved fact depends **only** on:

- `claim.pred` and `claim.args`

The `evidence` field is **computational fuel** for the rule checker. Different evidence values MAY prove the same claim, provided the verifier accepts.

### Rule

A **rule** is a verifier-known, versioned procedure that validates a fact node.

Formally, each rule defines a deterministic checker:
check(rule_id, claim, premises_claims, evidence, objects, input) -> OK | ERROR


Rules are not transmitted by the certificate; the certificate only references `rule_id`.
The verifier MUST reject any rule_id not present in the active ruleset.

Rules are divided into two verification styles:

1. **Computational rules**: verifier recomputes/locally checks a property.
   - Examples: `disc.compute@1`, `zz.nonsquare.isqrt@1`, `resolventF20.compute@1`, `noQRoot.ratroot@1`

2. **Theorem rules**: verifier checks that the required premises are present and consistent, then accepts a fixed theorem conclusion.
   - Example: `galois.quintic.is_S5@1` accepts `IsGaloisGroupS5($input)` when given the required invariants as premises.

Theorem rules MUST NOT perform global decision procedures; they only validate premises/bindings and then accept a fixed conclusion.

### Ruleset

A **ruleset** is a versioned bundle that defines:

- the fact catalog (allowed predicates + typing),
- the rule catalog (allowed rules + verification procedures),
- any auxiliary assets needed by rules (if any).

The certificate declares a `ruleset_id`. The verifier MUST enforce that only rules from that ruleset are used.

---

## Normative vs non-normative fields

A certificate is accepted/rejected solely based on:

- schema validity (structural)
- normative fields:
  - `input` (including hash and canonicalization constraints),
  - `objects` (as referenced by claims),
  - `proof.facts[]` (id/claim/rule/premises/evidence),
  - the declared `ruleset_id`.

Non-normative fields MUST NOT affect acceptance:

- `summary`
- `fact_node.statement`
- `fact_node.data`
- any pedagogical/transcript fields

---

## Proof ordering and streaming verification (normative)

`proof.facts[]` MUST be **topologically ordered**.

A fact node MAY ONLY reference in its `premises` the ids of fact nodes that appear **strictly earlier** in the `proof.facts[]` array.

The verifier MUST reject the certificate immediately if a forward reference is detected.

This ordering guarantees:
- the dependency graph is acyclic by construction,
- verification can be implemented as a single forward pass (streaming-friendly),
- minimal TCB (no topological sort required in the verifier).

---

## Global invariants for valid certificates

A conforming certificate MUST satisfy:

1. **Input integrity**: input hash must match the specified hash scope.
2. **Reference integrity**:
   - every `ObjectRef` must point to `$input` or an existing object store key,
   - every `premises` entry must reference an earlier fact node id.
3. **Ruleset gating**:
   - all referenced rule ids must exist in the ruleset,
   - the ruleset must define typing for all predicates used by claims.
4. **Deterministic verification**:
   - the verifier’s acceptance decision must be deterministic given certificate + ruleset.

---

## Example (informal) derivation: “IsGaloisGroupS5($input)”

A typical quintic `S5` proof (illustrative) might consist of the following proved facts:

- `F1`: `IrreducibleQQ($input)` via `irreducible.QQ.deg5_recompute@1`
- `F2`: `DiscEq($input, D)` via `disc.compute@1`
- `F3`: `NonSquareZ(D)` via `zz.nonsquare.isqrt@1`
- `F4`: `ResolventF20Eq($input, R)` via `resolventF20.compute@1`
- `F5`: `NoQRootQQ(R)` via `noQRoot.ratroot@1`
- `F6`: `IsGaloisGroupS5($input)` via `galois.quintic.is_S5@1` (premises: F1, F3, F5)

The verifier checks each node locally in sequence.

---

## What “glass-box” means operationally (non-normative)

Given the fact sequence, an explanation tool can produce:

- `why(fact_id)`: minimal prefix-subgraph of premises needed for `fact_id`
- `why_not(candidate)`: identify which verified fact excludes a candidate group
- step-by-step narration using `statement` and `data` if present, without affecting correctness

Explanation is derived; it is not trusted input.

---