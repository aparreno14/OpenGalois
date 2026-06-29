# Rule: `galois_group.QQ.deg4.S4@1`

## 1) Rule id
`galois_group.QQ.deg4.S4@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly five premises:

- `Degree(f, 4)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscNonSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `IrreducibleQQ(R)` for the same quartic resolvent `R` occurring in the resolvent premise.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `f ∈ Q[x]` be irreducible of degree 4, and let `R` be its quartic cubic resolvent in the sense of
Definition 3.1 of Conrad's paper. This rule fixes the same quartic cubic-resolvent family by requiring
that the third argument `p` in the premise `ResolventQQ(R,f,p)` is exactly the canonical `MPolyQQ`
object representing

\[
p = x_1x_2 + x_3x_4.
\]

For a monic quartic

\[
f(X)=X^4+aX^3+bX^2+cX+d,
\]

the corresponding resolvent is

\[
R_3(X)=X^3-bX^2+(ac-4d)X-(a^2d+c^2-4bd).
\]

### 5.1 Why only `A4` or `S4` remain

Since `f` is irreducible of degree 4, its Galois group acts transitively on the four roots of `f`.
Therefore `Gal(f)` is a transitive subgroup of `S4`, and its order is divisible by 4.

Since the cubic resolvent `R` is also irreducible over `Q`, adjoining one of its roots yields a cubic
subextension inside the splitting field of `f`. Therefore `|Gal(f)|` is also divisible by 3.

Among the transitive subgroups of `S4`, the only possibilities whose order is divisible by both 4 and 3 are:

- `A4` (order 12),
- `S4` (order 24).

So the quartic irreducibility plus the irreducibility of the cubic resolvent reduce the problem to
distinguishing `A4` from `S4`.

### 5.2 Discriminant criterion

By the discriminant criterion (Theorem 1.3 in Conrad), for a separable polynomial over a field of
characteristic not 2:

\[
Gal(f) \subseteq A_n \iff disc(f) \text{ is a square in the base field.}
\]

Here the premise `DiscNonSquareQQ(f)` asserts that the discriminant of `f` is **not** a square in `Q`.
Therefore `Gal(f)` is **not** contained in `A4`.

Since the only remaining possibilities were `A4` and `S4`, it follows that:

\[
Gal(f) \cong S4.
\]

### 5.3 Field picture

The two relevant intermediate extensions are:

```text
             Splitting field of f
            /                   \\
           /                     \\
       Q(r1)                 Q(ρ)
      degree 4             degree 3
           \\                     /
            \\                   /
                     Q
```

Here:
- `r1` is any root of the quartic `f`,
- `ρ` is any root of the cubic resolvent `R`.

The existence of both a quartic and a cubic subextension forces the Galois-group order to be divisible
by both 4 and 3, leaving only `A4` and `S4`. The non-square discriminant then excludes `A4`.

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `Degree(f, 4)` bound to the same `f` as the claim.
2. Check there is a verified premise `IrreducibleQQ(f)` bound to the same `f` as the claim.
3. Check there is a verified premise `DiscNonSquareQQ(f)` bound to the same `f` as the claim.
4. Check there is a verified premise `ResolventQQ(R, f, p)` whose second argument is the same `f` as in the claim.
5. Check that `p` is exactly the canonical `MPolyQQ` object representing `x1*x2 + x3*x4`.
6. Check there is a verified premise `IrreducibleQQ(R)` for that same `R`.
7. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
8. Require `(G.order, G.index) = (24, 12)`.
9. Accept.

This is a theorem rule: the verifier does not recompute the classification argument from scratch. Instead,
it checks that the precise premises corresponding to Conrad's quartic `S4` criterion are present and
properly bound to the same quartic and the same canonical resolvent family.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the same `f`, or the resolvent irreducibility premise does not bind to the same `R`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise does not use the canonical `p = x1*x2 + x3*x4`.
- `E_TYPE` — invalid claim shape or cannot decode `G`.
- `E_GROUP_MISMATCH` — `G` is not `S4` in the `smallgroup` catalog.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.S4@1_001.json`
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.S4@1_002.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.S4@1_fail_001.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.S4@1_fail_002.json`
