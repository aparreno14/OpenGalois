# Lemma kind: `normalize.depressed_monic_QQ`

## 1) Mathematical statement

Given a polynomial \(f(x) \in \mathbb{Q}[x]\) of degree \(n\ge 1\) with leading coefficient \(a_n\neq 0\), there exists a unique rational number

    t = a_{n-1} / (n a_n)

such that the translated and scaled polynomial

    g(x) = (1/a_n) * f(x - t)

is **monic** and **depressed**, i.e. the coefficient of \(x^{n-1}\) in \(g\) is 0.

This lemma node certifies the exact computation of \(g\) and records the witness \(t\) and \(a_n\).

## 2) Inputs / outputs

Inputs (normative):

- `inputs`: exactly one polynomial reference.
  - `{ "ref": "$input" }` denotes the top-level input polynomial, encoded by `certificate.input`.

Outputs (normative):

- `outputs`: exactly one reference to an object in `certificate.objects`.
- The referenced object MUST have `kind = "poly_qq_desc"` and represent \(g(x)\) in descending coefficients.

Witness (normative):

`witness` MUST be a JSON object containing:

- `tschirnhaus_shift`: a canonical rational string, equal to \(t\)
- `monic_scale`: a canonical rational string, equal to \(a_n\)

Additional witness fields MAY be present, but verifiers MUST ignore them unless specified here in a future revision.

## 3) Verification obligations

Let the input polynomial be

    f(x) = a_n x^n + a_{n-1} x^{n-1} + ... + a_0.

A verifier MUST perform the following checks exactly in \(\mathbb{Q}\):

1. Resolve the input polynomial coefficients \(a_i\) and degree \(n\).
2. Parse `monic_scale` as a rational and check `monic_scale == a_n`.
3. Form the monic polynomial \(f_m(x) = f(x)/a_n\).
4. Compute

       t = (coeff of x^{n-1} in f_m) / n

   and check it equals `tschirnhaus_shift`.
5. Compute the translated polynomial

       g(x) = f_m(x - t)

   by exact polynomial translation.
6. Resolve the output object (from `outputs[0].ref`) as a `poly_qq_desc` object and check its coefficients match \(g\) exactly.
7. Enforce the structural invariants of the normalization result:
   - \(g\) is monic (leading coefficient is 1)
   - the coefficient of \(x^{n-1}\) in \(g\) is 0

Failure of any check rejects the certificate.

## 4) Degree policy

- This lemma is **optional at the schema level**.
- Applications may require it as part of a conformance set (e.g. for degree 5 workflows).
- For degrees < 5, generators MAY omit this lemma; verifiers must not assume its presence unless a conformance set requires it.

## 5) Notes

- Uniqueness: the shift \(t\) is uniquely determined by the input polynomial.
- The translation convention is \(x \mapsto x - t\). If a future variant uses \(x \mapsto x + t\), it MUST be a different lemma kind.
