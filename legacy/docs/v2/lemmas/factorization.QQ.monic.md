# Lemma kind: `factorization.QQ.monic`

## 1) Mathematical statement

This lemma certifies an exact factorization in \(\mathbb{Q}[x]\) of the form:

    f(x) = u * Π_i f_i(x)^{m_i}

where:

- \(u \in \mathbb{Q}^\times\) is a non-zero rational unit,
- each \(f_i(x)\) is a **monic** polynomial in \(\mathbb{Q}[x]\) of degree at least 1,
- each \(m_i\) is a positive integer multiplicity.

The list of factors is treated as a multiset: order is irrelevant.

## 2) Inputs / outputs

Inputs (normative):

- `inputs`: exactly one polynomial reference (often `$input`).

Outputs:

- This lemma does not need outputs; it can be omitted.
- If future versions want to expose the factor list as a shared object, that MUST be a different object kind and/or lemma kind.
- `outputs` MUST NOT contain `{ "ref": "$input" }`.

Witness (normative):

`witness` MUST be a JSON object containing:

- `unit`: a canonical **non-zero** rational string
- `factors`: an array of factor entries, each with:
  - `ref`: object id of a polynomial object in `certificate.objects`
  - `multiplicity`: positive integer (if omitted by a generator, verifiers MUST treat it as 1)

The referenced factor objects MUST have:

- `kind = "poly_qq_desc"`
- leading coefficient equal to 1 (monic)
- degree >= 1 (non-constant)

## 3) Verification obligations

Let the input polynomial be \(f\). The verifier MUST:

1. Resolve the input polynomial coefficients as an exact polynomial in \(\mathbb{Q}[x]\).
2. Parse `unit` as an exact rational and reject if it is 0.
3. For each factor entry:
   - resolve the factor object via `ref`,
   - check object kind is `poly_qq_desc`,
   - check leading coefficient is exactly 1,
   - check degree >= 1,
   - read multiplicity `m_i` (default 1).
4. Compute the product \(P = Π_i f_i^{m_i}\) in \(\mathbb{Q}[x]\).
5. Compute \(uP\) and check exact equality with the input polynomial \(f\).

A verifier MAY accept any factor order. It MUST reject if any reference is missing or ill-typed.

## 4) Notes

- This lemma does not claim irreducibility of the factors, only that the product equals the input.
- If irreducibility certificates are required, they must be expressed via additional lemma kinds.
