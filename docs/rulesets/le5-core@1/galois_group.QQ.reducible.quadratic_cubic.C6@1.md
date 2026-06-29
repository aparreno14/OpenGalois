# Rule: `galois_group.QQ.reducible.quadratic_cubic.C6@1`

## 1) Rule id
`galois_group.QQ.reducible.quadratic_cubic.C6@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

## 3) Premises
Required premises:

- `FactorizationMonicQQ(f, factors, unit)` with the same `f` as in the claim.
- `Degree(q, 2)`.
- `IrreducibleQQ(q)`.
- `Degree(c, 3)`.
- `IrreducibleQQ(c)`.
- `DiscSquareQQ(c)`.

In addition, if `factors.items` contains any factor refs other than `q` and `c`, the checker requires a
verified premise `Degree(li, 1)` for each such extra **distinct** factor ref `li`.

The intended structural shape is therefore:

- exactly one distinct irreducible quadratic factor `q`,
- exactly one distinct irreducible cubic factor `c`,
- and all remaining distinct factors, if any, are linear.

Equivalently, this is the reducible core `[2,3] + linears` after ignoring multiplicities.
Repeated occurrences of `q` or `c` do not change the splitting field and do not change the branch.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let

\[
f(x)=q(x)^{e_q} c(x)^{e_c}\prod_i \ell_i(x) \in \mathbf{Q}[x]
\]

where `e_q, e_c >= 1`, where `q` is irreducible quadratic, where `c` is irreducible cubic, and where
all `\ell_i` are linear over `\mathbf{Q}`.

All linear factors split already over `\mathbf{Q}`, and repeating an irreducible factor does not enlarge
the splitting field. Hence the splitting field of `f` is exactly the splitting field of the square-free
quadratic-cubic core `q c`.

For this core the only possible groups are `C6`, `S3`, `D6`. In the present branch the cubic factor has
square discriminant, so its Galois group is `C3`. Adjoining the irreducible quadratic factor gives the
cyclic degree-6 compositum, hence `G ≅ C6`.

## 6) Verifier algorithm (normative)

1. Require a verified premise `FactorizationMonicQQ(f, factors, unit)` bound to the same `f` as in the claim.
2. Require verified premises `Degree(q,2)`, `IrreducibleQQ(q)`, `Degree(c,3)`, `IrreducibleQQ(c)`, and `DiscSquareQQ(c)`.
3. Decode `factors` as `PolyQQList`.
4. Form the list of **distinct** factor refs appearing in `factors.items`.
5. Require that among those distinct refs:
   - exactly one factor `q` has degree `2`,
   - exactly one factor `c` has degree `3`,
   - every remaining distinct factor `li` satisfies `Degree(li,1)`.
6. Decode `G` canonically as `GroupId` with `system="smallgroup"` and require `(G.order, G.index) = (6, 1)`.
7. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a required premise exists but does not bind to the intended `f`, `q`, or `c`.
- `E_SIDE_CONDITION` — the factorization does not have exactly one distinct quadratic, exactly one distinct cubic, and all remaining distinct factors linear after ignoring multiplicities.
- `E_TYPE` — invalid claim shape or referenced objects cannot be decoded canonically.
- `E_GROUP_MISMATCH` — `G` is not `C6` in the SmallGroup catalog.
