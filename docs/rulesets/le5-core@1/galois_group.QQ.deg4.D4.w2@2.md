# Rule: `galois_group.QQ.deg4.D4.w2@2`

## 1) Rule id
`galois_group.QQ.deg4.D4.w2@2`

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
- `NonSquareQQ(u2)` for the second auxiliary discriminant-times-Δ value.

These are the same premises as in `galois_group.QQ.deg4.D4.w2@1`, except that the resolvent family required in the `ResolventQQ` premise is now the pair-sums family

\[
p=(x_1+x_2)(x_3+x_4)
\]

instead of the pair-products family \(x_1x_2+x_3x_4\).

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(X)=X^4+aX^3+bX^2+cX+d \in \mathbf{Q}[X]
\]

be an irreducible quartic, and let \(\Delta = \operatorname{disc}(f)\).

This rule fixes the pair-sums quartic cubic-resolvent family by requiring that the third argument `p` in the premise `ResolventQQ(R,f,p)` is exactly the canonical `MPolyQQ` object representing

\[
p=(x_1+x_2)(x_3+x_4).
\]

For a monic quartic, the corresponding cubic resolvent is

\[
R_S(X)=X^3-2bX^2+(b^2+ac-4d)X+(a^2d-abc+c^2).
\]

### 5.1 The branch reduced by the quartic classification theorem

For an irreducible quartic over \(\mathbf{Q}\), the classification table says:

- if \(\Delta\) is non-square and the quartic cubic resolvent is irreducible, the group is \(S_4\),
- if \(\Delta\) is square and the quartic cubic resolvent is irreducible, the group is \(A_4\),
- if \(\Delta\) is square and the quartic cubic resolvent is reducible, the group is \(V_4\),
- if \(\Delta\) is non-square and the quartic cubic resolvent has a rational root, the group is either \(D_4\) or \(C_4\).

The last branch is the Kappe--Warren branch. In the non-square discriminant branch, a reducible cubic resolvent has exactly one rational root. Once the verifier has `DiscNonSquareQQ(f)` and a factorization of `R` with exactly one monic linear factor, the only remaining possibilities are `D4` and `C4`.

### 5.2 Pair-sums coordinate and the root used by the rule

Set

\[
r=x_1x_2+x_3x_4,
\qquad
s=(x_1+x_2)(x_3+x_4).
\]

For the monic quartic \(X^4+aX^3+bX^2+cX+d\), these satisfy

\[
r+s=b.
\]

The selected `@2` resolvent is the resolvent in the \(s\)-coordinate. Therefore, if its unique rational root is \(s_0\), the corresponding pair-products coordinate is

\[
r_0=b-s_0.
\]

### 5.3 Kappe--Warren in pair-sums coordinates

In the legacy pair-products coordinate, the auxiliary quadratics are

\[
X^2+aX+(b-r_0),
\qquad
X^2-r_0X+d.
\]

Substituting \(r_0=b-s_0\), the same two quadratics become

\[
X^2+aX+s_0,
\qquad
X^2-(b-s_0)X+d.
\]

Their discriminants are

\[
a^2-4s_0,
\qquad
(b-s_0)^2-4d.
\]

As in the Kappe--Warren criterion, over the non-square discriminant branch the cyclic case occurs exactly when both corresponding discriminant-times-\(\Delta\) values are squares in \(\mathbf{Q}\). The concrete rational values certified by OpenGalois are therefore

\[
w_1=(a^2-4s_0)\Delta,
\qquad
w_2=((b-s_0)^2-4d)\Delta.
\]

This rule certifies the dihedral case by requiring `NonSquareQQ(w2)`. Since at least one auxiliary value fails the square test, the cyclic case is excluded.

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `Degree(f, 4)` bound to the same `f` as in the claim.
2. Check there is a verified premise `IrreducibleQQ(f)` bound to the same `f`.
3. Check there is a verified premise `Discriminant(f, Δ)` bound to the same `f`.
4. Check there is a verified premise `DiscNonSquareQQ(f)` bound to the same `f`.
5. Check there is a verified premise `ResolventQQ(R, f, p)` bound to the same `f`.
6. Check that `p` is exactly the canonical `MPolyQQ` object representing `(x1+x2)(x3+x4)`.
7. Check there is a verified premise `FactorizationMonicQQ(R, factors, unit)` for that same `R`.
8. Require `unit = 1`.
9. Decode `factors` as `PolyQQList` and require that exactly one listed factor is monic linear.
10. If the unique linear factor is `X - s0`, extract `s0`.
11. Monicize `f` internally and write it as
    \[
    X^4+aX^3+bX^2+cX+d.
    \]
12. From the discriminant premise, decode the rational number \(\Delta\).
13. Recompute
    \[
    w_1=(a^2-4s_0)\Delta,
    \qquad
    w_2=((b-s_0)^2-4d)\Delta.
    \]
14. Require the `NonSquareQQ` premise to bind to the exact `RatQQ` object encoding `w2`.
15. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
16. Require `(G.order, G.index) = (8, 3)`.
17. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING`
- `E_PREMISE_BINDING`
- `E_BAD_RESOLVENT_FAMILY`
- `E_BAD_FACTORIZATION`
- `E_BAD_AUXILIARY_SQUARES`
- `E_BAD_AUXILIARY_NONSQUARE`
- `E_TYPE`
- `E_GROUP_MISMATCH`

## 8) Fixtures

Example adapted from Conrad's Table 9, now expressed in the pair-sums coordinate:

- `X^4+3X+3`, with
  \[
  \Delta = 21\cdot 15^2,
  \qquad
  R_S(X)=(X-3)(X^2+3X-3).
  \]
  The unique rational root of the pair-sums resolvent is \(s_0=3\). Since \(a=b=0\), the auxiliary values are
  \[
  w_1=-4s_0\Delta=-56700,
  \qquad
  w_2=((-s_0)^2-4d)\Delta=-14175.
  \]

Files:
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.D4.w2@2_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.D4.w2@2_fail_001.json`
