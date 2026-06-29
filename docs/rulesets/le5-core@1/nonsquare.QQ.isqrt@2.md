# Rule: `nonsquare.QQ.isqrt@2`

## 1) Rule id

`nonsquare.QQ.isqrt@2`

## 2) Claim

Proves a fact of the form:

- `NonSquareQQ(q: RatQQ)`

where `q` is an object reference of kind `RatQQ`.

## 3) Premises

None.

## 4) Evidence

The rule carries compact explanatory evidence.

For a negative rational:

```json
{
  "obstruction": {
    "kind": "negative"
  }
}
```

For a positive rational whose reduced numerator or denominator is not a square:

```json
{
  "obstruction": {
    "kind": "integer_isqrt_interval",
    "side": "numerator",
    "previous_square": "16",
    "next_square": "25"
  }
}
```

The field `side` is either `numerator` or `denominator`.

## 5) Verifier algorithm

Let \(q=a/b\) be the decoded reduced fraction, with \(b>0\).

1. If \(a<0\), require evidence `{"obstruction":{"kind":"negative"}}` and accept.
2. Otherwise, read an `integer_isqrt_interval` obstruction.
3. Let \(n\) be either \(a\) or \(b\), according to `side`.
4. Compute \(r=\lfloor\sqrt n\rfloor\) exactly.
5. Require:
   \[
   \texttt{previous\_square}=r^2,
   \qquad
   \texttt{next\_square}=(r+1)^2.
   \]
6. Accept iff:
   \[
   r^2 < n < (r+1)^2.
   \]

This proves that the selected integer is not a square in \(\mathbb{Z}\). Since \(q\) is reduced,
a positive rational is a square in \(\mathbb{Q}\) if and only if both its numerator and denominator
are squares in \(\mathbb{Z}\).

## 6) Failure codes

- `E_TYPE` — malformed claim or referenced object.
- `E_MISMATCH` — the rational is actually a square in \(\mathbb{Q}\).
- `E_EVIDENCE` — malformed or incorrect evidence.
