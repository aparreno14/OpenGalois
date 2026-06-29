# Ruleset `le5-core@1` — Fact Catalog (Normative)

This document defines the **fact predicates** supported by the ruleset `le5-core@1`.

## 1. Supported object kinds

This ruleset uses the v3 canonical object kinds (see `docs/spec/v3/objects.md`):

- `PolyQQ`
- `MPolyQQ`
- `RatQQ`
- `PolyQQList`
- `RadicalExpr`
- `RadicalExprList`
- `GroupId`
- `IntZ`

## 2. Predicates

### 2.1 `IrreducibleQQ(f: PolyQQ)`

**Meaning:** `f` is irreducible in \(\mathbb{Q}[x]\).

**Typical proving rule:** `irreducible.QQ.deg5_recompute@1` (planned).

---

### 2.2 `FactorizationMonicQQ(f: PolyQQ, factors: PolyQQList, unit: RatQQ)`

**Meaning:** \(f = u \cdot \prod_i g_i\) in \(\mathbb{Q}[x]\), where:

- `unit` encodes \(u \in \mathbb{Q}^\times\),
- each factor \(g_i\) is a non-constant **monic** polynomial,
- multiplicity is significant.

**Multiplicity encoding (normative):**
`PolyQQList.items` MAY contain duplicates, and duplicates encode multiplicity.
For example, `["poly:g1","poly:g1","poly:g2"]` means \(g_1^2 g_2\).

**Typical proving rule:** `factorization.QQ.monic@1` (planned).

---

### 2.3 `DepressedMonicEq(f: PolyQQ, g: PolyQQ)`

**Meaning:** `g` is the **depressed-monic normalization** of `f` over \(\mathbb{Q}\),
according to the conventions fixed by this ruleset.

At minimum, `g` MUST satisfy:
- \(\mathrm{lc}(g)=1\) (monic),
- the coefficient of \(x^{n-1}\) is 0 (depressed), for \(n=\deg(g)\).

**Typical proving rule:** `normalize.depressed_monic_QQ@1` (planned), with rule-defined evidence
encoding the shift/scale parameters.

---

### 2.4 `GaloisGroup(f: PolyQQ, G: GroupId)`

**Meaning:** The **Galois Group** of `f` over \(\mathbb{Q}\) is isomorphic to `G`.

---


### 2.5 `SolvableByRadicals(f: PolyQQ)`

**Meaning:** `f` is solvable by radicals over \(\mathbb{Q}\).

**Typical proving rule:** `solvable_by_radicals.QQ.from_galois_group@1` (planned).

**Normative notes:**
- This predicate is about solvability by radicals over the base field \(\mathbb{Q}\).
- In `le5-core@1`, this fact is intended to be derived from a verified
  `GaloisGroup(f, G)` fact by a theorem rule whose checker recognizes the
  supported **resoluble** groups of the ruleset.

---

### 2.6 `NonSolvableByRadicals(f: PolyQQ)`

**Meaning:** `f` is not solvable by radicals over \(\mathbb{Q}\).

**Typical proving rule:** `nonsolvable_by_radicals.QQ.from_galois_group@1` (planned).

**Normative notes:**
- This predicate is about non-solvability by radicals over the base field \(\mathbb{Q}\).
- In `le5-core@1`, this fact is intended to be derived from a verified
  `GaloisGroup(f, G)` fact by a theorem rule whose checker recognizes the
  supported **non-resoluble** groups of the ruleset.

---

### 2.7 `RadicalRoots(f: PolyQQ, roots: RadicalExprList)`

**Meaning:** `roots` is the canonical ordered list of roots of `f` expressed by radicals under the rule-specific scheme.

**Normative notes:**
- The order of `roots` is **normative**.
- The canonical shape of the expressions in `roots` is rule-specific.
- Equality of radical expressions is **structural exact equality** of the canonical `RadicalExpr`
  payloads, not algebraic equivalence of arbitrary radical formulas.
- The verifier checks kind-level well-formedness of `RadicalExpr` and `RadicalExprList`; any
  stronger mathematical interpretation belongs to the proving rule.

**Typical proving rules:** scheme-specific `radical_roots.QQ.*` rules (planned), including
`radical_roots.QQ.deg3.cardano.depressed_monic@1`,
`radical_roots.QQ.deg4.ferrari.depressed_monic@1`,
`radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1`, and
`radical_roots.QQ.lift.depressed_monic@1`.

See also `docs/rulesets/le5-core@1/radical_expr_canonicality.md` for the
canonical AST policy used by `RadicalRoots`.

---

### 2.8 `Degree(f: PolyQQ, n: IntZ)`


**Meaning:** `n` is the degree of the polynomial `f`.

**Typical proving rule:** `degree.QQ@1`.

---

### 2.9 `Discriminant(f: PolyQQ, D: RatQQ)`

**Meaning:** `D` is the discriminant of the polynomial `f`.

**Typical proving rule:** `disc.QQ.compute@1`.

**Convention (ruleset-local):** if \(\deg(f)=1\), define \(\mathrm{Disc}(f)=1\).

---

### 2.10 `SqrtQQ(q: RatQQ, k: RatQQ)`

**Meaning:** `k` is a rational square root of `q` in \(\mathbb{Q}\), i.e. \(k^2=q\).

**Typical proving rule:** `sqrt.QQ.check@1`.

---

### 2.11 `IsSquareQQ(q: RatQQ)`
 
**Meaning:** `q` is a square in \(\mathbb{Q}\), i.e. there exists \(k\in\mathbb{Q}\) such that \(k^2 = q\).
 
**Typical proving rule:** `is_square.QQ.lift@1` (derived from `SqrtQQ(q,k)`).
 
---

### 2.12 `NonSquareQQ(q: RatQQ)`

**Meaning:** `q` is not a square in \(\mathbb{Q}\).

**Typical proving rule:** `nonsquare.QQ.isqrt@1`.

---

### 2.13 `DiscSquareQQ(f: PolyQQ)`

**Meaning:** The discriminant of `f` is a square in \(\mathbb{Q}\).

**Typical proving rule:** `disc.square.QQ.lift@1`.

---

### 2.14 `DiscNonSquareQQ(f: PolyQQ)`

**Meaning:** The discriminant of `f` is not a square in \(\mathbb{Q}\).

**Typical proving rule:** `disc.nonsquare.QQ.lift@1`.

---

### 2.15 `ResolventQQ(R: PolyQQ, f: PolyQQ, p: MPolyQQ)`

**Meaning:** `R` is the **specialized resolvent** over \(\mathbb{Q}\) of `p` at `f`.

More precisely, let \(f \in \mathbb{Q}[t]\) be a polynomial of degree \(n\), let
\(\alpha=(\alpha_1,\dots,\alpha_n)\) be an enumeration of its roots in a splitting field, and let
\(p \in \mathbb{Q}[x_1,\dots,x_n]\). If

\[
O_p=\{\widetilde{\sigma}(p): \sigma\in S_n\}
\]

denotes the orbit of \(p\) under the natural action of \(S_n\), then the specialized resolvent of
\(p\) at \(f\) is the polynomial

\[
R_{f,p}(t)=\prod_{q\in O_p}(t-q(\alpha)).
\]

The fact `ResolventQQ(R, f, p)` asserts exactly that

\[
R = R_{f,p}.
\]

**Normative notes:**

- The predicate itself does **not** encode side conditions such as irreducibility, separability,
  or compatibility between degree and variable count.
- Compatibility conditions such as \(\deg(f)=n\) and `p.nvars = n` belong to the proving rule, not
  to the fact statement itself.
- The third argument `p` is a multivariate polynomial over \(\mathbb{Q}\), represented canonically
  as `MPolyQQ`.
- This predicate is mathematical and general; concrete proving rules MAY certify only specific
  instances (for example, fixed quartic families such as `x1*x2 + x3*x4` or `(x1+x2)(x3+x4)`).

---

## 3. Planned rules (rule ids)

The following rule ids are intended to be supported by verifiers claiming support for `le5-core@1`:

- `irreducible.QQ.deg5_recompute@1`
- `factorization.QQ.monic@1`
- `normalize.depressed_monic_QQ@1`
- `irreducible.QQ.deg1_trivial@1`
- `galois_group.QQ.deg1.trivial@1`
- `degree.QQ@1`
- `galois_group.QQ.deg2.C2@1`
- `disc.QQ.compute@1`
- `sqrt.QQ.check@1`
- `is_square.QQ.lift@1`
- `disc.square.QQ.lift@1`
- `disc.nonsquare.QQ.lift@1`
- `galois_group.QQ.deg3.C3@1`
- `galois_group.QQ.deg3.S3@1`
- `resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1`
- `resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1`
- `galois_group.QQ.deg4.S4@1`
- `galois_group.QQ.deg4.S4@2`
- `galois_group.QQ.deg4.A4@1`
- `galois_group.QQ.deg4.A4@2`
- `galois_group.QQ.deg4.V4@1`
- `galois_group.QQ.deg4.V4@2`
- `galois_group.QQ.deg4.V4@3`
- `galois_group.QQ.deg4.C4@1`
- `galois_group.QQ.deg4.C4@2`
- `galois_group.QQ.deg4.D4.w1@1`
- `galois_group.QQ.deg4.D4.w1@2`
- `galois_group.QQ.deg4.D4.w2@1`
- `galois_group.QQ.deg4.D4.w2@2`
- `galois_group.QQ.reducible.all_linear.trivial@1`
- `galois_group.QQ.reducible.single_nonlinear.inherit@1`
- `galois_group.QQ.reducible.double_quadratic.C2@1`
- `galois_group.QQ.reducible.double_quadratic.V4@1`
- `galois_group.QQ.reducible.quadratic_cubic.C6@1`
- `galois_group.QQ.reducible.quadratic_cubic.S3@1`
- `galois_group.QQ.reducible.quadratic_cubic.D6@1`
- `galois_group.QQ.reducible.quadratic_cubic.S3@2`
- `galois_group.QQ.reducible.quadratic_cubic.D6@2`
- `resolvent.QQ.compute.deg5.sextic_dummit_F20@1`
- `galois_group.QQ.deg5.S5@1`
- `galois_group.QQ.deg5.A5@1`
- `galois_group.QQ.deg5.F20@1`
- `galois_group.QQ.deg5.D5@1`
- `galois_group.QQ.deg5.C5@1`
- `galois_group.QQ.lift.depressed_monic@1`
- `irreducible.QQ.dummit_resolvent@1`
- `solvable_by_radicals.QQ.from_galois_group@1`
- `nonsolvable_by_radicals.QQ.from_galois_group@1`
- `radical_roots.QQ.reducible.compose@1`
- `radical_roots.QQ.reducible.compose@2`
- `radical_roots.QQ.deg1.trivial@1`
- `radical_roots.QQ.deg2.quadratic_formula@1`
- `radical_roots.QQ.deg3.cardano.depressed_monic@1`
- `radical_roots.QQ.deg3.cardano.depressed_monic@2`
- `radical_roots.QQ.deg4.ferrari.depressed_monic@1`
- `radical_roots.QQ.deg4.ferrari.depressed_monic@2`
- `radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1`
- `radical_roots.QQ.deg5.mcclintock.depressed_monic@1`
- `radical_roots.QQ.lift.depressed_monic@1`
- `irreducible.QQ.to.depressed_monic@1`

Verifiers MUST clearly document which of these rules they implement; certificates using rules that a given verifier does not implement SHOULD be rejected by that verifier.




## 4. Degree-four pair-sums classification rules

The degree-four Galois-group rules with version `@2` use the canonical pair-sums
resolvent family

\[
p=(x_1+x_2)(x_3+x_4).
\]

For a monic quartic

\[
f(X)=X^4+aX^3+bX^2+cX+d,
\]

the associated cubic resolvent is

\[
R_S(T)=T^3-2bT^2+(b^2+ac-4d)T+(a^2d-abc+c^2).
\]

In the Kappe--Warren branch, if \(s_0\) is the rational root of this resolvent,
then \(r_0=b-s_0\), and OpenGalois checks

\[
w_1=(a^2-4s_0)\Delta,\qquad
w_2=((b-s_0)^2-4d)\Delta.
\]
