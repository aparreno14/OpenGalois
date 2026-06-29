# Rule: `galois_group.QQ.deg4.V4@2`

## 1) Rule id
`galois_group.QQ.deg4.V4@2`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly five premises:

- `Degree(f, 4)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscSquareQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `FactorizationMonicQQ(R, factors, unit)` for the same quartic resolvent `R`.

These are the same premises as in `galois_group.QQ.deg4.V4@1`, except that the resolvent family required in the `ResolventQQ` premise is now the pair-sums family

\[
p=(x_1+x_2)(x_3+x_4)
\]

instead of the pair-products family \(x_1x_2+x_3x_4\).

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `f ∈ Q[x]` be irreducible of degree 4, and let `R` be the pair-sums cubic resolvent. This rule fixes the selected resolvent family by requiring that the third argument `p` in `ResolventQQ(R,f,p)` is exactly the canonical `MPolyQQ` object representing

\[
p=(x_1+x_2)(x_3+x_4).
\]

For a monic quartic

\[
f(X)=X^4+aX^3+bX^2+cX+d,
\]

the corresponding resolvent is

\[
R_S(X)=X^3-2bX^2+(b^2+ac-4d)X+(a^2d-abc+c^2).
\]

### 5.1 Why the square-discriminant reducible-resolvent branch leads to `V4`

The quartic classification theorem says that, for an irreducible quartic, if `disc(f)` is a square in `Q` and the quartic cubic resolvent is reducible over `Q`, then the Galois group is the Klein four group `V`.

In OpenGalois this rule certifies a stronger and more explicit form of reducibility: the premise `FactorizationMonicQQ(R, factors, unit)` must show that `R` splits completely over `Q` as a product of three monic linear factors.

This is the same contract as in `V4@1`; the only change is that `R` is now the pair-sums resolvent. Since the pair-sums and pair-products coordinates satisfy `r+s=b`, their cubic resolvents are related by an affine change of variable and have the same splitting pattern over `Q`.

### 5.2 Field picture

In the Klein-four case, the three resolvent values already lie in the base field. This corresponds to the three quadratic subfields of the splitting field being visible through the three linear factors of the cubic resolvent.

```text
            Splitting field of f
           /         |         \
          /          |          \
      Q(√u1)      Q(√u2)      Q(√u3)
          \          |          /
           \         |         /
                     Q
```

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `Degree(f, 4)` bound to the same `f` as the claim.
2. Check there is a verified premise `IrreducibleQQ(f)` bound to the same `f` as the claim.
3. Check there is a verified premise `DiscSquareQQ(f)` bound to the same `f` as the claim.
4. Check there is a verified premise `ResolventQQ(R, f, p)` whose second argument is the same `f` as in the claim.
5. Check that `p` is exactly the canonical `MPolyQQ` object representing `(x1+x2)(x3+x4)`.
6. Check there is a verified premise `FactorizationMonicQQ(R, factors, unit)` for that same `R`.
7. Decode `factors` as a `PolyQQList` and `unit` as `RatQQ`.
8. Require `unit = 1`.
9. Require `factors.items` to contain exactly three factor references.
10. For each listed factor:
    - decode it as `PolyQQ`,
    - require it to be degree 1,
    - require it to be monic.
11. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
12. Require `(G.order, G.index) = (4, 2)`.
13. Accept.

This is a theorem rule: the verifier does not recompute the quartic classification from scratch. Instead, it checks the exact premises corresponding to the `V` branch, with the pair-sums resolvent family fixed by the rule version.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the same `f` or the same resolvent `R`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise does not use the canonical `p = (x1+x2)(x3+x4)`.
- `E_BAD_FACTORIZATION` — the factorization does not have the required shape (unit ≠ 1, wrong number of factors, or some factor is not monic linear).
- `E_TYPE` — invalid claim shape or object decoding failure.
- `E_GROUP_MISMATCH` — `G` is not `V4` in the `smallgroup` catalog.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.V4@2_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.V4@2_fail_001.json`
