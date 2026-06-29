# Rule: `normalize.depressed_monic_QQ@1`

## 1) Rule id
`normalize.depressed_monic_QQ@1`

## 2) Claim
Proves a fact of the form:

- `DepressedMonicEq(f: PolyQQ, g: PolyQQ)`

where `f` is typically `$input` and `g` is an object id of kind `PolyQQ`.

## 3) Premises
Exactly one premise, of the form:

- `Degree(f, n)` with the same polynomial `f` as in the claim.

The verifier requires this premise and then applies the rule side-condition on `n`
(currently `n ∈ {2,3,4,5}` in the implemented checker).

## 4) Evidence (required)
An object with the following fields:

- `monic_scale`: canonical rational string equal to `lc(f)`.
- `tschirnhaus_shift`: canonical rational string `t` defined by:
  - Let `f_m = f / lc(f)` (monic), `n = deg(f_m)`.
  - `t = (coeff of x^(n-1) in f_m) / n`.

## 5) Verifier algorithm (normative)

Given `f` and `g` decoded canonically in \(\mathbb{Q}[x]\):

1. Check there is a premise `Degree(f, n)` bound to the same `f` as the claim.
2. **Side condition:** require `n ∈ {2,3,4,5}`.
3. (Defensive check) Recompute `deg(f)` and require `deg(f) ∈ {2,3,4,5}` and consistency with the premise.
4. Let `a_n = lc(f)` and check `evidence.monic_scale == a_n`.
5. Compute `f_m = f / a_n`.
6. Compute `t_expected = (coeff of x^(n-1) in f_m) / n` and check `evidence.tschirnhaus_shift == t_expected`.
7. Recompute `g_expected(x) = f_m(x - t_expected)` exactly.
8. Check that `g` matches `g_expected` exactly.
9. Additionally enforce:
   - `lc(g) = 1` (monic),
   - the coefficient of `x^(n-1)` in `g` is `0` (depressed).

This rule is a **verify-evidence** rule: the verifier recomputes the normalization using the supplied parameters and checks equality.

## 6) Failure codes
- `E_PREMISE_MISSING` — missing required `Degree(f,n)` premise.
- `E_PREMISE_BINDING` — degree premise does not bind to the same `f` (or is malformed).
- `E_TYPE` — invalid claim shape or cannot decode PolyQQ arguments.
- `E_SIDE_CONDITION` — degree not in `{2,3,4,5}`.
- `E_EVIDENCE` — missing/invalid evidence or mismatch against recomputed values.
- `E_EXCEPTION` — arithmetic/shift construction failed.
- `E_CONSTRUCTION_MISMATCH` — recomputed polynomial does not match claimed `g`.
- `E_NOT_MONIC` — `g` is not monic.
- `E_NOT_DEPRESSED` — `x^(n-1)` coefficient of `g` is not 0.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/normalize.depressed_monic_QQ@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/normalize.depressed_monic_QQ@1_fail_001.json`