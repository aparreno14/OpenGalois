# Ruleset `le5-core@1` — Fact Catalog

This document defines the fact predicates supported by the ruleset `le5-core@1`.

The corresponding machine-readable catalog is:

```text
rulesets/le5-core@1/facts.yaml
```

Object encodings are documented in:

```text
docs/objects.md
```

---

## 1. Supported object kinds

`le5-core@1` uses the following object kinds:

- `PolyQQ`;
- `MPolyQQ`;
- `RatQQ`;
- `PolyQQList`;
- `RadicalExpr`;
- `RadicalExprList`;
- `GroupId`;
- `IntZ`.

---

## 2. Predicates

### `IrreducibleQQ(f: PolyQQ)`

`f` is irreducible in `Q[x]`.

Typical proving rules include:

- `irreducible.QQ.deg1_trivial@1`;
- `irreducible.QQ.zassenhaus_trace@1`;
- `irreducible.QQ.deg5_recompute@1`;
- `irreducible.QQ.dummit_resolvent@1`;
- `irreducible.QQ.to.depressed_monic@1`.

---

### `FactorizationMonicQQ(f: PolyQQ, factors: PolyQQList, unit: RatQQ)`

`f = unit * product_i factors[i]` in `Q[x]`, where every factor is monic and non-constant. Duplicates encode multiplicity.

Typical proving rule:

- `factorization.QQ.monic@1`.

---

### `DepressedMonicEq(f: PolyQQ, g: PolyQQ)`

`g` is the depressed-monic normalization of `f` over `Q`, according to the conventions fixed by this ruleset.

Typical proving rule:

- `normalize.depressed_monic_QQ@1`.

---

### `GaloisGroup(f: PolyQQ, G: GroupId)`

The Galois group of `f` over `Q` is isomorphic to `G`.

Typical proving rules include:

- `galois_group.QQ.deg1.trivial@1`;
- `galois_group.QQ.deg2.C2@1`;
- `galois_group.QQ.deg3.C3@1`;
- `galois_group.QQ.deg3.S3@1`;
- `galois_group.QQ.deg4.*`;
- `galois_group.QQ.deg5.*`;
- `galois_group.QQ.reducible.*`;
- `galois_group.QQ.lift.depressed_monic@1`.

---

### `SolvableByRadicals(f: PolyQQ)`

`f` is solvable by radicals over `Q`.

Typical proving rule:

- `solvable_by_radicals.QQ.from_galois_group@1`.

---

### `NonSolvableByRadicals(f: PolyQQ)`

`f` is not solvable by radicals over `Q`.

Typical proving rule:

- `nonsolvable_by_radicals.QQ.from_galois_group@1`.

---

### `RadicalRoots(f: PolyQQ, roots: RadicalExprList)`

`roots` is the canonical ordered list of roots of `f` expressed by radicals under the rule-specific scheme.

The order of roots is normative. Equality of radical expressions is structural equality of their canonical `RadicalExpr` payloads, not arbitrary algebraic equivalence.

Typical proving rules include:

- `radical_roots.QQ.deg1.trivial@1`;
- `radical_roots.QQ.deg2.quadratic_formula@1`;
- `radical_roots.QQ.deg3.cardano.depressed_monic@1`;
- `radical_roots.QQ.deg3.cardano.depressed_monic@2`;
- `radical_roots.QQ.deg4.ferrari.depressed_monic@1`;
- `radical_roots.QQ.deg4.ferrari.depressed_monic@2`;
- `radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1`;
- `radical_roots.QQ.deg5.mcclintock.depressed_monic@1`;
- `radical_roots.QQ.lift.depressed_monic@1`;
- `radical_roots.QQ.reducible.compose@1`;
- `radical_roots.QQ.reducible.compose@2`.

See also:

```text
docs/rulesets/le5-core@1/radical_expr_canonicality.md
```

---

### `Degree(f: PolyQQ, n: IntZ)`

`n` is the degree of `f`.

Typical proving rule:

- `degree.QQ@1`.

---

### `Discriminant(f: PolyQQ, D: RatQQ)`

`D` is the discriminant of `f`.

Ruleset-local convention: if `deg(f) = 1`, then `Disc(f) = 1`.

Typical proving rule:

- `disc.QQ.compute@1`.

---

### `SqrtQQ(q: RatQQ, k: RatQQ)`

`k` is a rational square root of `q`, i.e. `k^2 = q`.

Typical proving rule:

- `sqrt.QQ.check@1`.

---

### `IsSquareQQ(q: RatQQ)`

`q` is a square in `Q`.

Typical proving rule:

- `is_square.QQ.lift@1`.

---

### `NonSquareQQ(q: RatQQ)`

`q` is not a square in `Q`.

Typical proving rules:

- `nonsquare.QQ.isqrt@1`;
- `nonsquare.QQ.isqrt@2`.

---

### `DiscSquareQQ(f: PolyQQ)`

The discriminant of `f` is a square in `Q`.

Typical proving rule:

- `disc.square.QQ.lift@1`.

---

### `DiscNonSquareQQ(f: PolyQQ)`

The discriminant of `f` is not a square in `Q`.

Typical proving rule:

- `disc.nonsquare.QQ.lift@1`.

---

### `ResolventQQ(R: PolyQQ, f: PolyQQ, p: MPolyQQ)`

`R` is the specialized resolvent over `Q` of the multivariate invariant `p` at `f`.

Concrete proving rules certify specific resolvent families, including:

- quartic cubic resolvents;
- Dummit's sextic quintic resolvent.

Typical proving rules:

- `resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1`;
- `resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1`;
- `resolvent.QQ.compute.deg5.sextic_dummit_F20@1`.

---

## 3. Implemented rule ids

The reference verifier implements the rules listed in the compiled ruleset under:

```text
src/opengalois/rulesets/le5_core_1.py
```

Human-readable rule documentation is under:

```text
docs/rulesets/le5-core@1/
```

The ruleset includes, among others:

```text
degree.QQ@1
disc.QQ.compute@1
factorization.QQ.monic@1
normalize.depressed_monic_QQ@1
irreducible.QQ.zassenhaus_trace@1
galois_group.QQ.deg4.S4@2
galois_group.QQ.deg4.A4@2
galois_group.QQ.deg4.V4@3
galois_group.QQ.deg5.S5@1
galois_group.QQ.deg5.A5@1
galois_group.QQ.deg5.F20@1
galois_group.QQ.deg5.D5@1
galois_group.QQ.deg5.C5@1
solvable_by_radicals.QQ.from_galois_group@1
nonsolvable_by_radicals.QQ.from_galois_group@1
radical_roots.QQ.deg5.mcclintock.depressed_monic@1
```

For the complete source of truth, inspect the compiled ruleset and the corresponding rule documents.
