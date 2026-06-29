# Resolvents

Resolvents are one of the central tools used by OpenGalois to convert questions about permutation groups into exact arithmetic tests over `Q`.

The guiding principle is:

> a carefully chosen polynomial expression in the roots has a stabilizer in `S_n`; arithmetic information about its specialized resolvent detects whether the Galois group lies in that stabilizer.

---

## 1. Group action on expressions in the roots

Let `p` be a polynomial in variables `x1, ..., xn`, and let `S_n` act by permuting the variables.

The stabilizer of `p` is:

```text
Stab(p) = { sigma in S_n : sigma(p) = p }.
```

The orbit of `p` is:

```text
O_p = { sigma(p) : sigma in S_n }.
```

The orbit size is:

```text
|O_p| = [S_n : Stab(p)].
```

Thus a choice of `p` selects a subgroup of `S_n` through its stabilizer.

---

## 2. Universal resolvent

The universal resolvent attached to `p` is:

```text
R_p(T) = product_{q in O_p} (T - q).
```

Although each `q` is a polynomial in the formal roots, the coefficients of `R_p` are symmetric in the roots. Therefore they can be expressed in the elementary symmetric polynomials.

This is what makes specialization possible.

---

## 3. Specialized resolvent

Let `f` be a degree `n` polynomial over `Q`, with roots `alpha_1, ..., alpha_n`.

The specialized resolvent is obtained by evaluating the universal resolvent at those roots:

```text
R_{f,p}(T) = product_{q in O_p} (T - q(alpha_1, ..., alpha_n)).
```

It lies in `Q[T]`.

In OpenGalois, the fact

```text
ResolventQQ(R, f, p)
```

means that `R` is this specialized resolvent of `p` at `f`.

The predicate is general. Concrete rules certify specific families of `p`.

---

## 4. Why resolvents detect Galois groups

If a value `q(alpha)` lies in the base field, then the Galois group fixes that value. Equivalently, the Galois group is contained in the stabilizer of that value, up to conjugacy.

Thus:

- rational roots of a resolvent indicate subgroup containment;
- factorization patterns of a resolvent encode orbit decompositions;
- square discriminants detect containment in alternating groups.

The verifier does not reason from vague subgroup language. It checks concrete certified facts such as:

```text
ResolventQQ(R, f, p)
IrreducibleQQ(R)
FactorizationMonicQQ(R, factors, unit)
DiscSquareQQ(f)
DiscNonSquareQQ(f)
```

Then theorem rules use these facts to certify the final group.

---

## 5. Discriminant as a resolvent

Let

```text
delta = product_{i<j} (x_i - x_j)
```

A transposition sends `delta` to `-delta`. Therefore the orbit is `{delta, -delta}` and the associated resolvent is:

```text
T^2 - Delta
```

where `Delta = delta^2` is the discriminant.

After specialization, the classical criterion is recovered:

```text
Gal(f) is contained in A_n iff Disc(f) is a square in the base field.
```

OpenGalois represents this information through facts such as:

```text
Discriminant(f, D)
DiscSquareQQ(f)
DiscNonSquareQQ(f)
```

---

## 6. Degree 4: pair-sums cubic resolvent

For quartics, OpenGalois uses the pair-sums invariant

```text
p = (x1 + x2)(x3 + x4).
```

Its orbit has three elements, corresponding to the three pairings of four roots:

```text
(x1+x2)(x3+x4)
(x1+x3)(x2+x4)
(x1+x4)(x2+x3)
```

The stabilizer of one such value has order 8 and is isomorphic to `D4`.

For a monic quartic

```text
f(X) = X^4 + aX^3 + bX^2 + cX + d,
```

the associated cubic resolvent is:

```text
R_S(T) = T^3 - 2b T^2 + (b^2 + ac - 4d)T + (a^2 d - abc + c^2).
```

This is the resolvent used by the current degree-4 `@2` classification rules and by the quartic radical rules.

The branch structure is:

- irreducible resolvent plus non-square discriminant gives `S4`;
- irreducible resolvent plus square discriminant gives `A4`;
- complete splitting of the resolvent in the square-discriminant branch gives `V4`;
- one rational root in the non-square branch leaves `C4` versus `D4`, resolved by Kappe--Warren square tests.

---

## 7. Degree 5: Dummit's sextic resolvent

For irreducible quintics, OpenGalois uses Dummit's sextic resolvent to detect the Frobenius subgroup `F20`.

The relevant group-theoretic point is:

```text
|S5| / |F20| = 120 / 20 = 6.
```

Thus a suitable invariant with stabilizer `F20` has an orbit of size 6. The corresponding specialized resolvent is sextic.

In the OpenGalois classification pipeline:

- irreducibility gives a transitive subgroup of `S5`;
- the discriminant square test distinguishes containment in `A5`;
- Dummit's sextic resolvent detects containment in a conjugate of `F20`;
- Dummit's auxiliary quadratic criterion separates `D5` from `C5` inside the solvable branch.

The relevant current rule ids include:

```text
resolvent.QQ.compute.deg5.sextic_dummit_F20@1
galois_group.QQ.deg5.S5@1
galois_group.QQ.deg5.A5@1
galois_group.QQ.deg5.F20@1
galois_group.QQ.deg5.D5@1
galois_group.QQ.deg5.C5@1
```

---

## 8. Certificate role

Resolvents are useful in proof-carrying computation because they isolate explicit objects:

- a multivariate invariant `p`;
- a specialized polynomial `R`;
- arithmetic properties of `R`, such as factorization or irreducibility.

OpenGalois records these as ordinary objects and facts. The group-theoretic conclusion is then certified by a rule whose premises are explicit and independently checkable.

This separates:

- mathematical theory: why the resolvent detects subgroup information;
- computation: how the resolvent and its arithmetic properties are certified;
- explanation: how the proof is rendered for a human.
