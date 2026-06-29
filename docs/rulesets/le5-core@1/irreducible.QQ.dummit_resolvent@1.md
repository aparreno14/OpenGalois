# Rule: `irreducible.QQ.dummit_resolvent@1`

## 1) Rule id
`irreducible.QQ.dummit_resolvent@1`

## 2) Claim
Proves a fact of the form:

- `IrreducibleQQ(R: PolyQQ)`

for a sextic resolvent `R` belonging to Dummit's `F20` resolvent family attached to an irreducible quintic `f`.

## 3) Premises
Exactly three premises:

- `Degree(f, 5)`.
- `IrreducibleQQ(f)`.
- `ResolventQQ(R, f, p)`.

The claim polynomial `R` must be the same polynomial as the first argument of the `ResolventQQ` premise.
The quintic `f` appearing in the degree and irreducibility premises must be the same quintic as the second argument of that `ResolventQQ` premise.
The third argument `p` of the `ResolventQQ` premise must be the canonical `MPolyQQ` object for Dummit's `F20` sextic-resolvent family.

This is a **specialized computational rule**. It is not the generic irreducibility rule for arbitrary polynomials over `QQ`. Its scope is intentionally narrow: it certifies irreducibility only for the Dummit sextic resolvent attached to an irreducible quintic.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(X) \in \mathbf{Q}[X]
\]

be irreducible of degree `5`, and let

\[
R(X) = f_{20}(X)
\]

be Dummit's sextic resolvent attached to the `F20`-stabilized expression

\[
p = x_1^2x_2x_5 + x_1^2x_3x_4 + x_2^2x_1x_3 + x_2^2x_4x_5
  + x_3^2x_1x_5 + x_3^2x_2x_4 + x_4^2x_1x_2 + x_4^2x_3x_5
  + x_5^2x_1x_4 + x_5^2x_2x_3.
\]

The purpose of this rule is to certify `IrreducibleQQ(R)` by exploiting a property that is specific to this resolvent family.

### 5.1 Dummit's solvability criterion for the sextic resolvent

Dummit proves that for an irreducible quintic `f`, the sextic resolvent `f_{20}` has a rational root if and only if `f` is solvable by radicals. Moreover, in the solvable case, the sextic resolvent factors over `Q` as the product of one linear factor and one irreducible quintic factor.

So, within this family, the existence of a rational root is not just a weak reducibility witness: it is exactly the gateway to the soluble `1 + 5` factorization pattern.

### 5.2 Why absence of a rational root is enough here

This rule is **not** using the false general principle

\[
\text{"no rational root"} \Rightarrow \text{"irreducible"}
\]

for arbitrary sextics.
It uses a family-specific fact: Dummit's sextic is the degree-6 resolvent attached to the six conjugates of the `F20`-stabilized expression above. For an irreducible quintic, the reducible branch relevant to Theorem 1 is precisely the soluble `1 + 5` branch detected by a rational root. Therefore, inside this specific resolvent family, ruling out rational roots is exactly the criterion needed by OpenGalois to certify `IrreducibleQQ(R)`.

In other words, the rule is justified by the special structure of Dummit's resolvent, not by a generic statement about arbitrary degree-6 polynomials.

### 5.3 Why the rule requires `Degree(f,5)` and `IrreducibleQQ(f)`

The theory above is stated for **irreducible quintics**. If `f` were not irreducible, the transitive-subgroup classification branch would no longer apply, and the special `1 + 5` consequence for the sextic resolvent would not be the correct criterion. That is why this rule explicitly requires both:

- `Degree(f,5)`, and
- `IrreducibleQQ(f)`.

### 5.4 OpenGalois design notes

This rule is intentionally narrow and reusable:

- it does **not** attempt to be a generic degree-6 irreducibility checker;
- it does **not** require a separate factorization fact for the sextic;
- it does **not** introduce a new fact for “has/no rational root”.

Instead, it consumes an already-certified `ResolventQQ(R,f,p)` premise, verifies that `p` is exactly Dummit's `F20` family, and then runs an exact rational-root test on `R`. This lets OpenGalois certify irreducibility for the sextic resolvent without first extending the general-purpose irreducibility pipeline to arbitrary degree `6`.

## 6) Verifier algorithm (normative)

1. Require the claim to be `IrreducibleQQ(R)`.
2. Require a verified premise `ResolventQQ(R,f,p)` bound to that same claim polynomial `R`.
3. Require that `p` is exactly the canonical `MPolyQQ` object for Dummit's `F20` sextic-resolvent family.
4. Require a verified premise `Degree(f,5)` for that same quintic `f`.
5. Require a verified premise `IrreducibleQQ(f)` for that same quintic `f`.
6. Decode `R` canonically as a `PolyQQ` in descending coefficients.
7. Run an exact rational-root test over `Q` on `R`.
8. If a rational root exists, reject.
9. Otherwise accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but is not bound to the intended `R` or `f`.
- `E_BAD_RESOLVENT_FAMILY` — the `ResolventQQ` premise is not attached to the canonical Dummit `F20` family.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_SIDE_CONDITION` — the rational-root test found a rational root, so the rule cannot certify irreducibility.

## 8) References
- D. S. Dummit, *Solving Solvable Quintics*, Mathematics of Computation 57 (1991), no. 195, 387–401. In particular, Theorem 1 and the discussion of the sextic resolvent `f20`.
