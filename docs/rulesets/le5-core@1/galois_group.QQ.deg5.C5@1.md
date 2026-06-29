# Rule: `galois_group.QQ.deg5.C5@1`

## 1) Rule id
`galois_group.QQ.deg5.C5@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

with the intended conclusion that `G` is the cyclic transitive subgroup `C5`.

## 3) Premises
The rule consumes the certified square-discriminant solvable quintic branch:

- `Degree(f, 5)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `Discriminant(f, D)` with the same `f` as in the claim.
- `SqrtQQ(D, A)` for that same discriminant object `D`.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `FactorizationMonicQQ(R, factors, unit)` for that same resolvent polynomial `R`.
- `Degree(l, 1)` where `l` must occur among the factor references listed in `factors.items`.
- `Discriminant(q+, D+)` and `Discriminant(q-, D-)`, where `q+` and `q-` are the two Dummit quadratics of equation (7), in either order.
- `IsSquareQQ(D+)` and `IsSquareQQ(D-)`.

This is a **theorem-style** rule. It is the cyclic companion to `galois_group.QQ.deg5.D5@1`: both rules consume the same certified branch data and differ only in the final squarehood gates for the two Dummit quadratic discriminants.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(X) \in \mathbf{Q}[X]
\]

be an irreducible depressed monic quintic, and let `R` be Dummit's sextic resolvent in the `F20` family.

### 5.1 Solvable branch and fixed square-root witness

The premises `FactorizationMonicQQ(R, factors, unit)` and `Degree(l,1)` witness that the Dummit sextic has a rational root. The rule extracts that rational root `theta` from `l`.

The premise `SqrtQQ(D,A)` fixes the square-root witness needed to write Dummit's two rational quadratics:

\[
q_+(x)=x^2+(T_1+T_2A)x+(T_3+T_4A),
\]

\[
q_-(x)=x^2+(T_1-T_2A)x+(T_3-T_4A).
\]

Changing `A` to `-A` only interchanges these two quadratics, so the verifier checks them as an unordered pair.

### 5.2 Why both quadratics are required

Once the sextic has a rational root and the discriminant of `f` is a square in `Q`, the only remaining transitive possibilities are `D5` and `C5`.

Dummit's quadratic criterion is a criterion on the two quadratics from equation (7), not on just one selected quadratic. In the cyclic case all relevant Lagrange coefficients lie in `Q`, so both quadratics split over `Q`.

Therefore the cyclic gate is:

- both `D+` and `D-` are squares in `Q`.

This avoids the degenerate mixed case in which one quadratic becomes a repeated linear factor while the other remains irreducible. Such a mixed case is still dihedral, not cyclic.

## 6) Verifier algorithm (normative)

1. Require the claim to be `GaloisGroup(f, G)`.
2. Require verified premises `Degree(f,5)` and `IrreducibleQQ(f)` bound to the same `f`.
3. Require a verified premise `Discriminant(f,D)` bound to the same `f`.
4. Require a verified premise `SqrtQQ(D,A)` for that same discriminant object `D`.
5. Require a verified premise `ResolventQQ(R,f,p)` bound to the same `f`.
6. Require that `p` is exactly the canonical `MPolyQQ` object for Dummit's `F20` sextic-resolvent family.
7. Require a verified premise `FactorizationMonicQQ(R,factors,unit)` for that same resolvent `R`.
8. Require a verified premise `Degree(l,1)` and check that the factor reference `l` occurs in `factors.items`.
9. Decode `l` as a linear polynomial over `Q` and extract its rational root `theta`.
10. Decode `f` in descending coefficients and require that it has Dummit's depressed monic quintic shape

    \[
    x^5 + p x^3 + q x^2 + r x + s.
    \]

11. Use the shared Dummit appendix module together with `(p,q,r,s,theta,D,A)` to recompute `q+` and `q-` exactly.
12. Recompute `D+ = disc(q+)` and `D- = disc(q-)` exactly over `Q`.
13. Require verified `Discriminant` premises for those two exact quadratics and discriminants, allowing either order.
14. Require verified premises `IsSquareQQ(D+)` and `IsSquareQQ(D-)`.
15. Decode `G` canonically as `GroupId(system="smallgroup")` and require `(order,index)=(5,1)`.
16. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING`
- `E_PREMISE_BINDING`
- `E_BAD_RESOLVENT_FAMILY`
- `E_SIDE_CONDITION`
- `E_DUMMIT_QUADRATICS_MISMATCH`
- `E_DUMMIT_D_MISMATCH`
- `E_TYPE`
- `E_GROUP_MISMATCH`
