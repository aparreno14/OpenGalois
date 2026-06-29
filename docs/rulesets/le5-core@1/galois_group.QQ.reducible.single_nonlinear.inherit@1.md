# Rule: `galois_group.QQ.reducible.single_nonlinear.inherit@1`

## 1) Rule id
`galois_group.QQ.reducible.single_nonlinear.inherit@1`

## 2) Claim
Proves a fact of the form:

- `GaloisGroup(f: PolyQQ, G: GroupId)`

by inheriting the already-verified factor-level group statement `GaloisGroup(g, G)` from the unique
non-linear irreducible factor that controls the splitting field.

## 3) Premises
This is a theorem rule. The verifier receives already-verified premises and must check that the rule
application contains the premises required by the theorem.

Required premises:

- `FactorizationMonicQQ(f, factors, unit)` with the same `f` as in the claim.
- For each **distinct factor reference** `h` occurring in `factors.items`, a verified premise
  `Degree(h, n_h)`.
- `IrreducibleQQ(g)` for the unique distinct factor `g` whose degree satisfies `n_g > 1`.
- `GaloisGroup(g, G)` for that same factor `g`, with the same `G` as in the claim.

This rule is intended for the reducible branch, so the certified factorization must contain at least
2 factor occurrences.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)
Suppose the certified factorization has the form

\[
f = u \cdot g^e \cdot l_1^{e_1} \cdots l_r^{e_r}
\]

where:

- `u ∈ Q^×`,
- `e ≥ 1`,
- `g` is irreducible and non-linear,
- every `l_i` is linear over `Q`.

Then the linear factors contribute only rational roots, and multiplicities do not enlarge the
splitting field. Hence

\[
\operatorname{Spl}(f) = \operatorname{Spl}(g).
\]

Therefore the Galois groups over `Q` are isomorphic:

\[
\operatorname{Gal}(f/\mathbf{Q}) \cong \operatorname{Gal}(g/\mathbf{Q}).
\]

This is the whole mathematical content of the rule. It transports the already-proved factor-level
Galois group to the reducible polynomial.

### 5.1 Why `IrreducibleQQ(g)` is explicit
The theorem is about the unique irreducible non-linear atom that governs the splitting field. A
non-linear factor of unknown reducibility would not be enough for a glass-box proof object. The
certificate should say explicitly that the controlling factor is irreducible.

### 5.2 Why the checker does not re-classify the group
The premise `GaloisGroup(g, G)` is already a verified fact. Its own rule has already proved that group
statement. The current theorem rule does not classify `g` again; it only checks that the inherited
premise is present and bound to the same `g` and the same `G`.

### 5.3 Degree coverage inside `le5-core@1`
Within the current project scope `deg(f) <= 5`, this abstract rule covers the reducible cores usually
written as:

- `[2]`,
- `[3]`,
- `[4]`.

It also covers repeated-factor situations such as a square of an irreducible quadratic, because
multiplicity does not change the splitting field.

The genuinely new compositum cases `[2,2]` and `[2,3]` are excluded: in those cases the splitting
field is not controlled by a single irreducible non-linear factor.

## 6) Verifier algorithm (normative)
1. Require the claim to be `GaloisGroup(f, G)`.
2. Require a verified premise `FactorizationMonicQQ(f, factors, unit)` bound to the same `f` as in the claim.
3. Decode `factors` as `PolyQQList` and require `len(factors.items) >= 2`.
4. Form the order-preserving list of distinct factor refs occurring in `factors.items`.
5. For each such factor ref `h`, require a verified premise `Degree(h, n_h)`.
6. Require that exactly one listed factor `g` satisfy `n_g > 1`, and that every remaining listed
   factor satisfy `Degree(l,1)`.
7. Require a verified premise `IrreducibleQQ(g)`.
8. Require a verified premise `GaloisGroup(g, G)` with the same group object `G` as in the claim.
9. Accept.

## 7) Failure codes
- `E_PREMISE_MISSING` — a required premise is absent.
- `E_PREMISE_BINDING` — a premise exists but does not bind to the required `f`, `g`, or `G`, or a
  required degree binding is wrong.
- `E_TYPE` — invalid claim shape or object decoding failure.
- `E_SIDE_CONDITION` — the certified factorization is not reducible, or it does not have exactly one
  distinct non-linear factor.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.reducible.single_nonlinear.inherit@1_001.json`
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.reducible.single_nonlinear.inherit@1_002.json`
  - `fixtures/v3/le5-core@1/ok/galois_group.QQ.reducible.single_nonlinear.inherit@1_003.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.reducible.single_nonlinear.inherit@1_fail_001.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.reducible.single_nonlinear.inherit@1_fail_002.json`
  - `fixtures/v3/le5-core@1/bad/galois_group.QQ.reducible.single_nonlinear.inherit@1_fail_003.json`
