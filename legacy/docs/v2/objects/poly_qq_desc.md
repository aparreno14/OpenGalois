# Object kind: `poly_qq_desc`

## 1) Meaning

An object of kind `poly_qq_desc` represents a polynomial

    f(x) = a_n x^n + a_{n-1} x^{n-1} + ... + a_1 x + a_0

with coefficients in \(\mathbb{Q}\), encoded in **descending degree order**.

This object is intended to be consumed by proof lemmas that operate in \(\mathbb{Q}[x]\).

## 2) Canonical encoding

An object of this kind MUST be a JSON object containing:

- `kind`: the constant string `"poly_qq_desc"`
- `degree`: an integer `n >= 0`
- `coeffs_qq`: an array of length `n+1` of canonical rational strings

Additional fields MAY be present, but verifiers MUST ignore them unless a specific lemma contract states otherwise.

### 2.1 Coefficient array

`coeffs_qq = [a_n, a_{n-1}, ..., a_0]`

Normative constraints:

- length is exactly `degree + 1`
- `a_n != 0` (no leading zero; except the zero polynomial is not representable by this kind)
- each entry is a canonical rational string (see `docs/verification.md`, §4.3)
- the string `"-0"` is forbidden

## 3) Equality

Two `poly_qq_desc` objects are equal iff:

- their `degree` fields are equal, and
- their `coeffs_qq` arrays are identical entry-wise as canonical rationals (equivalently: as strings).

Because rationals are canonical, string equality is sufficient after schema and canonicality checks.

## 4) Notes and edge cases

- Constant polynomials have `degree = 0` and `coeffs_qq` of length 1.
- Zero polynomial is intentionally excluded (it would violate `a_n != 0`).
  If zero is needed, introduce a separate object kind (e.g., `zero_poly`) or represent it as a constant polynomial only if you allow `a_0 = "0"` with `degree = 0` (but then leading nonzero still fails).
