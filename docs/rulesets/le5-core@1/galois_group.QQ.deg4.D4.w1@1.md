# Rule: `galois_group.QQ.deg4.D4.w1@1`

## 1) Rule id
`galois_group.QQ.deg4.D4.w1@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly seven premises:

- `Degree(f, 4)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `Discriminant(f, Δ)` with the same `f` as in the claim.
- `DiscNonSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `FactorizationMonicQQ(R, factors, unit)` for the same quartic resolvent `R`.
- `NonSquareQQ(u1)` for the first auxiliary discriminant-times-Δ value.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(X)=X^4+aX^3+bX^2+cX+d \in \mathbf{Q}[X]
\]

be an irreducible quartic, and let \(\Delta = \operatorname{disc}(f)\).

OpenGalois fixes Conrad's quartic cubic-resolvent family by requiring that the third
argument `p` in the premise `ResolventQQ(R,f,p)` is exactly the canonical `MPolyQQ`
object representing

\[
p=x_1x_2+x_3x_4.
\]

For a monic quartic, the corresponding cubic resolvent is

\[
R_3(X)=X^3-bX^2+(ac-4d)X-(a^2d+c^2-4bd).
\]

### 5.1 The branch reduced by Theorem 3.6 and Corollary 3.8

For an irreducible quartic over \(\mathbf{Q}\), Conrad's quartic classification says that if

- \(\Delta\) is not a square in \(\mathbf{Q}\), and
- the quartic cubic resolvent has a rational root \(r_0\),

then the only remaining possibilities are \(D_4\) and \(\mathbf{Z}/4\mathbf{Z}\) (denoted `C4`
inside OpenGalois).

Corollary 3.8 sharpens this: in the non-square discriminant branch, a reducible cubic resolvent
has exactly one rational root. Thus, once the verifier has:
- `DiscNonSquareQQ(f)`, and
- a factorization of `R` with exactly one monic linear factor \(X-r_0\),

the only remaining possibilities are `D4` and `C4`.

### 5.2 Kappe–Warren: conceptual form

Theorem 4.1 and Remark 4.2 show that in this branch the distinction between \(D_4\) and \(C_4\)
is governed by the two quadratic polynomials

\[
X^2+aX+(b-r_0), \qquad X^2-r_0X+d.
\]

The Galois group is cyclic of order 4 if and only if **both** of these quadratics split completely
over the quadratic field \(\mathbf{Q}(\sqrt{\Delta})\).

Equivalently, if at least one of them fails to split over \(\mathbf{Q}(\sqrt{\Delta})\), then the
group is dihedral of order 8.

### 5.3 From splitting over \(\mathbf{Q}(\sqrt{\Delta})\) to rational square tests

Let

\[
u_1 = a^2 - 4(b-r_0), \qquad u_2 = r_0^2 - 4d.
\]

These are the discriminants of the two auxiliary quadratics above.

Conrad's Corollary 4.3 shows that, in the relevant branch, the cyclic condition is equivalent to

\[
u_1\Delta \in \mathbf{Q}^{2}
\quad\text{and}\quad
u_2\Delta \in \mathbf{Q}^{2}.
\]

Therefore the dihedral condition is equivalent to saying that **at least one** of the two rational values

\[
w_1 := (a^2-4(b-r_0))\Delta,
\qquad
w_2 := (r_0^2-4d)\Delta
\]

is **not** a square in \(\mathbf{Q}\).

OpenGalois makes this disjunction explicit by offering two theorem rules:
- one witnessing that `w1` is non-square,
- one witnessing that `w2` is non-square.

Either witness is sufficient to certify `D4`.

### 5.4 Example from the paper

Conrad's Table 9 gives the quartic trinomial

\[
X^4+3X+3,
\]

with

\[
\Delta = 21\cdot 15^2,
\qquad
R_3(X)=(X+3)(X^2-3X-3).
\]

Thus the unique rational root of the resolvent is \(r_0=-3\). Since \(a=b=0\), the two
auxiliary values become

\[
w_1 = 4r_0\Delta = -56700,
\qquad
w_2 = (r_0^2-4d)\Delta = -14175,
\]

and both are non-squares in \(\mathbf{Q}\). Hence the Galois group is `D4`.


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
    w_1=(a^2-4(b-r_0))\Delta.
    \]
14. Check there is a verified premise `NonSquareQQ(u1)` whose argument is exactly the `RatQQ`
    object encoding `w1`.
15. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
16. Require `(G.order, G.index) = (8, 3)`.
17. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING`
- `E_PREMISE_BINDING`
- `E_BAD_RESOLVENT_FAMILY`
- `E_BAD_FACTORIZATION`
- `E_BAD_AUXILIARY_NONSQUARE`
- `E_TYPE`
- `E_GROUP_MISMATCH`

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.D4.w1@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.D4.w1@1_fail_001.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.D4.w1@1_fail_002.json`
