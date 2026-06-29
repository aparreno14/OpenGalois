# Lemma kind: `classify.galois_group.irreducible.deg1`

## 1) Mathematical statement

This lemma certifies the (unique) Galois group of a **degree-1** polynomial over \(\mathbb{Q}\).

Let \(f(x) \in \mathbb{Q}[x]\) with \(\deg(f)=1\). Then the splitting field of \(f\) over \(\mathbb{Q}\) is \(\mathbb{Q}\) itself, hence the Galois group is the **trivial group**.

This lemma is intended as the **terminal classification lemma** for irreducible degree-1 workflows.

## 2) Inputs / outputs

Inputs (normative):

- `inputs`: exactly one polynomial reference.
  - `{ "ref": "$input" }` denotes the top-level polynomial in `certificate.input`.
  - Otherwise, the ref MUST resolve to an object in `certificate.objects` with `kind = "poly_qq_desc"`.

Outputs (normative):

- `outputs` MUST be absent or an empty list.
- This lemma does not introduce shared objects.

Children (premises):

- `children` MAY be present, but this lemma does not require any specific premises.
  - Applications may choose to include an `irreducible.QQ` premise with method `trivial_linear` as part of a conformance profile.
  - Verifiers MUST NOT assume such a premise exists unless a conformance set/profile requires it.

## 3) Witness schema

Witness (normative):

- `witness` MUST be a JSON object with exactly the following keys:
  - `group` (string, required): MUST equal `"TRIVIAL"`.

No other witness keys are allowed in v2.0.0 for this lemma kind.

Rationale:
- The group is mathematically fixed for \(\deg=1\), but the explicit label provides a stable machine-readable output.

## 4) Verifier obligations

Let the input polynomial be \(f\).

A verifier MUST:

1. Resolve the input ref to an exact polynomial in \(\mathbb{Q}[x]\).
2. Check that \(\deg(f) = 1\) (i.e., the coefficient list has length 2 after trimming leading zeros).
3. Check that the leading coefficient is non-zero (i.e., \(f\) is not the zero polynomial).
4. Check `witness.group == "TRIVIAL"`.
5. Accept the lemma.

No further algebraic computation is required.

## 5) Failure modes

A verifier SHOULD report failure under one of these labels (names are recommendations):

- `inputs.shape`: `inputs` is not a 1-element list
- `inputs.ref`: missing/invalid ref
- `type_mismatch`: ref does not resolve to a polynomial over \(\mathbb{Q}\)
- `degree_mismatch`: resolved polynomial does not have degree 1
- `zero_polynomial`: input is the zero polynomial
- `witness.shape`: witness is missing or not an object
- `witness.keys`: witness keys are not exactly `{ "group" }`
- `witness.group`: witness group label is not `"TRIVIAL"`

## 6) Notes / references

- Degree-1 polynomials are irreducible over any field by definition.
- Field theory fact used: the splitting field of a linear polynomial over \(\mathbb{Q}\) is \(\mathbb{Q}\) itself, hence the Galois group is trivial.