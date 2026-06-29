# Rule: `radical_roots.QQ.lift.depressed_monic@1`

## 1) Rule id
`radical_roots.QQ.lift.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(f: PolyQQ, roots: RadicalExprList)`

from a certified depressed-monic normalization `DepressedMonicEq(f,g)` and a certified radical-roots fact for the normalized polynomial `g`.

## 3) Premises
Exactly two premises are required:

- `DepressedMonicEq(f, g)` with the same `f` as in the claim.
- `RadicalRoots(g, roots_g)` with the same `g` as in the normalization premise.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)
The fact `DepressedMonicEq(f,g)` means that `g` is obtained from `f` by:

1. monicizing `f`, and
2. applying a rational Tschirnhaus translation `x -> x - t`.

If `g(x)=f_m(x-t)`, then every root `y` of `g` yields a root `x=y-t` of `f`. Therefore a certified ordered radical list for `g` can be transported to a certified ordered radical list for `f` by subtracting the same rational shift `t` from every expression.

In OpenGalois this rule is intentionally thin: the computational burden belongs to the rule certifying `DepressedMonicEq(f,g)` and to the rule certifying `RadicalRoots(g, roots_g)`. The present rule only transports the already-certified radical expressions back to the original polynomial.

## 6) Verifier algorithm (normative)
1. Require the claim to be `RadicalRoots(f, roots)`.
2. Require a verified premise `DepressedMonicEq(f,g)`.
3. Require a verified premise `RadicalRoots(g, roots_g)`.
4. Recompute the canonical rational shift `t` from the source polynomial `f` according to the depressed-monic normalization convention.
5. Recompute the transported ordered list by replacing each radical expression `y_i` in `roots_g` with `y_i - t`.
6. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
7. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended objects.
- `E_TYPE` — invalid claim shape, invalid normalization evidence, object decoding failure, or invalid `RadicalExprList` payload.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical transported list for this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.lift.depressed_monic@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.lift.depressed_monic@1_fail_001.json`
