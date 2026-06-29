# Rule: `galois_group.QQ.lift.depressed_monic@1`

## 1) Rule id
`galois_group.QQ.lift.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

from a certified depressed-monic normalization of `f` and a certified Galois-group fact for the normalized polynomial.

## 3) Premises
Exactly two premises:

- `DepressedMonicEq(f, g)` with the same `f` as in the claim.
- `GaloisGroup(g, G)` with the same `g` as in the normalization premise and the same `G` as in the claim.

This is a **theorem-style** lift rule. It does not recompute the normalization and it does not reclassify the group of `g`. It only checks that an already-certified depressed-monic normalization connects the input polynomial `f` to a polynomial `g` whose Galois group has already been certified.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

The fact `DepressedMonicEq(f, g)` means that `g` is obtained from `f` by the standard rational normalization used in OpenGalois:

1. multiply by a nonzero rational scalar so that the polynomial becomes monic, and
2. apply a rational Tschirnhaus translation `x -> x - t` that kills the `x^(n-1)` term.

Neither of these operations changes the splitting field over `QQ`:

- multiplying by a nonzero rational scalar does not change the set of roots;
- translating the variable by a rational amount sends the roots of `f` to the roots of `g` by a rational affine change of variables.

Therefore `f` and `g` have the same splitting field over `QQ`, hence the same Galois group up to the abstract group identifier used by the ruleset.

In OpenGalois this rule is intentionally thin. The computational burden belongs to:

- the rule that certifies `DepressedMonicEq(f,g)`, and
- the theorem/computational rule that certifies `GaloisGroup(g,G)`.

The present rule only performs the logical lift from the normalized representative back to the original polynomial.

## 6) Verifier algorithm (normative)

1. Require the claim to be `GaloisGroup(f, G)`.
2. Require a verified premise `DepressedMonicEq(f, g)` bound to the same `f` as in the claim.
3. Require a verified premise `GaloisGroup(g, G)` bound to the same `g` as in the normalization premise.
4. Require that the `GroupId` in the second premise matches the `GroupId` of the claim.
5. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended objects.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.lift.depressed_monic@1_001.json` *(placeholder until the emitting pipeline starts using the lift rule)*
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.lift.depressed_monic@1_fail_001.json` *(placeholder)*
