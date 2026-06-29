# Rule: `degree.QQ@1`

## 1) Rule id
`degree.QQ@1`

## 2) Claim
Proves a fact of the form:

- `Degree(f: PolyQQ, n: IntZ)`

## 3) Premises
None.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

1. Decode `f` canonically as a `PolyQQ`.
2. Decode `n` canonically as an `IntZ`.
3. Recompute `deg(f)` using the canonical polynomial representation (leading zeros trimmed).
4. Accept iff `n == deg(f)`.

## 6) Failure codes
- `E_TYPE` — invalid claim shape or cannot decode `f` / `n`.
- `E_MISMATCH` — claimed degree does not match the recomputed degree.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/degree.QQ@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/degree.QQ@1_fail_001.json`
