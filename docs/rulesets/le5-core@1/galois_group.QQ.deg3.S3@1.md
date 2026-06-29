# Rule: `galois_group.QQ.deg3.S3@1`

## 1) Rule id
`galois_group.QQ.deg3.S3@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly three premises:

- `Degree(f, 3)` with the same `f` as in the claim.
- `IrreducibleQQ(f)` with the same `f` as in the claim.
- `DiscNonSquareQQ(f)` with the same `f` as in the claim.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

For an irreducible cubic `f`, `Gal(f)` is transitive in `S3`, so its order is a multiple of 3.
Hence `Gal(f)` is either `A3 ≅ C3` or `S3`.

If the discriminant is **not** a square in `Q`, then `Gal(f)` is **not** contained in `A3`,
so the only possibility is `S3`.

Field diagram (non-square discriminant case):

```
              L = Q(a, sqrt(Δ))          (degree 6)
             /             \
            /               \
      Q(a) (deg 3)     Q(sqrt(Δ)) (deg 2)
            \               /
             \             /
                    Q
```

## 6) Verifier algorithm (normative)

1. Require a verified premise `Degree(f, 3)` bound to the claim’s `f`.
2. Require a verified premise `IrreducibleQQ(f)` bound to the claim’s `f`.
3. Require a verified premise `DiscNonSquareQQ(f)` bound to the claim’s `f`.
4. Decode `G` canonically as `GroupId` with `system="smallgroup"` and require `(G.order, G.index) = (6, 2)`.
5. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — missing required premises.
- `E_PREMISE_BINDING` — premises exist but do not bind to the same `f` (or degree is not `IntZ("3")`).
- `E_TYPE` — invalid claim shape or cannot decode `f` / `G`.
- `E_GROUP_MISMATCH` — `G` is not `S3` in the SmallGroup catalog (expected `(order=6,index=2)`).

## 8) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg3.S3@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg3.S3@1_fail_001.json`
