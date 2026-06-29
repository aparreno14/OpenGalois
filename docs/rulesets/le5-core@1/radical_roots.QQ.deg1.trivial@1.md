# Rule: `radical_roots.QQ.deg1.trivial@1`

## 1) Rule id
`radical_roots.QQ.deg1.trivial@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(f: PolyQQ, roots: RadicalExprList)`

for a polynomial of degree `1`.

## 3) Premises
Exactly one premise is required:

- `Degree(f, 1)` with the same polynomial `f` as in the claim.

## 4) Evidence
None.

## 5) Canonical radical scheme (normative)
Let
\[
f(x)=ax+b\qquad (a
eq 0).
\]
Then the unique root is
\[
-b/a.
\]
The canonical output of this rule is the one-element list
\[
[\, -b/a \,].
\]
The corresponding `RadicalExpr` is a single `qq` literal node:

```json
{ "kind": "qq", "value_qq": "..." }
```

No alternative but algebraically equivalent AST is accepted. Equality is exact structural equality of the canonical `RadicalExpr` payload.

## 6) Verifier algorithm (normative)
1. Require the claim to be `RadicalRoots(f, roots)`.
2. Require a verified premise `Degree(f,1)`.
3. Decode `f` canonically as a `PolyQQ` and defensively require `deg(f)=1`.
4. If `f(x)=ax+b`, recompute the canonical root expression as the one-element list
   `[{"kind":"RadicalExpr","expr":{"kind":"qq","value_qq":str((-b)/a)}}]`.
5. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality.
6. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound to the same polynomial.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed degree is not 1 or the leading coefficient is zero.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical list for this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg1.trivial@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg1.trivial@1_fail_001.json`
