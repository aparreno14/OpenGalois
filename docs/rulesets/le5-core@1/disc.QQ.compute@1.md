# Rule: `disc.QQ.compute@1`

## 1) Rule id
`disc.QQ.compute@1`

## 2) Claim
Proves a fact of the form:

- `Discriminant(f: PolyQQ, D: RatQQ)`

## 3) Premises
None.

## 4) Evidence
None.

## 5) Verifier algorithm (normative)

Let `f(x) = a_n x^n + ... + a_0` be the polynomial decoded canonically in \(\mathbb{Q}[x]\)
from the referenced `PolyQQ` object (or `$input`). Let \(n = \deg(f)\).

**Convention (ruleset-local):** if \(n = 1\), define \(\mathrm{Disc}(f) = 1\).

For \(n \ge 2\), compute the discriminant via the resultant with the derivative:

\[
\mathrm{Disc}(f) \,=\, (-1)^{n(n-1)/2}\,\frac{\mathrm{Res}(f, f')}{a_n}.
\]

Here \(f'\) is the formal derivative of \(f\), and \(\mathrm{Res}(f,g)\) is the **resultant**, 
the determinant of the Sylvester matrix \(S(f,g)\).

### 5.1 Resultant via Sylvester determinant (normative)

Let \(m = \deg(f)\) and \(k = \deg(g)\). The Sylvester matrix \(S(f,g)\) is the
\((m+k)\times(m+k)\) matrix formed by:

- the first \(k\) rows: shifted coefficient rows of \(f\),
- the next \(m\) rows: shifted coefficient rows of \(g\),

using the descending-degree coefficient vectors of \(f\) and \(g\).

Then:

\[
\mathrm{Res}(f,g) = \det(S(f,g)).
\]

The verifier MUST compute this determinant **exactly** over \(\mathbb{Q}\).

### 5.2 Acceptance condition (normative)

1. Decode `f` canonically as a `PolyQQ`.
2. Decode `D` canonically as a `RatQQ`.
3. Recompute \(D_\mathrm{expected} = \mathrm{Disc}(f)\) exactly as above (using the convention
   \(\deg(f)=1 \Rightarrow \mathrm{Disc}(f)=1\)).
4. Accept iff `D == D_expected` as rationals in canonical form (exact equality in \(\mathbb{Q}\)).

## 6) Failure codes
- `E_TYPE` — invalid claim shape or cannot decode `f` / `D`.
- `E_EXCEPTION` — internal computation failure (derivative/resultant/determinant).
- `E_MISMATCH` — claimed discriminant does not match the recomputed discriminant.

## 7) Fixtures
- OK: `fixtures/v3/le5-core@1/ok/disc.QQ.compute@1_001.json`
- BAD: `fixtures/v3/le5-core@1/bad/disc.QQ.compute@1_fail_001.json`
