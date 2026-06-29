# Rule: `solvable_by_radicals.QQ.from_galois_group@1`

## 1) Rule id
`solvable_by_radicals.QQ.from_galois_group@1`

## 2) Claim
Proves a fact of the form:

- `SolvableByRadicals(f: PolyQQ)`

## 3) Premises
Exactly one premise is required:

- `GaloisGroup(f, G)` with the same `f` as in the claim.

This is a **theorem-style** rule. The verifier does not recompute the Galois group and does not inspect how the premise `GaloisGroup(f,G)` was obtained. It consumes an already-verified group classification and checks whether the certified group is resoluble.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `L` be the splitting field of `f` over `Q` and let `G = Gal(L/Q)`.

A polynomial over `Q` is solvable by radicals exactly when its Galois group is a **resoluble group**. Here, a finite group `G` is called resoluble if it admits a subnormal series

\[
1 = G_0 \triangleleft G_1 \triangleleft \cdots \triangleleft G_n = G
\]

such that each factor `G_{i+1}/G_i` is abelian. In all groups supported by this rule, the series may be refined so that each factor is cyclic of prime order.

The corresponding field-theoretic tower is the inverse tower of fixed fields

\[
Q = L^G \subseteq L^{G_{n-1}} \subseteq \cdots \subseteq L^{G_1} \subseteq L^{G_0} = L,
\]

and every successive extension has abelian Galois group. This is the group-theoretic content used by the rule.

### 5.1 Why degrees at most 4 are always in the solvable branch
For the groups that occur in `le5-core@1` up to degree `4`, every possibility is resoluble:

- `Trivial`, `C2`, `C3`, `C4`, `C5`, `C6`, and `V4` are abelian.
- `S3` is resoluble since
  \[
  1 \triangleleft A_3 \triangleleft S_3,
  \]
  with factors `C3` and `C2`.
- `D4` is resoluble since
  \[
  1 \triangleleft C_2 \triangleleft V_4 \triangleleft D_4,
  \]
  with factors `C2`, `C2`, `C2`.
- `A4` is resoluble since
  \[
  1 \triangleleft C_2 \triangleleft V_4 \triangleleft A_4,
  \]
  with factors `C2`, `C2`, `C3`.
- `S4` is resoluble since
  \[
  1 \triangleleft C_2 \triangleleft V_4 \triangleleft A_4 \triangleleft S_4,
  \]
  with factors `C2`, `C2`, `C3`, `C2`.

Thus, in the range covered by OpenGalois up to degree `4`, group classification never leaves the solvable-by-radicals branch.

### 5.2 The resoluble groups that still occur in degree 5
In degree `5`, the supported resoluble transitive groups are `C5`, `D5`, and `F20`:

- `C5` is abelian.
- `D5` is resoluble since
  \[
  1 \triangleleft C_5 \triangleleft D_5,
  \]
  with factors `C5` and `C2`.
- `F20` is resoluble since
  \[
  1 \triangleleft C_5 \triangleleft D_5 \triangleleft F_{20},
  \]
  with factors `C5`, `C2`, `C2`.

### 5.3 Reducible branches
The reducible groups emitted by `le5-core@1` are also resoluble:

- `Trivial`, `C2`, `V4`, and `C6` are abelian.
- `S3` is resoluble as above.
- `D6` (the dihedral group of order `12`) is resoluble since
  \[
  1 \triangleleft C_3 \triangleleft C_6 \triangleleft D_6,
  \]
  with factors `C3`, `C2`, `C2`.

## 6) Verifier algorithm (normative)

1. Require the claim to be `SolvableByRadicals(f)`.
2. Require a verified premise `GaloisGroup(f,G)` bound to the same `f`.
3. Decode `G` canonically as `GroupId(system="smallgroup")`.
4. Accept exactly for the following SmallGroup identifiers:
   - `Trivial = (1,1)`
   - `C2 = (2,1)`
   - `C3 = (3,1)`
   - `S3 = (6,2)`
   - `V4 = (4,2)`
   - `C4 = (4,1)`
   - `D4 = (8,3)`
   - `A4 = (12,3)`
   - `S4 = (24,12)`
   - `C5 = (5,1)`
   - `D5 = (10,2)`
   - `F20 = (20,3)`
   - `C6 = (6,1)`
   - `D6 = (12,4)`
5. If the certified group is one of the supported non-resoluble groups (`A5`, `S5`), reject with `E_GROUP_NOT_RESOLUBLE`.
6. Otherwise reject with `E_GROUP_UNSUPPORTED`.

## 7) Failure codes
- `E_PREMISE_MISSING` — the required `GaloisGroup(f,G)` premise is absent.
- `E_PREMISE_BINDING` — a `GaloisGroup` premise exists but is malformed.
- `E_TYPE` — invalid claim shape or the referenced group object cannot be decoded canonically.
- `E_GROUP_NOT_RESOLUBLE` — the certified group is supported by the ruleset but is not resoluble.
- `E_GROUP_UNSUPPORTED` — the certified group is not among the supported groups recognized by this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/solvable_by_radicals.QQ.from_galois_group@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/solvable_by_radicals.QQ.from_galois_group@1_fail_001.json`
