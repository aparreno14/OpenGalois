# Canonicality of `RadicalExpr` and `RadicalExprList` in `le5-core@1`

## 1) Scope

This document specifies the canonicality policy for the object kinds

- `RadicalExpr`
- `RadicalExprList`

as used by the `RadicalRoots` facts and rules in `le5-core@1`.

This policy is **normative** for the ruleset.

It explains:

- what kind of canonicality is intended,
- which local simplifications are allowed,
- which transformations are intentionally **not** performed,
- and why equality of radical expressions is checked **structurally** rather than algebraically.

---

## 2) Principle

A `RadicalExpr` is not a canonical representative of an algebraic number modulo general algebraic equivalence.

Instead, it is a **canonical syntactic output** of a specific rule-local construction scheme.

Therefore:

- canonicality is **rule-relative**,
- expression equality is **structural exact equality**,
- and the verifier does **not** attempt to decide whether two different radical expressions define the same algebraic quantity.

This design is intentional.

It keeps the certificate transparent, avoids hidden symbolic manipulation inside the verifier, and avoids the mathematically difficult problem of simplifying or comparing general radical expressions.

---

## 3) Consequence for `RadicalRoots`

A fact

- `RadicalRoots(f, roots)`

asserts that `roots` is the **canonical ordered list of radical expressions produced by the specific proving rule** used for that fact.

It does **not** assert that:

- every algebraically equivalent radical form would also be accepted,
- the expressions are globally simplified,
- or the verifier can recognize arbitrary equivalent rewritings.

Each proving rule fixes its own construction scheme and therefore fixes a unique expected AST output.

---

## 4) Allowed local simplifications

The canonical AST builder may apply only a small set of **explicit local simplifications**.

These simplifications are purely structural and are intended only to remove obvious syntactic noise.

The following simplifications are allowed:

- `neg(0) -> 0`
- `neg(neg(a)) -> a`
- `add(a, 0) -> a`
- `add(0, a) -> a`
- `sub(a, 0) -> a`
- `mul(a, 0) -> 0`
- `mul(0, a) -> 0`
- `mul(a, 1) -> a`
- `mul(1, a) -> a`
- `div(a, 1) -> a`
- `root(n, 0) -> 0`
- `pow_int(0, k) -> 0` for integers `k > 0`

These are the only simplifications assumed by the canonical builder unless a rule explicitly states otherwise.

---

## 5) Simplifications that are intentionally not performed

The verifier and the canonical AST builder do **not** attempt any general algebraic simplification beyond the local rules listed above.

In particular, the following are **not** part of canonicalization:

- rewriting `sqrt(8)/2` as `sqrt(2)`,
- rationalizing denominators,
- reordering terms by commutativity,
- rewriting using associativity,
- cancelling nontrivial common factors,
- recognizing identities involving roots of unity,
- comparing different nested-radical forms,
- deciding whether two different ASTs define the same algebraic number.

Thus expressions such as `root(2, 8) / 2` may remain unchanged if they are the rule-canonical output after applying only the allowed local simplifications.

---

## 6) Why structural equality is used

General equivalence of radical expressions is not a trivial normalization problem.

Even very simple-looking nested radicals may admit non-obvious rewritings, and deciding useful canonical simplifications in full generality would significantly enlarge the trusted computational core.

For this reason, `le5-core@1` adopts the following policy:

- rules produce one fixed AST,
- the verifier reconstructs that AST deterministically,
- and acceptance is by exact structural comparison.

This keeps the semantics of the certificate clear:

- the rule explains **which expression scheme is being certified**,
- not which entire equivalence class of radical expressions is accepted.

---

## 7) Order is normative

For `RadicalExprList`, the order of the expressions is normative.

Therefore two lists containing the same expressions in a different order are different objects and are not interchangeable.

Any required ordering convention must be stated by the proving rule.

---

## 8) Responsibility split

The responsibility split is as follows.

### Object layer
The object layer checks only:

- that a `RadicalExpr` is well-formed,
- that a `RadicalExprList` is well-formed,
- and that references point to objects of the expected kinds.

### Rule layer
The rule layer determines:

- how a radical expression is constructed,
- which local simplifications are applied,
- and which ordered list is the unique canonical output for that rule.

---

## 9) Summary

In `le5-core@1`, canonicality of radical expressions means:

- **canonical for a fixed rule-specific construction**, not canonical modulo algebraic equivalence;
- **locally simplified**, but only by a short explicit list of safe rewrites;
- **structurally compared**, not algebraically normalized;
- **order-sensitive** at the level of `RadicalExprList`.

This policy is deliberate and is part of the semantic contract of `RadicalRoots` in this ruleset.
