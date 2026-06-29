# Rule: `radical_roots.QQ.deg2.quadratic_formula@1`

## 1) Rule id
`radical_roots.QQ.deg2.quadratic_formula@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(f: PolyQQ, roots: RadicalExprList)`

for an irreducible polynomial of degree `2`.

## 3) Premises
Exactly two premises are required:

- `Degree(f, 2)` with the same polynomial `f` as in the claim.
- `IrreducibleQQ(f)` with the same polynomial `f`.

## 4) Evidence
None.

## 5) Canonical radical scheme (normative)
Let
\[
f(x)=ax^2+bx+c\qquad (a
eq 0),\qquad \Delta=b^2-4ac.
\]
This rule uses the quadratic formula in the exact canonical order
\[
\left[\, rac{-b+\sqrt{\Delta}}{2a},\; rac{-b-\sqrt{\Delta}}{2a} \,ight].
\]
The rule does **not** accept algebraically equivalent but differently shaped ASTs. The checker recomputes this precise scheme and compares by exact structural equality.

The canonical ASTs are:

- first root: `div(add(qq(-b), root(2, qq(Δ))), qq(2a))`
- second root: `div(sub(qq(-b), root(2, qq(Δ))), qq(2a))`

where `qq(r)` denotes the canonical `qq` literal node with value `r`.

## 6) Verifier algorithm (normative)
1. Require the claim to be `RadicalRoots(f, roots)`.
2. Require a verified premise `Degree(f,2)`.
3. Require a verified premise `IrreducibleQQ(f)`.
4. Decode `f` canonically as a `PolyQQ` and defensively require `deg(f)=2`.
5. If `f(x)=ax^2+bx+c`, recompute `Δ=b^2-4ac` and `2a`.
6. Recompute the canonical ordered root list described above.
7. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality.
8. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound to the same polynomial.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed degree is not 2 or the leading coefficient is zero.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical list for this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg2.quadratic_formula@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg2.quadratic_formula@1_fail_001.json`
