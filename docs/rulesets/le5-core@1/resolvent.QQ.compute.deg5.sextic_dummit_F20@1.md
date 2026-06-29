# Rule: `resolvent.QQ.compute.deg5.sextic_dummit_F20@1`

## 1) Rule id
`resolvent.QQ.compute.deg5.sextic_dummit_F20@1`

## 2) Claim
Proves a fact of the form:

- `ResolventQQ(R: PolyQQ, g: PolyQQ, p: MPolyQQ)`

## 3) Premises
Exactly one premise:

- `Degree(g, 5)` with the same `g` as in the claim.

No irreducibility premise is required.

This is intentional: in OpenGalois, a computational resolvent rule should certify the
**construction** of the resolvent polynomial itself, not mix that construction with later
classification facts such as irreducibility, rational roots, solvability, or final Galois group.

## 4) Evidence
None.

## 5) What this rule computes, and why it exists
This rule certifies the degree-5 sextic resolvent used by Dummit for the solvable-quintic branch.

The fixed multivariate polynomial `p` is the element

\
x_1^2 x_2 x_5 + x_1^2 x_3 x_4 + x_2^2 x_1 x_3 + x_2^2 x_4 x_5
+ x_3^2 x_1 x_5 + x_3^2 x_2 x_4 + x_4^2 x_1 x_2 + x_4^2 x_3 x_5
+ x_5^2 x_1 x_4 + x_5^2 x_2 x_3,
\

whose stabilizer in `S5` is the Frobenius group `F20`.

Dummit's Theorem 1 shows that, for an **irreducible** quintic, the associated resolvent sextic
has a rational root if and only if the quintic is solvable by radicals. OpenGalois should not
collapse all of that mathematics into one monolithic checker: this rule only certifies the
underlying resolvent polynomial `R`. Later rules may consume `ResolventQQ(...)` together with
factorization and discriminant facts to classify the Galois group.

## 6) Design note: why the claim is over a depressed-monic quintic
Dummit's explicit sextic formula is written only after translating to the depressed form

\
g(x) = x^5 + p x^3 + q x^2 + r x + s.
\

Accordingly, this rule proves `ResolventQQ(R, g, p)` for such a quintic `g`, not directly for
an arbitrary quintic `f`. In OpenGalois terms, that keeps the fact semantics honest:
`ResolventQQ(R, g, p)` should refer to the polynomial that the checker actually uses.

The checker therefore requires:

- the degree premise `Degree(g,5)`,
- monicity of `g`,
- vanishing `x^4` coefficient (depressed form),
- and exact equality of `p` with the canonical `MPolyQQ` family above.

## 7) Verifier algorithm (normative)
Given `R`, `g`, and `p` decoded canonically:

1. Check there is a verified premise `Degree(g, 5)` bound to the same `g` as in the claim.
2. Decode `R` canonically as a `PolyQQ`.
3. Decode `g` canonically as a `PolyQQ`.
4. Decode `p` canonically as an `MPolyQQ`.
5. Require `p` to be exactly the canonical `MPolyQQ` for the Dummit `F20` sextic family.
6. Require `g` to be monic.
7. Require the coefficient of `x^4` in `g` to be `0`.
8. Write
   \
   g(x)=x^5 + p x^3 + q x^2 + r x + s.
   \
9. Recompute the sextic `f20(x)` exactly in `QQ[x]` by Dummit's formula:
   \
   f_{20}(x) = x^6 + 8 r x^5 + (2 p q^2 - 6 p^2 r + 40 r^2 - 50 q s) x^4
   + (-2 q^4 + 21 p q^2 r - 40 p^2 r^2 + 160 r^3 - 15 p^2 q s - 400 q r s + 125 p s^2) x^3
   + (p^2 q^4 - 6 p^3 q^2 r - 8 q^4 r + 9 p^4 r^2 + 76 p q^2 r^2 - 136 p^2 r^3 + 400 r^4
      - 50 p q^3 s + 90 p^2 q r s - 1400 q r^2 s + 625 q^2 s^2 + 500 p r s^2) x^2
   + (-2 p q^6 + 19 p^2 q^4 r - 51 p^3 q^2 r^2 + 3 q^4 r^2 + 32 p^4 r^3 + 76 p q^2 r^3
      - 256 p^2 r^4 + 512 r^5 - 31 p^3 q^3 s - 58 q^5 s + 117 p^4 q r s + 105 p q^3 r s
      + 260 p^2 q r^2 s - 2400 q r^3 s - 108 p^5 s^2 - 325 p^2 q^2 s^2 + 525 p^3 r s^2
      + 2750 q^2 r s^2 - 500 p r^2 s^2 + 625 p q s^3 - 3125 s^4) x
   + (q^8 - 13 p q^6 r + p^5 q^2 r^2 + 65 p^2 q^4 r^2 - 4 p^6 r^3 - 128 p^3 q^2 r^3 + 17 q^4 r^3
      + 48 p^4 r^4 - 16 p q^2 r^4 - 192 p^2 r^5 + 256 r^6 - 4 p^5 q^3 s - 12 p^2 q^5 s
      + 18 p^6 q r s + 12 p^3 q^3 r s - 124 q^5 r s + 196 p^4 q r^2 s + 590 p q^3 r^2 s
      - 160 p^2 q r^3 s - 1600 q r^4 s - 27 p^7 s^2 - 150 p^4 q^2 s^2 - 125 p q^4 s^2
      - 99 p^5 r s^2 - 725 p^2 q^2 r s^2 + 1200 p^3 r^2 s^2 + 3250 q^2 r^2 s^2
      - 2000 p r^3 s^2 - 1250 p q r s^3 + 3125 p^2 s^4 - 9375 r s^4).
   \
10. Accept iff the claimed `R` equals the recomputed sextic exactly in `QQ[x]`.

## 8) Failure codes
- `E_PREMISE_MISSING` — missing required `Degree(g,5)` premise.
- `E_PREMISE_BINDING` — degree premise does not bind to the same `g`, or is malformed.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_P_MISMATCH` — `p` is not the fixed canonical `MPolyQQ` for Dummit's `F20` family.
- `E_NOT_MONIC` — `g` is not monic.
- `E_NOT_DEPRESSED` — the coefficient of `x^4` in `g` is not `0`.
- `E_EXCEPTION` — arithmetic or coefficient unpacking raised an exception during recomputation.
- `E_MISMATCH` — the claimed sextic does not match the recomputed sextic.

## 9) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/resolvent.QQ.compute.deg5.sextic_dummit_F20@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/resolvent.QQ.compute.deg5.sextic_dummit_F20@1_fail_001.json`
