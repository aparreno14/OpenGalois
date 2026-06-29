# Rule: `galois_group.QQ.deg5.F20@1`

## 1) Rule id
`galois_group.QQ.deg5.F20@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

with the intended conclusion that `G` is the Frobenius group `F20`.

## 3) Premises
Exactly six premises:

- `Degree(f, 5)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscNonSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `FactorizationMonicQQ(R, factors, unit)` for the same sextic resolvent polynomial `R` occurring in the resolvent premise.
- `Degree(l, 1)` for some factor reference `l` that must occur among the factors listed in `factors`.

This is a **theorem-style** rule. The verifier does **not** recompute the sextic resolvent here, and it does **not** care how the `ResolventQQ` premise was obtained. Its job is only to verify that the already-certified resolvent belongs to the intended Dummit `F20` family and that the supplied factorization contains a specifically certified linear factor.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(X) \in \mathbf{Q}[X]
\]

be an irreducible polynomial of degree `5`, and let `R` be the associated sextic resolvent in Dummit's `F20` family, i.e. the family obtained from the stabilizer in `S5` of

\[
p = x_1^2x_2x_5 + x_1^2x_3x_4 + x_2^2x_1x_3 + x_2^2x_4x_5
  + x_3^2x_1x_5 + x_3^2x_2x_4 + x_4^2x_1x_2 + x_4^2x_3x_5
  + x_5^2x_1x_4 + x_5^2x_2x_3.
\]

This rule is intentionally **blind** to the computational origin of `R`. In OpenGalois, that work belongs to the computational rule that certifies the premise `ResolventQQ(R,f,p)`. The present rule only consumes that premise and a certified factorization of `R`.

### 5.1 Why the irreducibility of `f` matters

If `f` is irreducible of degree `5`, then its Galois group acts transitively on the five roots of `f`. In particular, the group is a transitive subgroup of `S5`, and its order is divisible by `5`.

That transitivity is essential: the classification branch targeted by this rule is the branch of **irreducible quintics**. Without irreducibility, the permutation action would not be transitive and the conclusion `F20` would not even be in the correct search space.

### 5.2 Why the rule asks for `Degree(l,1)`

Dummit's Theorem 1 proves the key criterion for this sextic resolvent:

\[
f \text{ is solvable by radicals } \iff R=f_{20} \text{ has a rational root.}
\]

Moreover, in the solvable case the sextic factors over `Q` as the product of **one linear factor and one irreducible quintic factor**.

In OpenGalois, the theorem rule should not rediscover this structural information by re-inspecting coefficients more than necessary. Instead, it consumes two already-certified premises:

- `FactorizationMonicQQ(R, factors, unit)`, which certifies the factorization structure of `R`, and
- `Degree(l,1)`, which certifies that a specific factor reference `l` is linear.

The verifier then only checks that the very same `l` actually occurs among the factors listed in `factors`. This is more faithful to the OpenGalois style than having the theorem rule itself scan the factor list and infer lineality on its own.

### 5.3 Why `DiscNonSquareQQ(f)` forces `F20` inside the solvable branch

For an irreducible solvable quintic over `Q`, the only transitive possibilities are:

- `C5`,
- `D5`,
- `F20`.

Dummit's Theorem 2 then distinguishes these three solvable cases. Part (a) states that the Galois group is the Frobenius group of order `20` **if and only if** the discriminant is **not** a square in `Q`. Parts (b) and (c) handle the square-discriminant cases `D5` and `C5`.

Therefore, once the resolvent factorization has certified entry into the solvable branch, the additional premise `DiscNonSquareQQ(f)` forces

\[
\operatorname{Gal}(f) \cong F_{20}.
\]

### 5.4 OpenGalois design notes

This rule is deliberately thin:

- it does **not** recompute the resolvent;
- it does **not** inspect how `R` was obtained;
- it does **not** introduce a special predicate for rational roots;
- it does **not** infer “linear factor” from raw coefficients inside the theorem rule.

Instead, it consumes already-certified arithmetic facts (`IrreducibleQQ`, `DiscNonSquareQQ`, `ResolventQQ`, `FactorizationMonicQQ`, `Degree`) and checks only that they are bound to the same mathematical objects. This is exactly the intended OpenGalois split between:

1. computational rules, which construct and certify arithmetic invariants, and
2. theorem rules, which turn those invariants into group-theoretic conclusions.

## 6) Verifier algorithm (normative)

1. Require the claim to be `GaloisGroup(f, G)`.
2. Require a verified premise `Degree(f,5)` bound to the same `f`.
3. Require a verified premise `IrreducibleQQ(f)` bound to the same `f`.
4. Require a verified premise `DiscNonSquareQQ(f)` bound to the same `f`.
5. Require a verified premise `ResolventQQ(R,f,p)` bound to the same `f`.
6. Require that `p` is exactly the canonical `MPolyQQ` object representing Dummit's `F20` sextic-resolvent family.
7. Require a verified premise `FactorizationMonicQQ(R,factors,unit)` for that same resolvent polynomial `R`.
8. Require a verified premise `Degree(l,1)`.
9. Decode `factors` as a `PolyQQList` and require that the factor reference `l` occurs among `factors.items`.
10. Decode `G` canonically as `GroupId(system="smallgroup")` and require `(order,index)=(20,3)`.
11. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended `f`, `R`, or listed factor `l`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise is not attached to the canonical Dummit `F20` family.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_GROUP_MISMATCH` — `G` is not `F20` in the SmallGroup catalog.
