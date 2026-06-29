# Rule: `galois_group.QQ.deg2.C2@1`

## 1) Rule id
`galois_group.QQ.deg2.C2@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Exactly two premises, of the form:

- `Degree(f, n)` with the same polynomial `f` as in the claim, and `n = 2`.
- `IrreducibleQQ(f)` with the same polynomial `f` as in the claim.

In other words, the rule requires previously verified facts proving that `f` has degree 2 and is irreducible over $\mathbb{Q}$.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

1. Check there is a premise matching `Degree(f, 2)`:
   - same `f` reference as the claim’s first argument,
   - second argument is an `IntZ` object with canonical value `"2"`.
2. Check there is a premise matching `IrreducibleQQ(f)`:
   - same `f` reference as the claim’s first argument.   
3. Decode `f` canonically as a `PolyQQ`.
4. Decode `G` canonically as a `GroupId` with `system="smallgroup"`.
5. Require `(G.order, G.index) = (2, 1)`.
6. Accept.

Justification: Let f be an irreducible polynomial of degree 2 over $\mathbb{Q}$. Adjoining one root of f generates a quadratic field extension $K$ over $\mathbb{Q}$ with degree $[K : \mathbb{Q}] = 2$. The other root is also in $K$ (their sum is rational), making $K$ the splitting field of f. The Galois group of $K/\mathbb{Q}$ must have an order equal to the extension degree (2). The only group of order 2 is the cyclic group $C_2$, identified in the Small Groups catalog as (2, 1).

## 6) Failure codes
- `E_PREMISE_MISSING` — missing required premises.
- `E_PREMISE_BINDING` — premise exists but does not bind to the same `f`, or degree object is not `IntZ("2")`.
- `E_TYPE` — invalid claim shape or cannot decode `f` / `G`.
- `E_GROUP_MISMATCH` — `G` is not C2 `(order=2,index=1)` in the SmallGroup catalog.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/galois_group.QQ.deg2.C2@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/galois_group.QQ.deg2.C2@1_fail_001.json`