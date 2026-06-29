# Rule: `radical_roots.QQ.deg4.ferrari.depressed_monic@1`

## 1) Rule id
`radical_roots.QQ.deg4.ferrari.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(g: PolyQQ, roots: RadicalExprList)`

for an irreducible quartic polynomial `g` treated under the canonical depressed-monic
quartic Ferrari scheme of `le5-core@1`.

## 3) Premises
Exactly five premises are required:

- `Degree(g, 4)` with the same polynomial `g` as in the claim.
- `IrreducibleQQ(g)` with the same polynomial `g`.
- `DepressedMonicEq(f, g)` for some polynomial `f`.
- `ResolventQQ(R, g, p)` where `p` is the canonical multivariate polynomial
  \((x_1+x_2)(x_3+x_4)\).
- `RadicalRoots(R, roots_R)` for the same cubic resolvent `R`.

The rule therefore works on a quartic already admitted in the proof graph as a depressed
monic representative, and assumes that a radical description of the cubic resolvent has
already been certified.

## 4) Evidence
None.

## 5) Theoretical justification
Write
\[
g(t)=t^4+ct^2+dt+e.
\]
Let `R` be the cubic resolvent attached to the family
\[
p=(x_1+x_2)(x_3+x_4).
\]
If `s` is a root of `R`, then the quartic admits the classical Ferrari-style
factorization
\[
g(t)=(t^2-ut+\alpha)(t^2+ut+\beta),
g(t)=(t^2-ut+\alpha)(t^2+ut+\beta),
\]
where
\[
u=\sqrt{-s},\qquad \alpha=\frac{c-s-d/u}{2},\qquad \beta=\frac{c-s+d/u}{2}.
\]
Expanding the right-hand side gives
\[
t^4+(\alpha+\beta-u^2)t^2+u(\beta-\alpha)t+\alpha\beta,
t^4+(\alpha+\beta-u^2)t^2+u(\beta-\alpha)t+\alpha\beta,
\]
and the defining relation for `s` as a root of the cubic resolvent is exactly what makes
these coefficients equal to `c`, `d`, and `e`.

This yields two monic quadratics, so the four roots of `g` are obtained by applying the
quadratic formula to each factor.

When `d = 0`, the same Ferrari construction still applies. The only issue is canonical
selection of the resolvent root: the cubic resolvent then has a zero root, so choosing it
would make the intermediate expression `d/u` syntactically singular. The rule therefore
uses the first **nonzero** resolvent root in that branch and keeps the same Ferrari
factorization scheme.

## 6) Canonical radical scheme (normative)
Let `roots_R = [s_1, s_2, s_3]`.

- If `d != 0`, this rule fixes `s := s_1`.
- If `d = 0`, this rule fixes `s` to be the first nonzero root in `roots_R`.

It then builds
\[
u=\sqrt{-s},\qquad \alpha=\frac{c-s-d/u}{2},\qquad \beta=\frac{c-s+d/u}{2},
\]
and emits the ordered list obtained by the canonical quadratic-formula scheme for
\[
t^2-ut+\alpha \qquad\text{and}\qquad t^2+ut+\beta.
\]

Canonical AST comparison follows
`docs/rulesets/le5-core@1/radical_expr_canonicality.md`.

## 7) Verifier algorithm (normative)
1. Require verified premises `Degree(g,4)`, `IrreducibleQQ(g)`, and `DepressedMonicEq(f,g)` for some `f`.
2. Require a verified premise `ResolventQQ(R,g,p)` for the same `g`, with `p` equal to the canonical `MPolyQQ` for `(x1+x2)(x3+x4)`.
3. Require a verified premise `RadicalRoots(R, roots_R)` for the same cubic resolvent `R`.
4. Decode `g` canonically and defensively require exact form `t^4 + c t^2 + d t + e`.
5. Select the canonical resolvent root `s` according to the rule-local policy above.
6. Build the canonical Ferrari list from `s`.
7. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
8. Accept.

## 8) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound as required.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed polynomial is not a monic depressed quartic.
- `E_BAD_RESOLVENT_FAMILY` — the resolvent premise uses the wrong quartic family.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical Ferrari list for this rule.

## 9) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.ferrari.depressed_monic@1_001.json`
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.ferrari.depressed_monic@1_002.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg4.ferrari.depressed_monic@1_fail_001.json`
