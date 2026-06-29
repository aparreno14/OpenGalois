# Lemma kind: `irreducible.QQ`

## 1) Mathematical statement

This lemma certifies that a polynomial `f(x) ∈ Q[x]` is **irreducible over Q**.

The lemma is *procedure-based*: the verifier accepts the claim iff it can **replay a deterministic, exhaustive decision procedure** specified by the witness and confirm that no non-trivial factorization exists in `Q[x]`.

Scope:
- This lemma supports a restricted set of methods (see witness schema). Each method specifies the degrees it applies to.

## 2) Inputs / outputs

Inputs (normative):
- `inputs`: exactly one ref.
- The ref MUST resolve to a polynomial over `Q[x]`, either:
  - `$input`, or
  - an entry in `objects` with `kind = poly_qq_desc`.
- The resolved polynomial MUST have degree in the supported range of the selected method.

Outputs (normative):
- `outputs`: MUST be absent or an empty list.
- This lemma does not introduce new shared objects.

## 3) Witness schema

Witness MUST be a JSON object with:

- `method` (string, required): name of the irreducibility procedure.

Rules:
- Witness must be **structured data**, never “explanation text”.
- This lemma version stores no constant parameters in the witness.

### Supported methods (v2.0.0)

#### Method: `glassbox_le5`
Applies to degrees 2, 3, 4, 5 only.

Interpretation (informal summary):
- Degree 2: irreducible iff **no rational root exists** (Rational Root Test).
- Degree 3: irreducible iff **no rational root exists** (Rational Root Test).
- Degree 4: irreducible iff **no rational root exists** AND **no quadratic factor exists**.
- Degree 5: irreducible iff **no rational root exists** AND **no quadratic factor exists** (the only remaining reducible split without linears is 2+3).

#### Method: `trivial_linear`
Applies to degree 1 only.

Interpretation (informal summary):
- Degree 1 polynomials are irreducible over any field by definition.

**Verifier obligations for `trivial_linear`:**
1. Confirm that `deg(f) == 1`.
2. Accept the lemma immediately.

## 4) Verifier obligations

The verifier MUST:

### (A) Resolve and normalize input
1. Resolve the input ref to a polynomial `f ∈ Q[x]` with exact rational coefficients.
2. Confirm its degree is within the method scope.
3. Convert `f` to a primitive integer polynomial `g ∈ Z[x]`:
   - Clear denominators.
   - Divide by content so `content(g)=1`.
   - Normalize sign so `lc(g) > 0`.

All subsequent checks operate on `g`.

### (B) Method-specific obligations

#### For `method = glassbox_le5`

**B1. Rational root exclusion (degrees 2,3,4,5)**
4. If `deg(g) ∈ {2,3,4,5}`, perform the Rational Root Test exhaustively:
   - Enumerate all candidates `p/q` with `p | g(0)` and `q | lc(g)`, `q>0`.
   - Evaluate exactly in `Q`.
   - Reject the lemma if any candidate is a root.

**B2. Quadratic factor exclusion (degrees 4,5)**
5. If `deg(g) ∈ {4,5}`, perform an exhaustive Kronecker-style search for a quadratic factor in `Z[x]`:
   - The verifier MUST use the fixed evaluation points `[0, 1, -1]`.
   - Compute `v0=g(0)`, `v1=g(1)`, `v-1=g(-1)`.
   - Enumerate all triples `(d0,d1,dm1)` such that each divides the corresponding `v*` (including sign).
   - Reconstruct the unique quadratic `q(x)=ax^2+bx+c ∈ Z[x]` satisfying:
     - `q(0)=d0`, `q(1)=d1`, `q(-1)=dm1`
     - `a,b,c ∈ Z`, `a>0`
     - `gcd(|a|,|b|,|c|)=1`
     - `a` MUST divide `lc(g)` (Gauss lemma constraint)
   - Reject the lemma if any such `q` divides `g` exactly in `Q[x]`.

### (C) Accept
6. Accept the lemma iff all required sub-checks pass.

## 5) Failure modes

Recommended failure labels:
- `wrong_degree`
- `bad_witness.method`
- `has_rational_root`
- `has_quadratic_factor`
- `noncanonical_rational`
- `type_mismatch`

## 6) Notes / references

- The `glassbox_le5` method is intended for degree ≤ 5 workflows where reducibility patterns are limited:
  - deg 2: only 1+1
  - deg 3: only 1+2
  - deg 4: 1+3 or 2+2
  - deg 5: 1+4 or 2+3
- The verifier is responsible for replaying the exhaustive checks; the certificate does not store transcripts.
