# Rule: `resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1`

## 1) Rule id
`resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1`

## 2) Claim
Proves a fact of the form:

- `ResolventQQ(R: PolyQQ, f: PolyQQ, p: MPolyQQ)`

## 3) Premises
Exactly one premise:

- `Degree(f, 4)` with the same `f` as in the claim.

## 4) Evidence
None.

## 5) Mathematical meaning
This rule certifies the cubic resolvent attached to the quartic family determined by

\[
p=(x_1+x_2)(x_3+x_4).
\]

The rule is independent of any later use of this resolvent. In particular, it does
**not** assume that the quartic is irreducible or already in depressed form.

If the monic quartic associated to `f` is
\[
f_m(X)=X^4+aX^3+bX^2+cX+d,
\]
then the specialized cubic resolvent for this family is
\[
R_3(X)=X^3-2bX^2+(b^2+ac-4d)X+(a^2d-abc+c^2).
\]
When `f` is already depressed, i.e. `a=0`, this becomes
\[
R_3(X)=X^3-2bX^2+(b^2-4d)X+c^2,
\]
which is the classical cubic resolvent used in the quartic radical constructions.

## 6) Verifier algorithm (normative)

1. Check there exists a verified premise `Degree(f, 4)` bound to the same `f` as in the claim.
2. Decode `R` canonically as a `PolyQQ`.
3. Decode `f` canonically as a `PolyQQ`.
4. Decode `p` canonically as an `MPolyQQ`.
5. Require that `p` is exactly the canonical multivariate polynomial
   \[
   (x_1+x_2)(x_3+x_4)=x_1x_3+x_1x_4+x_2x_3+x_2x_4.
   \]
6. Let `lc(f)` be the leading coefficient of `f`. Form the monic quartic
   \[
   f_m(X)=\frac{f(X)}{\operatorname{lc}(f)}=X^4+aX^3+bX^2+cX+d.
   \]
7. Recompute the cubic resolvent
   \[
   R_3(X)=X^3-2bX^2+(b^2+ac-4d)X+(a^2d-abc+c^2).
   \]
8. Accept iff the claimed `R` agrees exactly with the recomputed polynomial in `QQ[X]`.

This rule is computational (`recompute-and-compare`): the verifier monicizes the quartic
internally, recomputes the cubic resolvent by the explicit quartic formula, and checks
exact equality.

## 7) Failure codes
- `E_PREMISE_MISSING` — missing required `Degree(f,4)` premise.
- `E_PREMISE_BINDING` — degree premise does not bind to the same `f`, or is malformed.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_SIDE_CONDITION` — the decoded polynomial is not quartic.
- `E_P_MISMATCH` — `p` is not the fixed canonical `MPolyQQ` for `(x1+x2)(x3+x4)`.
- `E_EXCEPTION` — arithmetic raised an exception during recomputation.
- `E_MISMATCH` — the claimed resolvent does not match the recomputed cubic resolvent.

## 8) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1_fail_001.json`
