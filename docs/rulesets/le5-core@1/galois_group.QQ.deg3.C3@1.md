# Rule: `galois_group.QQ.deg3.C3@1`

## 1) Rule id
`galois_group.QQ.deg3.C3@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly three premises:

- `Degree(f, 3)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscSquareQQ(f)` with the same `f` as in the claim.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `f ∈ Q[x]` be irreducible of degree 3. Then `Gal(f)` is a **transitive** subgroup of `S3` and
`|Gal(f)|` is a multiple of 3. The only transitive subgroups of `S3` with order divisible by 3 are:

- `A3 ≅ C3` (order 3),
- `S3` (order 6).

Therefore it suffices to decide whether `Gal(f) ⊆ A3`.

### 5.1 Discriminant criterion

For an irreducible polynomial `f` over a field of characteristic 0 (in particular over `Q`):

> `Gal(f) ⊆ A_n` **iff** the discriminant `Disc(f)` is a square in the base field.

In degree 3, if `Disc(f)` is a square in `Q`, then `Gal(f) ⊆ A3`, hence `Gal(f) = A3 ≅ C3`.

### 5.2 Splitting field description (cubic case)

Let `a` be a root of `f` and let `Δ = Disc(f)`.
For an irreducible cubic, the splitting field is:
\[
L = Q(a, \sqrt{Δ}).
\]

- If `\sqrt{Δ} ∈ Q`, then `L = Q(a)` and `[L:Q]=3`, so `Gal(f) ≅ C3`.
- If `\sqrt{Δ} ∉ Q`, then `[Q(\sqrt{Δ}):Q]=2` and `[Q(a):Q]=3`.
  Since 2 and 3 are coprime and `Q(a) ∩ Q(\sqrt{Δ}) = Q`, we get `[L:Q]=6`, so `Gal(f) ≅ S3`.

Field diagram (square-discriminant case):

```
        L = Q(a)            (degree 3)
        |
        |
        Q
```

## 6) Verifier algorithm (normative)

1. Require a verified premise `Degree(f, 3)` bound to the claim’s `f`.
2. Require a verified premise `IrreducibleQQ(f)` bound to the claim’s `f`.
3. Require a verified premise `DiscSquareQQ(f)` bound to the claim’s `f`.
4. Decode `G` canonically as `GroupId` with `system="smallgroup"` and require `(G.order, G.index) = (3, 1)`.
5. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — missing required premises.
- `E_PREMISE_BINDING` — premises exist but do not bind to the same `f` (or degree is not `IntZ("3")`).
- `E_TYPE` — invalid claim shape or cannot decode `f` / `G`.
- `E_GROUP_MISMATCH` — `G` is not C3 `(order=3,index=1)` in the SmallGroup catalog.

## 8) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg3.C3@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg3.C3@1_fail_001.json`
