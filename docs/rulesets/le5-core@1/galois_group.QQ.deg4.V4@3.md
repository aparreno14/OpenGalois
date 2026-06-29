# Rule: `galois_group.QQ.deg4.V4@3`

## 1) Rule id
`galois_group.QQ.deg4.V4@3`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly seven premises:

- `Degree(f, 4)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `ResolventQQ(R, f, p)` with the same `f` as in the claim.
- `FactorizationMonicQQ(R, factors, unit)` for the same quartic resolvent `R`.
- `Degree(l1, 1)` for the first factor listed in `factors`.
- `Degree(l2, 1)` for the second factor listed in `factors`.
- `Degree(l3, 1)` for the third factor listed in `factors`.

The factor references `l1,l2,l3` are not arbitrary: they must be exactly the three references appearing in `factors.items`, in the `PolyQQList` object used by the `FactorizationMonicQQ` premise.

Unlike `galois_group.QQ.deg4.V4@2`, this rule does **not** require a `DiscSquareQQ(f)` premise. The complete splitting of the cubic resolvent already isolates the Klein-four branch among transitive subgroups of `S4`.

The required resolvent family is the pair-sums family

\[
p=(x_1+x_2)(x_3+x_4).
\]

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `f ∈ Q[x]` be irreducible of degree 4. The three roots of the cubic resolvent attached to

\[
p=(x_1+x_2)(x_3+x_4)
\]

encode the three ways of partitioning the four roots of `f` into two unordered pairs. The Galois group of `f`, viewed as a transitive subgroup of `S4`, acts on these three pairings.

If the pair-sums cubic resolvent splits completely over `Q`, then all three pairing-values are rational. Equivalently, the induced action on the set of three pairings is trivial. Among the transitive subgroups of `S4`, the kernel of this action is precisely the Klein four group `V4`. Therefore the Galois group is `V4`.

For a monic quartic

\[
f(X)=X^4+aX^3+bX^2+cX+d,
\]

the pair-sums resolvent is

\[
R_S(X)=X^3-2bX^2+(b^2+ac-4d)X+(a^2d-abc+c^2).
\]

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `Degree(f, 4)` bound to the same `f` as the claim.
2. Check there is a verified premise `IrreducibleQQ(f)` bound to the same `f` as the claim.
3. Check there is a verified premise `ResolventQQ(R, f, p)` whose second argument is the same `f` as in the claim.
4. Check that `p` is exactly the canonical `MPolyQQ` object representing `(x1+x2)(x3+x4)`.
5. Check there is a verified premise `FactorizationMonicQQ(R, factors, unit)` for that same `R`.
6. Decode `factors` as a `PolyQQList` and `unit` as `RatQQ`.
7. Require `unit = 1`.
8. Require `factors.items` to contain exactly three factor references `l1,l2,l3`.
9. For each listed factor `li`, require an explicit verified premise `Degree(li, 1)`.
10. Decode each `li` as `PolyQQ` and require it to be monic linear.
11. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
12. Require `(G.order, G.index) = (4, 2)`.
13. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the same `f`, the same resolvent `R`, or one of the listed factor references.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise does not use the canonical `p = (x1+x2)(x3+x4)`.
- `E_BAD_FACTORIZATION` — the factorization does not have the required split-linear shape.
- `E_TYPE` — invalid claim shape or object decoding failure.
- `E_GROUP_MISMATCH` — `G` is not `V4` in the `smallgroup` catalog.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg4.V4@3_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg4.V4@3_fail_001.json`
