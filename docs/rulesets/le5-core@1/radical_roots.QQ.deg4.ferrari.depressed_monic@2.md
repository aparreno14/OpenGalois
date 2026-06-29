# Rule: `radical_roots.QQ.deg4.ferrari.depressed_monic@2`

## 1) Rule id
`radical_roots.QQ.deg4.ferrari.depressed_monic@2`

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

## 4) Evidence
None.

## 5) Theoretical justification
Write
\[
g(t)=t^4+ct^2+dt+e.
\]

This rule keeps the same quartic resolvent family as Ferrari@1, but changes the
canonical AST shape in two ways:

- when `d = 0`, it treats the quartic as a genuine biquadratic;
- when `d != 0`, it emits the already-simplified Ferrari formulas instead of
  going through an intermediate quadratic-formula helper.

### 5.1 Biquadratic branch (`d = 0`)
If `d = 0`, set `y = t^2`. Then `g` becomes
\[
y^2 + c y + e = 0,
\]
so
\[
y_\pm = \frac{-c \pm \sqrt{c^2 - 4e}}{2}.
\]
The quartic roots are therefore
\[
\pm\sqrt{y_+},\qquad \pm\sqrt{y_-}.
\]

### 5.2 Simplified Ferrari branch (`d != 0`)
Let `s` be the first certified root in `roots_R`, and set
\[
u = \sqrt{-s}.
\]
Then the canonical discriminants of the two quadratic factors are emitted directly as
\[
\Delta_1 = s - 2c + \frac{2d}{u},\qquad
\Delta_2 = s - 2c - \frac{2d}{u}.
\]
The four roots are then emitted in the ordered list
\[
\left[
\frac{u+\sqrt{\Delta_1}}{2},
\frac{u-\sqrt{\Delta_1}}{2},
\frac{-u+\sqrt{\Delta_2}}{2},
\frac{-u-\sqrt{\Delta_2}}{2}
\right].
\]

## 6) Canonical radical scheme (normative)
The canonical AST list is:

- if `d = 0`:
  \[
  [\sqrt{y_+}, -\sqrt{y_+}, \sqrt{y_-}, -\sqrt{y_-}]
  \]
  with
  \[
  y_\pm = \frac{-c \pm \sqrt{c^2 - 4e}}{2};
  \]

- if `d != 0`:
  \[
  \left[
  \frac{u+\sqrt{\Delta_1}}{2},
  \frac{u-\sqrt{\Delta_1}}{2},
  \frac{-u+\sqrt{\Delta_2}}{2},
  \frac{-u-\sqrt{\Delta_2}}{2}
  \right]
  \]
  with
  \[
  u = \sqrt{-s},\qquad
  \Delta_1 = s - 2c + \frac{2d}{u},\qquad
  \Delta_2 = s - 2c - \frac{2d}{u}.
  \]

Comparison is by exact structural equality of canonical `RadicalExpr` payloads.

## 7) Verifier algorithm (normative)
1. Require verified premises `Degree(g,4)`, `IrreducibleQQ(g)`, and `DepressedMonicEq(f,g)` for some `f`.
2. Require a verified premise `ResolventQQ(R,g,p)` for the same `g`, with `p` equal to the canonical `MPolyQQ` for `(x1+x2)(x3+x4)`.
3. Require a verified premise `RadicalRoots(R, roots_R)` for the same cubic resolvent `R`.
4. Decode `g` canonically and defensively require exact form `t^4 + c t^2 + d t + e`.
5. If `d = 0`, recompute the canonical biquadratic branch.
6. If `d != 0`, recompute the canonical simplified Ferrari branch.
7. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
8. Accept.

## 8) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound as required.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed polynomial is not a monic depressed quartic.
- `E_BAD_RESOLVENT_FAMILY` — the resolvent premise uses the wrong quartic family.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical Ferrari-v2 list for this rule.

## 9) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.ferrari.depressed_monic@2_001.json`
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.ferrari.depressed_monic@2_002.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg4.ferrari.depressed_monic@2_fail_001.json`
