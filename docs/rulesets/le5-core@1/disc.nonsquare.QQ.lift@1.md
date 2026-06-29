# Rule: `disc.nonsquare.QQ.lift@1`

## 1) Rule id
`disc.nonsquare.QQ.lift@1`

## 2) Claim
Proves a fact of the form:

- `DiscNonSquareQQ(f: PolyQQ)`

## 3) Premises
Exactly two premises:

- `Discriminant(f, D)` with the same `f` as in the claim.
- `NonSquareQQ(D)` for the same `D` appearing in the discriminant premise.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

1. Check there exists a verified premise `Discriminant(f, D)` whose `f` reference matches the claim.
2. Extract the referenced discriminant object `D` from that premise.
3. Check there exists a verified premise `NonSquareQQ(D)` for the same `D` reference.
4. Accept.

## 6) Failure codes
- `E_PREMISE_MISSING` — missing required premises.
- `E_PREMISE_BINDING` — premises exist but do not bind to the same `f` / `D`.
- `E_TYPE` — invalid claim shape.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/disc.nonsquare.QQ.lift@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/disc.nonsquare.QQ.lift@1_fail_001.json`
