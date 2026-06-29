# Rule: `radical_roots.QQ.deg5.mcclintock.depressed_monic@1`

## 1) Rule id
`radical_roots.QQ.deg5.mcclintock.depressed_monic@1`

## 2) Claim
Proves a fact of the form:

- `RadicalRoots(g: PolyQQ, roots: RadicalExprList)`

for an irreducible quintic polynomial `g` treated under the canonical depressed-monic
McClintock scheme of `le5-core@1`.

## 3) Premises
Exactly five premises are required:

- `Degree(g, 5)` with the same polynomial `g` as in the claim.
- `IrreducibleQQ(g)` with the same polynomial `g`.
- `DepressedMonicEq(f, g)` for some polynomial `f`.
- `ResolventQQ(R, g, p)` where `p` is the canonical multivariate polynomial
  for Dummit's `F20` sextic resolvent family.
- `FactorizationMonicQQ(R, factors, unit)` for the same sextic resolvent `R`.

## 4) Evidence
None.

## 5) Theoretical justification
Write
\[
g(t)=t^5+10Ct^3+10Dt^2+5Et+f.
\]

For the canonical Dummit sextic resolvent family, a solvable irreducible depressed quintic
admits a rational linear factor in the resolvent. This rule uses that factorization as the
certificate-level entry point for the McClintock reconstruction.

The verifier:

- scans the certified factorization of the Dummit sextic resolvent,
- locates a certified monic linear factor,
- extracts its rational root \(\theta\),
- and recomputes the unique canonical McClintock radical output for `g`.

The internal case split of the scheme (`general`, `R1 = 0`, `S = C`, `S = 0`, `S = T = 0`,
`S = C = 0`) is **not** exposed at the logical level as separate rules or separate premises.
It is entirely internal to the recomputation scheme.

## 6) Canonical radical scheme (normative)
The canonical ordered radical list is the one returned by the rule-local McClintock builder for
depressed quintics:

- it starts from the rational sextic-resolvent root extracted from the certified linear factor,
- it follows the rule-local internal branch policy,
- it emits one fixed AST shape per branch,
- and comparison is by exact structural equality of canonical `RadicalExpr` payloads.

This rule does **not** accept algebraically equivalent but differently shaped ASTs.

The rule also keeps the OpenGalois philosophy that all non-rational quantities are represented
as ASTs. Rational computations may guide the branch selection, but no non-rational quantity is
numerically evaluated.

## 7) Verifier algorithm (normative)
1. Require verified premises `Degree(g,5)`, `IrreducibleQQ(g)`, and `DepressedMonicEq(f,g)` for some `f`.
2. Require a verified premise `ResolventQQ(R,g,p)` for the same `g`, with `p` equal to the canonical `MPolyQQ` for the Dummit `F20` sextic family.
3. Require a verified premise `FactorizationMonicQQ(R, factors, unit)` for the same sextic resolvent `R`.
4. Require `unit = 1`.
5. Scan `factors.items` in order and locate a monic linear factor of `R`.
6. Extract its rational root `theta`.
7. Decode `g` canonically and defensively require exact form `t^5 + 10 C t^3 + 10 D t^2 + 5 E t + f`.
8. Recompute the canonical ordered radical list for `g` by running the depressed-monic McClintock builder on `(g, theta)`.
9. Decode the claimed `RadicalExprList` and compare it to the recomputed list by exact structural equality of `RadicalExpr` payloads.
10. Accept.

## 8) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is malformed or not bound as required.
- `E_TYPE` — invalid claim shape, object decoding failure, or invalid `RadicalExprList` payload.
- `E_SIDE_CONDITION` — the recomputed polynomial is not a monic depressed quintic.
- `E_BAD_RESOLVENT_FAMILY` — the resolvent premise uses the wrong degree-5 family.
- `E_BAD_FACTORIZATION` — the certified factorization does not supply a usable monic linear factor with unit `1`.
- `E_EXCEPTION` — the internal McClintock builder raised unexpectedly.
- `E_MISMATCH` — the claimed radical root list does not equal the canonical McClintock list for this rule.

## 9) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg5.mcclintock.depressed_monic@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg5.mcclintock.depressed_monic@1_fail_001.json`
