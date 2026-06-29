# Rule: `galois_group.QQ.reducible.double_quadratic.C2@1`

## 1) Rule id
`galois_group.QQ.reducible.double_quadratic.C2@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

with the intended conclusion that `G` is the cyclic group of order `2`.

## 3) Premises
This is a theorem rule. The verifier receives already-verified premises and must check that the
required premises are present and correctly bound.

Required premises:

- `FactorizationMonicQQ(f, factors, unit)` with the same `f` as in the claim.
- `Degree(q1, 2)`.
- `IrreducibleQQ(q1)`.
- `Discriminant(q1, d1)`.
- `Degree(q2, 2)`.
- `IrreducibleQQ(q2)`.
- `Discriminant(q2, d2)`.
- `IsSquareQQ(c)` where `c` is the rational number `d1*d2`.
- For every remaining **distinct** factor ref `l` in `factors.items` different from `q1` and `q2`, a premise
  `Degree(l, 1)`.

The factorization premise must witness a reducible pattern whose non-linear core, after ignoring
linear factors and multiplicities, is exactly two distinct irreducible quadratics `q1`, `q2`.
Equivalently, among the **distinct** factor refs appearing in `factors.items`:

- `q1` and `q2` are the only non-linear factors,
- both are irreducible quadratics,
- `q1 != q2`,
- every other distinct factor ref is linear.

So this rule applies to the reducible core `[2,2]`, allowing optional linear factors and optional
repetition of the same quadratic factors. Repeated occurrences do not change the splitting field and
therefore do not change the intended classification.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
 f = u \cdot l_1 \cdots l_r \cdot q_1^{e_1} q_2^{e_2}
\]

with `u ∈ Q^×`, where each `l_i` is linear over `Q`, where `q1`, `q2` are distinct irreducible
quadratics, and where `e_1, e_2 >= 1`.

The linear factors contribute only rational roots, so they do not enlarge the splitting field.
Likewise, repeating an irreducible factor does not change the splitting field: the splitting field
of `q^m` is the same as the splitting field of `q`. Therefore the splitting field of `f` is the
same as the splitting field of the square-free quadratic core `q1 q2`.

For an irreducible quadratic polynomial `q`, its splitting field is a quadratic extension
`Q(√disc(q))`. Two irreducible quadratics define the same quadratic field exactly when their
quadratic discriminants differ by a square in `Q^×`, equivalently when `d1*d2` is a square in `Q`.
If `d1*d2` is a square, the two quadratic factors generate the same quadratic field, so the full
splitting field still has degree `2`. Hence

\[
\operatorname{Gal}(f/\mathbf{Q}) \cong C_2.
\]

## 6) Verifier algorithm (normative)

1. Require the claim to be `GaloisGroup(f, G)`.
2. Require a verified premise `FactorizationMonicQQ(f, factors, unit)` bound to the same `f`.
3. Decode `factors` as `PolyQQList`.
4. Form the list of **distinct** factor refs appearing in `factors.items`.
5. Inspect those distinct refs and require that:
   - exactly two distinct factor refs `q1`, `q2` are justified by premises `Degree(q1,2)`, `IrreducibleQQ(q1)` and `Degree(q2,2)`, `IrreducibleQQ(q2)`;
   - every other distinct factor ref `l` is justified by a verified premise `Degree(l,1)`.
6. Require verified premises `Discriminant(q1,d1)` and `Discriminant(q2,d2)`.
7. Compute the rational product `d1*d2`.
8. Require a verified premise `IsSquareQQ(c)` whose argument `c` is exactly the canonical `RatQQ`
   object encoding that product.
9. Decode `G` canonically as `GroupId` with `system="smallgroup"` and require `(G.order, G.index) = (2,1)`.
10. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but is malformed or does not bind to the required `f`, quadratic factors, or discriminant product.
- `E_TYPE` — invalid claim shape or object decoding failure.
- `E_SIDE_CONDITION` — the factorization premise is not of the required `[2,2]`-plus-linears form after ignoring multiplicities.
- `E_GROUP_MISMATCH` — the claim does not state `C2`.
