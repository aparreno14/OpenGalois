# Rule: `radical_roots.QQ.deg3.cardano.depressed_monic@2`

## 1) Rule id
`radical_roots.QQ.deg3.cardano.depressed_monic@2`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(g: PolyQQ, roots: RadicalExprList)`

for an irreducible cubic polynomial `g` treated under the canonical depressed-monic Cardano scheme of `le5-core@1`.

This is the version-2 Cardano scheme. It supersedes `radical_roots.QQ.deg3.cardano.depressed_monic@1` as the preferred emitted form, but it does not change the meaning of the predicate `RadicalRoots`.

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
Let \(\omega=\zeta_3\).

This rule has two canonical branches.

### 5.1 Special branch: `p = 0`

If \(p=0\), the polynomial is
\[
g(x)=x^3+q.
\]
The rule defines
\[
w=\sqrt[3]{-q}
\]
and fixes the canonical ordered root list
\[
[w,\,\omega w,\,\omega^2 w].
\]

In AST form:

- `w = root(3, qq(-q))`
- `root1 = w`
- `root2 = mul(zeta(3,1), w)`
- `root3 = mul(zeta(3,2), w)`

This branch is deliberately local to the Cardano-v2 rule.

### 5.2 Generic branch: `p != 0`

If \(p\ne 0\), define
\[
\Delta_C=\frac{q^2}{4}+\frac{p^3}{27},
\qquad
u=\sqrt[3]{-\frac q2+\sqrt{\Delta_C}},
\qquad
\alpha=-\frac p3.
\]

For this fixed choice of \(u\), the implication \(u=0 \Rightarrow p=0\) holds. Hence in the generic branch \(p\ne0\), the denominator \(u\) is nonzero.

The rule fixes the canonical ordered list
\[
\left[
u+\frac{\alpha}{u},\,
\omega u+\omega^2 \frac{\alpha}{u},\,
\omega^2 u+\omega \frac{\alpha}{u}
\right].
\]

In AST form:

- `u = root(3, add(qq(-q/2), root(2, qq(Δ_C))))`
- `alpha_over_u = div(qq(-p/3), u)`
- `root1 = add(u, alpha_over_u)`
- `root2 = add(mul(zeta(3,1), u), mul(zeta(3,2), alpha_over_u))`
- `root3 = add(mul(zeta(3,2), u), mul(zeta(3,1), alpha_over_u))`

The rule does **not** accept algebraically equivalent but differently shaped radical expressions. In particular, the older independent `u,v` Cardano shape from `@1` is rejected by this rule.

## 6) Verifier algorithm (normative)
1. Require the claim to be `RadicalRoots(g, roots)`.
2. Require a verified premise `Degree(g,3)`.
3. Require a verified premise `IrreducibleQQ(g)`.
4. Require a verified premise `DepressedMonicEq(f,g)` for some `f`.
5. Decode `g` canonically as a `PolyQQ` and defensively require that it has exact form `x^3 + p x + q` (monic, degree `3`, depressed).
6. If `p = 0`, recompute the special branch `[w, ωw, ω²w]` with `w = root(3, qq(-q))`.
7. If `p != 0`, recompute the generic branch using `u` and `alpha_over_u = (-p/3)/u`.
8. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
9. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound as required.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed polynomial is not a monic depressed cubic.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical Cardano-v2 list for this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg3.cardano.depressed_monic@2_001.json`
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg3.cardano.depressed_monic@2_002_p0.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg3.cardano.depressed_monic@2_fail_001.json`
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg3.cardano.depressed_monic@2_fail_002_p0_wrong_zero.json`
