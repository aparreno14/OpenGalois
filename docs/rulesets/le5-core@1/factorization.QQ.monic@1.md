# Rule: `factorization.QQ.monic@1`

## 1) Rule id
`factorization.QQ.monic@1`

## 2) Claim
Proves a fact of the form:

- `FactorizationMonicQQ(f: PolyQQ, factors: PolyQQList, unit: RatQQ)`

## 3) Premises
None.

## 4) Evidence
None (all information is contained in the claim arguments: `f`, `factors`, `unit`).

## 5) Verifier algorithm (normative)

Given `f` a `PolyQQ`, `factors` a `PolyQQList`, and `unit` a `RatQQ`, the verifier MUST:

1. Decode `f`, `factors`, and `unit` canonically.
2. Require `factors.items` is non-empty.
3. Interpret `factors.items` as a multiset: **duplicates encode multiplicity**.
4. For each factor `g` referenced in `factors.items`:
   - require `deg(g) >= 1` (non-constant),
   - require `lc(g) = 1` (monic).
5. Compute \(P = \prod_i g_i\) exactly in \(\mathbb{Q}[x]\).
6. Compute \(u \cdot P\) and compare for exact equality with `f`.
7. Accept iff equality holds.

This rule is computational (`recompute-and-compare`): the verifier recomputes the product locally and compares.

## 6) Failure codes
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_EMPTY_FACTORS` — `factors.items` is empty.
- `E_OBJECT_REF` — a referenced factor object cannot be resolved/decoded.
- `E_UNIT_ZERO` — `unit = 0`.
- `E_DEG0_FACTOR` — a factor is constant.
- `E_NOT_MONIC` — a factor has leading coefficient different from 1.
- `E_EXCEPTION` — arithmetic raised an exception.
- `E_PRODUCT_MISMATCH` — reconstructed product does not match `f`.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/factorization.QQ.monic@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/factorization.QQ.monic@1_fail_001.json`
