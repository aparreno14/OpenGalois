# Rule: `galois_group.QQ.reducible.quadratic_cubic.S3@2`

## 1) Rule id
`galois_group.QQ.reducible.quadratic_cubic.S3@2`

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
- `NonSquareQQ(d2)`.
- `IsSquareQQ(w)`.

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

When the cubic discriminant is not a square, the cubic side is in the `S3` branch. The compositum has
Galois group `S3` exactly when `d1*d2` is a square in `Q`.

This version consumes `NonSquareQQ(d2)` directly rather than `DiscNonSquareQQ(c)`.

## 6) Verifier algorithm (normative)

1. Check there is a verified premise `FactorizationMonicQQ(f, factors, unit)` bound to the same `f`.
2. Check there are verified premises `Degree(q,2)`, `IrreducibleQQ(q)`, `Discriminant(q,d1)`.
3. Check there are verified premises `Degree(c,3)`, `IrreducibleQQ(c)`, `Discriminant(c,d2)`, and `NonSquareQQ(d2)`.
4. Decode `factors` as `PolyQQList` and form the list of **distinct** factor refs in `factors.items`.
5. Require that among those distinct refs:
   - exactly one factor `q` has degree `2`,
   - exactly one factor `c` has degree `3`,
   - every remaining distinct factor `li` satisfies `Degree(li,1)`.
6. Require a verified premise `IsSquareQQ(w)` where `w = d1*d2` exactly in `Q`.
7. Decode `G` canonically as `GroupId(system="smallgroup")` and require `(G.order,G.index)=(6,2)`.
8. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended `f`, `q`, `c`, `d2`, or `w`.
- `E_SIDE_CONDITION` — the factorization does not have exactly one distinct quadratic, exactly one distinct cubic, and all remaining distinct factors linear after ignoring multiplicities.
- `E_BAD_AUXILIARY_SQUARE` — the `IsSquareQQ` premise is not attached to the product `d1*d2`.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_GROUP_MISMATCH` — `G` is not `S3` in the SmallGroup catalog.
