# Rule: `is_square.QQ.lift@1`

## 1) Rule id
`is_square.QQ.lift@1`

## 2) Claim
Proves a fact of the form:

- `IsSquareQQ(q: RatQQ)`

## 3) Premises
Exactly one premise of the form:

- `SqrtQQ(q: RatQQ, k: RatQQ)` with the same `q` as in the claim.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

1. Check there exists a previously verified premise matching `SqrtQQ(q,k)` with the same `q` as the claim.
2. Accept.

## 6) Failure codes
- `E_PREMISE_MISSING` — missing required premise.
- `E_PREMISE_BINDING` — premise exists but does not bind to the same `q`.
- `E_TYPE` — invalid claim shape.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/is_square.QQ.lift@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/is_square.QQ.lift@1_fail_001.json`
