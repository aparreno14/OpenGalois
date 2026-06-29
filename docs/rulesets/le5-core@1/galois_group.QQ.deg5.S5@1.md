# Rule: `galois_group.QQ.deg5.S5@1`

## 1) Rule id
`galois_group.QQ.deg5.S5@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

with the intended conclusion that `G` is the symmetric group `S5`.

## 3) Premises
Exactly five premises:

- `Degree(f, 5)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscNonSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `IrreducibleQQ(R)` for the same resolvent polynomial `R` occurring in the resolvent premise.

This is a **theorem-style** rule. The verifier does **not** recompute the sextic resolvent here, and it does **not** care how the `ResolventQQ` premise was obtained. Its job is only to verify that the already-certified resolvent belongs to the intended Dummit `F20` family and that the stated arithmetic hypotheses force the Galois group to be `S5`.

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

This rule is intentionally **blind** to the computational origin of `R`. In OpenGalois, that work belongs to the computational rule that certifies the premise `ResolventQQ(R,f,p)`. The present rule only consumes that premise.

### 5.1 Why the irreducibility of `f` matters

If `f` is irreducible of degree `5`, then its Galois group acts transitively on the five roots of `f`. In particular, the group is a transitive subgroup of `S5`, and its order is divisible by `5`.

That transitivity is essential: the classification branch targeted by this rule is the branch of **irreducible quintics**. Without irreducibility, the permutation action would not be transitive and the conclusion `S5` would not even be in the correct search space.

### 5.2 Why the irreducibility of the sextic resolvent excludes the solvable branch

Dummit's Theorem 1 proves the key criterion for this particular sextic resolvent:

\[
f \text{ is solvable by radicals } \iff R=f_{20} \text{ has a rational root.}
\]

Moreover, in the solvable case, Dummit proves more than mere reducibility: the sextic resolvent factors over `Q` as the product of **one linear factor and one irreducible quintic factor**.

So, for this resolvent family, the premise `IrreducibleQQ(R)` has a very strong meaning:

- if `R` were to have a rational root, it would be reducible;
- if `f` were solvable, Theorem 1 says `R` would in fact split as `1 + 5`.

Therefore, once `IrreducibleQQ(R)` is known, the solvable branch is excluded. In particular, the Galois group of `f` is **not** one of the solvable transitive subgroups `C5`, `D5`, or `F20`.

### 5.3 Why only `A5` or `S5` remain

For an irreducible quintic, once the solvable transitive branch has been excluded, the only remaining transitive possibilities are `A5` and `S5`.

Thus the role of the irreducible sextic premise is exactly analogous to the role played by the irreducible cubic resolvent in the quartic `A4/S4` branch: it cuts away the smaller transitive alternatives and leaves only the two large non-solvable possibilities.

### 5.4 Why `DiscNonSquareQQ(f)` forces `S5`

The standard discriminant criterion says that for a separable polynomial over a field of characteristic not `2`,

\[
\operatorname{Gal}(f) \subseteq A_n \iff \operatorname{disc}(f) \text{ is a square in the base field}.
\]

Here the premise `DiscNonSquareQQ(f)` asserts that the discriminant of `f` is **not** a square in `Q`. Therefore the Galois group is **not** contained in `A5`.

Since the only remaining possibilities from §5.3 were `A5` and `S5`, this forces

\[
\operatorname{Gal}(f) \cong S_5.
\]

### 5.5 OpenGalois design notes

This rule is deliberately thin:

- it does **not** recompute the resolvent;
- it does **not** inspect how `R` was obtained;
- it does **not** introduce auxiliary negative facts such as “`R` has no rational root”.

Instead, it consumes already-certified arithmetic facts (`IrreducibleQQ`, `DiscNonSquareQQ`, `ResolventQQ`) and checks that they are bound to the same objects. This is exactly the intended OpenGalois split between:

1. computational rules, which construct and certify arithmetic invariants, and
2. theorem rules, which turn those invariants into group-theoretic conclusions.

## 6) Verifier algorithm (normative)

1. Require the claim to be `GaloisGroup(f, G)`.
2. Require a verified premise `Degree(f,5)` bound to the same `f`.
3. Require a verified premise `IrreducibleQQ(f)` bound to the same `f`.
4. Require a verified premise `DiscNonSquareQQ(f)` bound to the same `f`.
5. Require a verified premise `ResolventQQ(R,f,p)` bound to the same `f`.
6. Require that `p` is exactly the canonical `MPolyQQ` object representing Dummit's `F20` resolvent family
   
   \[
   x_1^2x_2x_5 + x_1^2x_3x_4 + x_2^2x_1x_3 + x_2^2x_4x_5
   + x_3^2x_1x_5 + x_3^2x_2x_4 + x_4^2x_1x_2 + x_4^2x_3x_5
   + x_5^2x_1x_4 + x_5^2x_2x_3.
   \]
7. Require a verified premise `IrreducibleQQ(R)` for that same resolvent polynomial `R`.
8. Decode `G` canonically as `GroupId(system="smallgroup")` and require `(order,index)=(120,34)`.
9. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended `f` or `R`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise is not attached to the canonical Dummit `F20` family.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_GROUP_MISMATCH` — `G` is not `S5` in the SmallGroup catalog.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg5.S5@1_001.json` *(placeholder until the sextic irreducibility rule and full emitting pipeline are wired)*
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg5.S5@1_fail_001.json` *(placeholder)*
