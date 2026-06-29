# Rule: `irreducible.QQ.to.depressed_monic@1`

## 1) Rule id
`irreducible.QQ.to.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `IrreducibleQQ(g: PolyQQ)`

from a certified depressed-monic normalization `DepressedMonicEq(f,g)` and a certified irreducibility fact for the source polynomial `f`.

## 3) Premises
Exactly two premises are required:

- `DepressedMonicEq(f, g)`.
- `IrreducibleQQ(f)` with the same `f` as in the normalization premise.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

The fact `DepressedMonicEq(f,g)` means that `g` is obtained from `f` over \(\mathbf{Q}\) by:

1. multiplying by a nonzero rational scalar so that the polynomial becomes monic, and
2. applying a rational Tschirnhaus translation \(x \mapsto x - t\).

Both operations preserve irreducibility over \(\mathbf{Q}\):

- scaling by a nonzero rational changes the polynomial only by a unit in \(\mathbf{Q}[x]\),
- translation by a rational parameter is an automorphism of \(\mathbf{Q}[x]\).

Therefore:

\[
f \text{ irreducible in } \mathbf{Q}[x]
\quad\Longrightarrow\quad
g \text{ irreducible in } \mathbf{Q}[x].
\]

This rule is intentionally theorem-style: the computational burden belongs to the rule certifying
`DepressedMonicEq(f,g)` and to the rule certifying `IrreducibleQQ(f)`.

## 6) Verifier algorithm (normative)

1. Require the claim to be `IrreducibleQQ(g)`.
2. Require a verified premise `DepressedMonicEq(f,g)`.
3. Require a verified premise `IrreducibleQQ(f)`.
4. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended `f` / `g`.
- `E_TYPE` — invalid claim shape.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/irreducible.QQ.to.depressed_monic@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/irreducible.QQ.to.depressed_monic@1_fail_001.json`
