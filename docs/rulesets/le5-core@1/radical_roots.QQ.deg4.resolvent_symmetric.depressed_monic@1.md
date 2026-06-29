# Rule: `radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1`

## 1) Rule id
`radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(g: PolyQQ, roots: RadicalExprList)`

for an irreducible quartic polynomial `g` treated under the canonical depressed-monic
symmetric resolvent scheme of `le5-core@1`.

## 3) Premises
Exactly five premises are required:

- `Degree(g, 4)` with the same polynomial `g` as in the claim.
- `IrreducibleQQ(g)` with the same polynomial `g`.
- `DepressedMonicEq(f, g)` for some polynomial `f`.
- `ResolventQQ(R, g, p)` where `p` is the canonical multivariate polynomial
  \((x_1+x_2)(x_3+x_4)\).
- `RadicalRoots(R, roots_R)` for the same cubic resolvent `R`.

## 4) Evidence
None.

## 5) Theoretical justification
Write
\[
g(t)=t^4+ct^2+dt+e.
\]
Let `roots_R = [s_1, s_2, s_3]` be the certified radical roots of the cubic resolvent attached
to
\[
p=(x_1+x_2)(x_3+x_4).
\]
The classical symmetric reconstruction uses the three quantities
\[
a=\sqrt{-s_1},\qquad b=\sqrt{-s_2},\qquad c'=\sqrt{-s_3},
\]
subject to the sign constraint
\[
abc'=-d.
\]
To obtain a deterministic certificate-level scheme in the generic branch `d != 0`, this rule fixes
\[
a=\sqrt{-s_1},\qquad b=\sqrt{-s_2},\qquad c=\frac{-d}{ab}.
\]
Since the constant term of the cubic resolvent is `d^2`, one has
\[
s_1s_2s_3=-d^2,
\]
and therefore
\[
c^2=\frac{d^2}{a^2b^2}=\frac{d^2}{(-s_1)(-s_2)}=-s_3.
\]
Thus `c` is a valid choice of square root of `-s_3`, and the classical quartic formulas become
\[
\frac{a+b+c}{2},\quad \frac{a-b-c}{2},\quad \frac{-a+b-c}{2},\quad \frac{-a-b+c}{2}.
\]

When `d = 0`, the cubic resolvent has a zero root. In this branch the rule keeps the same
symmetric scheme, but canonically places the zero root last:
\[
[s_1,s_2,s_3] := [\text{first nonzero root},\ \text{second nonzero root},\ 0].
\]
It then sets
\[
a=\sqrt{-s_1},\qquad b=\sqrt{-s_2},\qquad c=\sqrt{-s_3}=0,
\]
and uses the same symmetric quartic formulas.

## 6) Canonical radical scheme (normative)
- If `d != 0`, this rule fixes
  \[
  a=\sqrt{-s_1},\qquad b=\sqrt{-s_2},\qquad c=\frac{-d}{ab}.
  \]
- If `d = 0`, this rule first reorders the three resolvent roots so that the unique zero root
  is placed last, then sets
  \[
  a=\sqrt{-s_1},\qquad b=\sqrt{-s_2},\qquad c=\sqrt{-s_3}=0.
  \]

In both branches it emits the ordered list
\[
\left[
\frac{a+b+c}{2},\;
\frac{a-b-c}{2},\;
\frac{-a+b-c}{2},\;
\frac{-a-b+c}{2}
\right].
\]

Canonical AST comparison follows
`docs/rulesets/le5-core@1/radical_expr_canonicality.md`.

## 7) Verifier algorithm (normative)
1. Require verified premises `Degree(g,4)`, `IrreducibleQQ(g)`, and `DepressedMonicEq(f,g)` for some `f`.
2. Require a verified premise `ResolventQQ(R,g,p)` for the same `g`, with `p` equal to the canonical `MPolyQQ` for `(x1+x2)(x3+x4)`.
3. Require a verified premise `RadicalRoots(R, roots_R)` for the same cubic resolvent `R`.
4. Decode `g` canonically and defensively require exact form `t^4 + c t^2 + d t + e`.
5. Build the canonical symmetric-resolvent list using the branch policy above.
6. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
7. Accept.

## 8) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound as required.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed polynomial is not a monic depressed quartic.
- `E_BAD_RESOLVENT_FAMILY` — the resolvent premise uses the wrong quartic family.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical symmetric-resolvent list for this rule.

## 9) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1_001.json`
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1_002.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1_fail_001.json`
