# Rule: `irreducible.QQ.zassenhaus_trace@1`

## 1) Rule id

`irreducible.QQ.zassenhaus_trace@1`

## 2) Claim

Proves a fact of the form:

- `IrreducibleQQ(f: PolyQQ)`

where `f` is an object reference (`$input` or `objects[<id>]`) of kind `PolyQQ`.

## 3) Premises

Exactly one required premise:

- `Degree(f, n)`

with the same polynomial `f` as in the claim and `n in {2,3,4,5}`.

## 4) Evidence

The evidence records the modular trace used to start the Zassenhaus computation:

```json
{
  "prime": "3",
  "ell": 5,
  "mod_p_factorization": {
    "factors_desc": [
      ["1", "1"],
      ["1", "0", "2"],
      ["1", "2", "2"]
    ]
  }
}
```

Fields:

- `prime`: the good prime \(p\).
- `ell`: the Hensel precision exponent \(\ell\). If the modular factorization is already irreducible, `ell = 0`.
- `mod_p_factorization.factors_desc`: the irreducible factorization of the primitive integer model modulo \(p\), using descending coefficients in \(\{0,\dots,p-1\}\).

No Hensel-lifted factors are serialized. The current implementation lifts recombination pairs internally during the subset search, so there is no canonical global list of lifted factors to expose.

## 5) Verifier algorithm

Given `f`:

1. Decode `f` as a polynomial in \(\mathbb{Q}[x]\).
2. Require a matching `Degree(f,n)` premise with \(n \in \{2,3,4,5\}\).
3. Construct the primitive integer model \(F \in \mathbb{Z}[x]\).
4. Decode `prime` and require it to be the deterministic good Zassenhaus prime chosen for \(F\).
5. Factor \(F \bmod p\) in \(\mathbb{F}_p[x]\).
6. Require the recomputed modular factorization to match `mod_p_factorization.factors_desc`.
7. Recompute the Hensel precision exponent \(\ell\). If \(F \bmod p\) is irreducible, require `ell = 0`; otherwise require the exponent used by the deterministic bound \(p^\ell > 2B\).
8. Replay the deterministic degree-bounded Zassenhaus recombination procedure.
9. Accept iff no recombination gives a proper divisor of \(F\).

## 6) Mathematical justification

The primitive integer model preserves irreducibility over \(\mathbb{Q}\). A good prime gives a square-free factorization of \(F \bmod p\). Zassenhaus recombination states that, once the factors are lifted to sufficiently high \(p\)-adic precision, every proper factor of \(F\) must arise from a recombination of the lifted modular factors. The verifier enumerates all recombinations of degree at most \(\lfloor n/2 \rfloor\); this is enough because any proper factor of larger degree has a complementary proper factor of smaller degree.

If no such recombination divides \(F\) exactly in \(\mathbb{Z}[x]\), then \(F\) is irreducible in \(\mathbb{Z}[x]\), hence \(f\) is irreducible in \(\mathbb{Q}[x]\).

## 7) Failure codes

- `E_TYPE`
- `E_PREMISE_MISSING`
- `E_PREMISE_BINDING`
- `E_SIDE_CONDITION`
- `E_EVIDENCE`
- `E_EXCEPTION`
- `E_NOT_IRREDUCIBLE`
