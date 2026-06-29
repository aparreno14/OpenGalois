# Rule: `radical_roots.QQ.deg3.cardano.depressed_monic@1`

## 1) Rule id
`radical_roots.QQ.deg3.cardano.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(g: PolyQQ, roots: RadicalExprList)`

for an irreducible cubic polynomial `g` treated under the canonical depressed-monic Cardano scheme of `le5-core@1`.

## 3) Premises
Exactly three premises are required:

- `Degree(g, 3)` with the same polynomial `g` as in the claim.
- `IrreducibleQQ(g)` with the same polynomial `g`.
- `DepressedMonicEq(f, g)` for some polynomial `f`.

The third premise is used to certify, in the proof graph, that `g` is admitted as a depressed-monic representative under the ruleset normalization convention. The first argument `f` is not used by Cardano itself and may coincide with `g`.

## 4) Evidence
None.

## 5) Canonical radical scheme (normative)
Write
\[
g(x)=x^3+px+q.
\]
Let
\[
\Delta_C=\frac{q^2}{4}+\frac{p^3}{27},
\qquad
u=\sqrt[3]{-\frac q2+\sqrt{\Delta_C}},
\qquad
v=\sqrt[3]{-\frac q2-\sqrt{\Delta_C}}.
\]
Let \(\omega=\zeta_3\). This rule fixes the canonical ordered list
\[
\left[
u+v,\,
\omega u+\omega^2 v,\,
\omega^2 u+\omega v
\right].
\]

The canonical AST scheme is therefore:

- `root1 = add(u, v)`
- `root2 = add(mul(zeta(3,1), u), mul(zeta(3,2), v))`
- `root3 = add(mul(zeta(3,2), u), mul(zeta(3,1), v))`

with

- `u = root(3, add(qq(-q/2), root(2, qq(Δ_C))))`
- `v = root(3, sub(qq(-q/2), root(2, qq(Δ_C))))`

where `qq(r)` denotes the canonical rational literal node with value `r`.

Only trivial local simplifications are admitted by the reference checker (for example removing `+ 0` or `/ 1`). In particular, `root(n, 0)` is collapsed to `0`, and any occurrence of `0` raised to a nonzero integer power is collapsed to `0`. The rule does **not** accept algebraically equivalent but differently shaped radical expressions.

## 6) Verifier algorithm (normative)
1. Require the claim to be `RadicalRoots(g, roots)`.
2. Require a verified premise `Degree(g,3)`.
3. Require a verified premise `IrreducibleQQ(g)`.
4. Require a verified premise `DepressedMonicEq(f,g)` for some `f`.
5. Decode `g` canonically as a `PolyQQ` and defensively require that it has exact form `x^3 + p x + q` (monic, degree `3`, depressed).
6. Recompute the canonical Cardano list described above.
7. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
8. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound as required.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed polynomial is not a monic depressed cubic.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical Cardano list for this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg3.cardano.depressed_monic@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg3.cardano.depressed_monic@1_fail_001.json`
