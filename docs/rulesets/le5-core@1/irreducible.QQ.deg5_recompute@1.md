# Rule: `irreducible.QQ.deg5_recompute@1`

## 1) Rule id
`irreducible.QQ.deg5_recompute@1`

## 2) Claim
Proves a fact of the form:

- `IrreducibleQQ(f: PolyQQ)`

where `f` is an object reference (`$input` or `objects[<id>]`) of kind `PolyQQ`.

## 3) Premises
Exactly one premise, of the form:

- `Degree(f, n)` with the same polynomial `f` as in the claim.

The verifier requires this premise and then applies the rule side-condition on `n`
(currently `n ∈ {2,3,4,5}` in the implemented checker).

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

Given `f` (decoded canonically as coefficients in descending degree order in \(\mathbb{Q}[x]\)):

1. Check there is a premise `Degree(f, n)` bound to the same `f` as the claim.
2. **Side condition:** require `n ∈ {2,3,4,5}`.
3. (Defensive check) Recompute `deg(f)` and require `deg(f) ∈ {2,3,4,5}` and consistency with the premise.
4. Let `u` be the leading coefficient of `f`. Form `f_m = f / u` (monicization).
5. Run the deterministic glass-box degree-≤5 factorization procedure:

   `factors = factorize_le5(f_m)`

   where the procedure returns a list of monic irreducible factors in \(\mathbb{Q}[x]\).
6. Accept iff `factors` is exactly the singleton list `[f_m]` (i.e., no non-trivial factors were found).

This rule is **computational** (`recompute-and-compare`): the verifier recomputes the decision procedure
locally and deterministically.

## 6) Failure codes

- `E_PREMISE_MISSING` — missing required `Degree(f,n)` premise.
- `E_PREMISE_BINDING` — degree premise does not bind to the same `f` (or is malformed).
- `E_TYPE` — claim shape or referenced object cannot be decoded canonically as `PolyQQ`.
- `E_SIDE_CONDITION` — degree is not in `{2,3,4,5}`.
- `E_EXCEPTION` — the deterministic procedure raised an exception (treated as verification failure).
- `E_NOT_IRREDUCIBLE` — a non-trivial factorization was found (i.e., `factorize_le5(f_m) != [f_m]`).

## 7) Fixtures

- OK: `fixtures/v3/le5-core@1/ok/irreducible.QQ.deg5_recompute@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/irreducible.QQ.deg5_recompute@1_fail_001.json`