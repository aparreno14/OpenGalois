# Rule: `galois_group.QQ.reducible.all_linear.trivial@1`

## 1) Rule id
`galois_group.QQ.reducible.all_linear.trivial@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

with the intended conclusion that `G` is the trivial group.

## 3) Premises
This is a theorem rule. The verifier receives a list of already-verified premise claims and must
check that the theorem application contains the premises required by the rule.

Required premises:

- `FactorizationMonicQQ(f, factors, unit)` with the same `f` as in the claim.
- For each **distinct factor reference** `l` occurring in `factors.items`, a verified premise
  `Degree(l, 1)`.

The factorization premise is part of the mathematical content of the rule: it certifies that the
input polynomial splits as a product of listed monic factors over `Q[x]`. The degree premises then
state explicitly that every listed factor is linear.

This rule is intended for the reducible branch, so the certified factorization must contain at least
2 factor occurrences.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)
Assume the certified factorization exhibits

\[
f = u \cdot l_1^{e_1} \cdots l_r^{e_r}
\]

with `u ∈ Q^×` and each `l_i` linear over `Q`. Then every root of `f` is rational. Therefore the
splitting field of `f` over `Q` is just `Q`, so the Galois group is trivial.

### 5.1 Why the linearity premises are explicit
OpenGalois aims to be glass-box and mathematically legible. It is therefore not enough to say only
that `f` factors as a product of listed factors; the certificate should also state that those factors
are linear. That is why the rule explicitly consumes `Degree(l,1)` premises.

### 5.2 Why one premise per distinct factor reference is enough
If a factor reference occurs several times in `factors.items`, this records multiplicity. Repeated
roots do not enlarge the splitting field. Since `Degree(l,1)` is a fact about the object `l` itself,
one verified degree premise per distinct factor reference is sufficient.

### 5.3 Role of the checker
As with the existing theorem rules in the project, the checker does not re-prove the premises. The
factorization premise has already been verified by the factorization rule, and each degree premise has
already been verified by the degree rule. The checker only looks for the required premises, checks the
bindings that the rule asks for, and enforces the trivial-group conclusion.

## 6) Verifier algorithm (normative)
1. Require the claim to be `GaloisGroup(f, G)`.
2. Require a verified premise `FactorizationMonicQQ(f, factors, unit)` bound to the same `f` as in the claim.
3. Decode `factors` as `PolyQQList` and require `len(factors.items) >= 2`.
4. Form the order-preserving list of distinct factor refs occurring in `factors.items`.
5. For each such factor ref `l`, require a verified premise `Degree(l, 1)`.
6. Decode the claim group `G` canonically as `GroupId` with `system="smallgroup"` and require
   `(G.order, G.index) = (1,1)`.
7. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the required object, or a required
  `Degree(l,1)` binding is wrong.
- `E_TYPE` — invalid claim shape or object decoding failure.
- `E_SIDE_CONDITION` — the certified factorization is not reducible.
- `E_GROUP_MISMATCH` — the claim does not state the trivial group.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.reducible.all_linear.trivial@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.reducible.all_linear.trivial@1_fail_001.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.reducible.all_linear.trivial@1_fail_002.json`
