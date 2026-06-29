# Rule: `sqrt.QQ.check@1`

## 1) Rule id
`sqrt.QQ.check@1`

## 2) Claim
Proves a fact of the form:

- `SqrtQQ(q: RatQQ, k: RatQQ)`

## 3) Premises
None.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

1. Decode `q` canonically as a `RatQQ`, yielding \(q \in \mathbb{Q}\).
2. Decode `k` canonically as a `RatQQ`, yielding \(k \in \mathbb{Q}\).
3. Accept iff \(k^2 = q\) exactly in \(\mathbb{Q}\).

## 6) Failure codes
- `E_TYPE` — invalid claim shape or cannot decode `q` / `k`.
- `E_MISMATCH` — \(k^2\) does not equal \(q\).

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/sqrt.QQ.check@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/sqrt.QQ.check@1_fail_001.json`
