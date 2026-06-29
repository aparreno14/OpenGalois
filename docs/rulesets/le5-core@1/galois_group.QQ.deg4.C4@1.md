# Rule: `galois_group.QQ.deg4.C4@1`

## 1) Rule id
`galois_group.QQ.deg4.C4@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly eight premises:

- `Degree(f, 4)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `Discriminant(f, Δ)` with the same `f` as in the claim.
- `DiscNonSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `FactorizationMonicQQ(R, factors, unit)` for the same quartic resolvent `R`.
- `IsSquareQQ(u1)` for the first auxiliary discriminant-times-Δ value.
- `IsSquareQQ(u2)` for the second auxiliary discriminant-times-Δ value.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(X)=X^4+aX^3+bX^2+cX+d \in \mathbf{Q}[X]
\]

be an irreducible quartic, and let \(\Delta = \operatorname{disc}(f)\).

This rule fixes Conrad's quartic cubic-resolvent family by requiring that the third
argument `p` in the premise `ResolventQQ(R,f,p)` is exactly the canonical `MPolyQQ`
object representing

\[
p=x_1x_2+x_3x_4.
\]

For a monic quartic, the corresponding cubic resolvent is

\[
R_3(X)=X^3-bX^2+(ac-4d)X-(a^2d+c^2-4bd).
\]

This is Conrad's Definition 3.1 / formula (3.7).

### 5.1 The branch reduced by Theorem 3.6 and Corollary 3.8

For an irreducible quartic over \(\mathbf{Q}\), Conrad's Table 8 says:

- if \(\Delta\) is non-square and \(R_3\) is irreducible, the group is \(S_4\),
- if \(\Delta\) is square and \(R_3\) is irreducible, the group is \(A_4\),
- if \(\Delta\) is square and \(R_3\) is reducible, the group is \(V\),
- if \(\Delta\) is non-square and \(R_3\) has a rational root \(r_0\), the group is either \(D_4\) or \(\mathbf{Z}/4\mathbf{Z}\).

Corollary 3.8 sharpens the last line: in the non-square branch, a reducible cubic resolvent has
exactly one rational root. Thus, once the verifier has:
- `DiscNonSquareQQ(f)`, and
- a factorization of `R` with exactly one monic linear factor \(X-r_0\),

the only remaining possibilities are \(D_4\) and \(C_4\) (where OpenGalois uses `C4`
for Conrad's `Z/4Z`).

### 5.2 Kappe–Warren: conceptual form

Theorem 4.1 and Remark 4.2 show that in this branch the distinction between \(D_4\) and \(C_4\)
is governed by the two quadratic polynomials

\[
X^2+aX+(b-r_0), \qquad X^2-r_0X+d.
\]

The Galois group is cyclic of order 4 if and only if **both** of these quadratics split completely
over the quadratic field \(\mathbf{Q}(\sqrt{\Delta})\).

This gives the conceptual field picture:

```text
K = Q
|
| adjoining sqrt(Δ)
v
Q(√Δ)
|
| both quadratic auxiliary polynomials split here
v
splitting field of f
```

In the cyclic case, the unique quadratic subfield of the quartic splitting field is precisely
\(\mathbf{Q}(\sqrt{\Delta})\), so both auxiliary quadratics become reducible there.

### 5.3 From splitting over \(\mathbf{Q}(\sqrt{\Delta})\) to rational square tests

Let

\[
u_1 = a^2 - 4(b-r_0), \qquad u_2 = r_0^2 - 4d.
\]

These are the discriminants of the two auxiliary quadratics above.

To say that each auxiliary quadratic splits over \(\mathbf{Q}(\sqrt{\Delta})\) is equivalent to saying
that each of \(u_1\) and \(u_2\) is a square in \(\mathbf{Q}(\sqrt{\Delta})\).

Conrad then observes that, in the relevant branch, these discriminants are either \(0\) or nonsquares
in \(\mathbf{Q}\). For such a rational number \(u\), being a square in \(\mathbf{Q}(\sqrt{\Delta})\)
is equivalent to \(u\Delta\) being a square in \(\mathbf{Q}\).

Therefore, in the non-square discriminant branch, the cyclic condition is equivalent to:

\[
(a^2-4(b-r_0))\Delta \in \mathbf{Q}^{2}
\quad\text{and}\quad
(r_0^2-4d)\Delta \in \mathbf{Q}^{2}.
\]

This is exactly Conrad's Corollary 4.3.

### 5.4 What OpenGalois certifies

OpenGalois does not introduce a separate fact for “splits over \(\mathbf{Q}(\sqrt{\Delta})\)”.
Instead, the rule is fully glass-box and certifies the two concrete rational square tests:

\[
w_1 := (a^2-4(b-r_0))\Delta,
\qquad
w_2 := (r_0^2-4d)\Delta.
\]

The premises `IsSquareQQ(u1)` and `IsSquareQQ(u2)` must bind to these exact rational values.
Thus the verifier checks not merely that “some squares” are present, but that they are the two
specific quantities appearing in Conrad's quartic cyclic criterion.

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `Degree(f, 4)` bound to the same `f` as in the claim.
2. Check there is a verified premise `IrreducibleQQ(f)` bound to the same `f`.
3. Check there is a verified premise `Discriminant(f, Δ)` bound to the same `f`.
4. Check there is a verified premise `DiscNonSquareQQ(f)` bound to the same `f`.
5. Check there is a verified premise `ResolventQQ(R, f, p)` bound to the same `f`.
6. Check that `p` is exactly the canonical `MPolyQQ` object representing `x1*x2 + x3*x4`.
7. Check there is a verified premise `FactorizationMonicQQ(R, factors, unit)` for that same `R`.
8. Require `unit = 1`.
9. Decode `factors` as `PolyQQList` and require that exactly one listed factor is monic linear.
10. If the unique linear factor is `X - r0`, extract `r0`.
11. Monicize `f` internally and write it as
    \[
    X^4+aX^3+bX^2+cX+d.
    \]
12. From the discriminant premise, decode the rational number \(\Delta\).
13. Recompute
    \[
    w_1=(a^2-4(b-r_0))\Delta,
    \qquad
    w_2=(r_0^2-4d)\Delta.
    \]
14. Check there are verified premises `IsSquareQQ(u1)` and `IsSquareQQ(u2)` whose arguments
    are exactly the `RatQQ` objects encoding `w1` and `w2`.
15. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
16. Require `(G.order, G.index) = (4, 1)`.
17. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the same `f` or the same resolvent `R`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise does not use the canonical `p = x1*x2 + x3*x4`.
- `E_BAD_FACTORIZATION` — the resolvent factorization does not have unit 1 or exactly one monic linear factor.
- `E_BAD_AUXILIARY_SQUARES` — the `IsSquareQQ` premises do not bind to the exact rational values required by Corollary 4.3.
- `E_TYPE` — invalid claim shape or object decoding failure.
- `E_GROUP_MISMATCH` — `G` is not `C4` in the `smallgroup` catalog.

## 8) Fixtures

Examples drawn from Conrad's Table 9 (the `Z/4Z` rows):

- `X^4 + 5X + 5`, with
  \[
  \Delta = 5\cdot 55^2,\qquad
  R_3(X)=(X-5)(X^2+5X+5),
  \]
  and
  \[
  4r_0\Delta = 550^2,\qquad
  (r_0^2-4d)\Delta = 275^2.
  \]

- `X^4 + 8X + 14`, with
  \[
  \Delta = 2\cdot 544^2,\qquad
  R_3(X)=(X-8)(X^2+8X+8),
  \]
  and
  \[
  4r_0\Delta = 4352^2,\qquad
  (r_0^2-4d)\Delta = 2176^2.
  \]

- `X^4 + 13X + 39`, with
  \[
  \Delta = 13\cdot 1053^2,\qquad
  R_3(X)=(X-13)(X^2+13X+13),
  \]
  and
  \[
  4r_0\Delta = 27378^2,\qquad
  (r_0^2-4d)\Delta = 13689^2.
  \]

Files:
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.C4@1_001.json`
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.C4@1_002.json`
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.C4@1_003.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.C4@1_fail_001.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.C4@1_fail_002.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.C4@1_fail_003.json`
