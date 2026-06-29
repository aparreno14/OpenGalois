# Rule: `galois_group.QQ.deg4.A4@2`

## 1) Rule id
`galois_group.QQ.deg4.A4@2`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly five premises:

- `Degree(f, 4)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `IrreducibleQQ(R)` for the same quartic resolvent `R` occurring in the resolvent premise.

These are the same premises as in `galois_group.QQ.deg4.A4@1`, except that the resolvent family required in the `ResolventQQ` premise is now the pair-sums family

\[
p=(x_1+x_2)(x_3+x_4)
\]

instead of the pair-products family \(x_1x_2+x_3x_4\).

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `f ∈ Q[x]` be irreducible of degree 4, and let `R` be the quartic cubic resolvent attached to the pair-sums family. This rule fixes that family by requiring that the third argument `p` in the premise `ResolventQQ(R,f,p)` is exactly the canonical `MPolyQQ` object representing

\[
p=(x_1+x_2)(x_3+x_4).
\]

For a monic quartic

\[
f(X)=X^4+aX^3+bX^2+cX+d,
\]

the corresponding specialized cubic resolvent is

\[
R_S(X)=X^3-2bX^2+(b^2+ac-4d)X+(a^2d-abc+c^2).
\]

### 5.1 Why only `A4` or `S4` remain

Since `f` is irreducible of degree 4, its Galois group acts transitively on the four roots of `f`. Therefore `Gal(f)` is a transitive subgroup of `S4`, and its order is divisible by 4.

The pair-sums cubic resolvent has the same orbit size as the pair-products cubic resolvent: its stabilizer in `S4` has order 8, so the orbit has size 3. If this cubic resolvent is irreducible over `Q`, adjoining one of its roots yields a cubic subextension inside the splitting field of `f`. Therefore `|Gal(f)|` is also divisible by 3.

Among the transitive subgroups of `S4`, the only possibilities whose order is divisible by both 4 and 3 are:

- `A4` (order 12),
- `S4` (order 24).

So quartic irreducibility plus irreducibility of the selected cubic resolvent reduce the problem to distinguishing `A4` from `S4`.

### 5.2 Discriminant criterion

By the discriminant criterion, for a separable polynomial over a field of characteristic not 2,

\[
Gal(f) \subseteq A_n \iff disc(f) 	ext{ is a square in the base field.}
\]

Here the premise `DiscSquareQQ(f)` asserts that the discriminant of `f` is a square in `Q`. Therefore the discriminant branch forces the conclusion

\[
Gal(f) \cong A_4.
\]

### 5.3 Relation with the legacy pair-products coordinate

If

\[
r=x_1x_2+x_3x_4,\qquad s=(x_1+x_2)(x_3+x_4),
\]

then, for a monic quartic with coefficient `b` of `X^2`,

\[
r+s=b.
\]

Thus the pair-sums resolvent is an affine reparametrization of the legacy pair-products resolvent. The subgroup information is the same, but version `@2` records the pair-sums coordinate explicitly because this is the coordinate used by the Ferrari radical rule.

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `Degree(f, 4)` bound to the same `f` as the claim.
2. Check there is a verified premise `IrreducibleQQ(f)` bound to the same `f` as the claim.
3. Check there is a verified premise `DiscSquareQQ(f)` bound to the same `f` as the claim.
4. Check there is a verified premise `ResolventQQ(R, f, p)` whose second argument is the same `f` as in the claim.
5. Check that `p` is exactly the canonical `MPolyQQ` object representing `(x1+x2)(x3+x4)`.
6. Check there is a verified premise `IrreducibleQQ(R)` for that same `R`.
7. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
8. Require `(G.order, G.index) = (12, 3)`.
9. Accept.

This is a theorem rule: the verifier does not recompute the classification argument from scratch. Instead, it checks the precise premises corresponding to the irreducible-resolvent quartic branch, with the pair-sums resolvent family fixed by the rule version.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the same `f`, or the resolvent irreducibility premise does not bind to the same `R`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise does not use the canonical `p = (x1+x2)(x3+x4)`.
- `E_TYPE` — invalid claim shape or cannot decode `G`.
- `E_GROUP_MISMATCH` — `G` is not `A4` in the `smallgroup` catalog.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.A4@2_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.A4@2_fail_001.json`
