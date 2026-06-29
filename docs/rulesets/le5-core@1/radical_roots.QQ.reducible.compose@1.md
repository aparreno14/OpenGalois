# Rule: `radical_roots.QQ.reducible.compose@1`

## 1) Rule id
`radical_roots.QQ.reducible.compose@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(f: PolyQQ, roots: RadicalExprList)`

for a reducible polynomial whose distinct irreducible factors already have certified radical root lists.

## 3) Premises
Required premises:

- `FactorizationMonicQQ(f, factors, unit)` with the same polynomial `f` as in the claim.
- For each **distinct factor reference** `g` occurring in `factors.items`:
  - `IrreducibleQQ(g)`
  - `RadicalRoots(g, roots_g)`

Multiplicity is encoded by repeated references in `factors.items`.

## 4) Evidence
None.

## 5) Canonical radical scheme (normative)
This rule does not introduce a new formula. It composes already certified factor-level root lists.

Let
\[
f = u \prod_i g_i
\]
be the certified monic factorization, where `factors.items = [g_{i_1},\dots,g_{i_m}]` is the normative order with multiplicity.
For each distinct factor reference `g`, let
\[
\mathrm{Roots}(g)= [r_{g,1},\dots,r_{g,k_g}]
\]
be the already certified list from the corresponding premise `RadicalRoots(g, roots_g)`.

Then the canonical output of this rule is the concatenation
\[
\mathrm{Roots}(g_{i_1})\,\Vert\,\mathrm{Roots}(g_{i_2})\,\Vert\,\cdots\,\Vert\,\mathrm{Roots}(g_{i_m}).
\]
If the same factor reference appears multiple times in `factors.items`, the same certified root list is repeated each time.

No reordering, deduplication, or algebraic simplification is performed.

## 6) Verifier algorithm (normative)
1. Require the claim to be `RadicalRoots(f, roots)`.
2. Require a verified premise `FactorizationMonicQQ(f, factors, unit)`.
3. Decode `factors` as `PolyQQList`.
4. Form the order-preserving list of distinct factor refs occurring in `factors.items`.
5. For each such factor `g`, require a verified premise `IrreducibleQQ(g)`.
6. For each such factor `g`, require a verified premise `RadicalRoots(g, roots_g)`.
7. Recompute the expected root list for `f` by concatenating the already certified lists `roots_g` in the exact order of factor occurrences in `factors.items`.
8. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality.
9. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound to the required factor.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the certified factor list is empty.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical concatenation of factor-level lists.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.reducible.compose@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.reducible.compose@1_fail_001.json`
