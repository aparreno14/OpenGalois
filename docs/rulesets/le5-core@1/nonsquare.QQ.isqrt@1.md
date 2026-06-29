# Rule: `nonsquare.QQ.isqrt@1`

## 1) Rule id
`nonsquare.QQ.isqrt@1`

## 2) Claim
Proves a fact of the form:

- `NonSquareQQ(q: RatQQ)`

## 3) Premises
None.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

Let `q` be decoded canonically as a reduced fraction \(q = a/b\) with \(a \in \mathbb{Z}\), \(b \in \mathbb{Z}\),
\(b > 0\), and \(\gcd(a,b)=1\).

A rational number is a square in \(\mathbb{Q}\) iff it is nonnegative and both numerator and denominator are perfect squares in \(\mathbb{Z}\):
\[
q \in (\mathbb{Q})^2 \iff (a \ge 0) \wedge (a \in (\mathbb{Z})^2) \wedge (b \in (\mathbb{Z})^2).
\]

Therefore `NonSquareQQ(q)` holds iff:
\[
(a < 0) \vee (a \notin (\mathbb{Z})^2) \vee (b \notin (\mathbb{Z})^2).
\]

Verifier steps:

1. Decode `q` as \(a/b\) in lowest terms with \(b>0\).
2. If \(a < 0\), accept.
3. Otherwise compute exact integer square tests for \(a\) and \(b\) via `isqrt`.
4. Accept iff at least one of \(a\) or \(b\) is not a perfect square.

## 6) Failure codes
- `E_TYPE` — invalid claim shape or cannot decode `q`.
- `E_MISMATCH` — recomputation shows that `q` is actually a square in \(\mathbb{Q}\).

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/nonsquare.QQ.isqrt@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/nonsquare.QQ.isqrt@1_fail_001.json`
