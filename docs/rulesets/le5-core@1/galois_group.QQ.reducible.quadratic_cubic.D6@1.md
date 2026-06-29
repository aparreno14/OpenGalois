# Rule: `galois_group.QQ.reducible.quadratic_cubic.D6@1`

## 1) Rule id
`galois_group.QQ.reducible.quadratic_cubic.D6@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Required premises:

- `FactorizationMonicQQ(f, factors, unit)` with the same `f` as in the claim.
- `Degree(q, 2)`.
- `IrreducibleQQ(q)`.
- `Discriminant(q, d1)`.
- `Degree(c, 3)`.
- `IrreducibleQQ(c)`.
- `Discriminant(c, d2)`.
- `DiscNonSquareQQ(c)`.
- `NonSquareQQ(w)`.

In addition, if `factors.items` contains any factor refs other than `q` and `c`, the checker requires a
verified premise `Degree(li, 1)` for each such extra **distinct** factor ref `li`.

The intended structural shape is therefore:

- exactly one distinct irreducible quadratic factor `q`,
- exactly one distinct irreducible cubic factor `c`,
- and all remaining distinct factors, if any, are linear.

This is the reducible core `[2,3] + linears` after ignoring multiplicities.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(x)=q(x)^{e_q} c(x)^{e_c}\prod_i \ell_i(x)
\]

with `e_q, e_c >= 1`, where `q` is irreducible quadratic, `c` is irreducible cubic, and all `\ell_i`
are linear. Linear factors and repeated irreducible factors do not change the splitting field, so the
classification depends only on the square-free core `q c`.

When the cubic discriminant is not a square, the cubic side is in the `S3` branch. If `d1*d2` is not a
square, the quadratic field from `q` is different from the unique quadratic subfield already present on
the cubic side, and the full Galois group is `D6`.

## 6) Verifier algorithm (normative)

1. Require a verified premise `FactorizationMonicQQ(f, factors, unit)` bound to the same `f` as in the claim.
2. Require verified premises `Degree(q,2)`, `IrreducibleQQ(q)`, `Discriminant(q,d1)`.
3. Require verified premises `Degree(c,3)`, `IrreducibleQQ(c)`, `Discriminant(c,d2)`, and `DiscNonSquareQQ(c)`.
4. Require a verified premise `NonSquareQQ(w)`.
5. Decode `factors` as `PolyQQList` and form the list of **distinct** factor refs in `factors.items`.
6. Require that among those distinct refs:
   - exactly one factor `q` has degree `2`,
   - exactly one factor `c` has degree `3`,
   - every remaining distinct factor `li` satisfies `Degree(li,1)`.
7. Decode `d1`, `d2`, and `w` canonically as rationals and require `w = d1*d2` exactly in `Q`.
8. Decode `G` canonically as `GroupId` with `system="smallgroup"` and require `(G.order, G.index) = (12, 4)`.
9. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended `f`, `q`, `c`, or `w`.
- `E_SIDE_CONDITION` — the factorization does not have exactly one distinct quadratic, exactly one distinct cubic, and all remaining distinct factors linear after ignoring multiplicities.
- `E_BAD_AUXILIARY_NONSQUARE` — the `NonSquareQQ` premise is not attached to the product `d1*d2`.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_GROUP_MISMATCH` — `G` is not `D6` in the SmallGroup catalog.
