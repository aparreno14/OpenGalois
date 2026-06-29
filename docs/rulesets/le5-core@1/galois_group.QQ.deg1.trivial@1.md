# Rule: `galois_group.QQ.deg1.trivial@1`

## 1) Rule id
`galois_group.QQ.deg1.trivial@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly one premise, of the form:

- `Degree(f, n)` with the same polynomial `f` as in the claim, and `n = 1`.

In other words, the rule requires a previously verified degree fact proving that `f` has degree 1.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

1. Check there is a premise matching `Degree(f, 1)`:
   - same `f` reference as the claim’s first argument,
   - second argument is an `IntZ` object with canonical value `"1"`.
2. Decode `f` canonically as a `PolyQQ`.
3. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
4. (Defensive check) Recompute `deg(f)` and require `deg(f) = 1`.
5. Require `(G.order, G.index) = (1, 1)`.
6. Accept.

Justification: the splitting field of a degree-1 polynomial over \(\mathbb{Q}\) is \(\mathbb{Q}\) itself, hence the Galois group is the trivial group.

## 6) Failure codes
- `E_PREMISE_MISSING` — missing required premise `Degree(f,1)`.
- `E_PREMISE_BINDING` — premise exists but does not bind to the same `f`, or degree object is not `IntZ("1")`.
- `E_TYPE` — invalid claim shape or cannot decode `f` / `G`.
- `E_SIDE_CONDITION` — recomputed degree is not 1.
- `E_GROUP_MISMATCH` — `G` is not the trivial group `(order=1,index=1)` in the SmallGroup catalog.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg1.trivial@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg1.trivial@1_fail_001.json`