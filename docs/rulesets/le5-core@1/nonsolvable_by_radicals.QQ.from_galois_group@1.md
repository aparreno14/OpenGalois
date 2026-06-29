# Rule: `nonsolvable_by_radicals.QQ.from_galois_group@1`

## 1) Rule id
`nonsolvable_by_radicals.QQ.from_galois_group@1`

## 2) Claim
Proves a fact of the form:

- `NonSolvableByRadicals(f: PolyQQ)`

## 3) Premises
Exactly one premise is required:

- `GaloisGroup(f, G)` with the same `f` as in the claim.

This is a **theorem-style** rule. The verifier does not recompute the Galois group and does not inspect how the premise `GaloisGroup(f,G)` was obtained. It consumes an already-verified group classification and checks whether the certified group is non-resoluble.

## 4) Evidence
None.

## 5) Theoretical justification (normative notes)

Let `L` be the splitting field of `f` over `Q` and let `G = Gal(L/Q)`.

A polynomial over `Q` is not solvable by radicals exactly when its Galois group is **not** resoluble. In the range covered by `le5-core@1`, the only supported non-resoluble groups are `A5` and `S5`.

### 5.1 Why `A5` is not resoluble
The alternating group `A5` is a non-abelian simple group. Therefore it admits no non-trivial normal series with abelian successive quotients, and hence it is not resoluble.

### 5.2 Why `S5` is not resoluble
The subgroup `A5` is normal in `S5` with index `2`, so
\[
A_5 \triangleleft S_5, \qquad S_5/A_5 \cong C_2.
\]
If `S5` were resoluble, then every subgroup of `S5` would also be resoluble; in particular `A5` would be resoluble. This is impossible by §5.1. Hence `S5` is not resoluble.

### 5.3 Why this phenomenon first appears in degree 5
All groups supported by `le5-core@1` in degrees at most `4` are resoluble, and the reducible groups supported by the ruleset are resoluble as well. The failure of solvability by radicals appears only when the classification reaches the non-abelian simple group `A5`, and therefore also `S5`.

## 6) Verifier algorithm (normative)

1. Require the claim to be `NonSolvableByRadicals(f)`.
2. Require a verified premise `GaloisGroup(f,G)` bound to the same `f`.
3. Decode `G` canonically as `GroupId(system="smallgroup")`.
4. Accept exactly for the following SmallGroup identifiers:
   - `A5 = (60,5)`
   - `S5 = (120,34)`
5. If the certified group is one of the supported resoluble groups of `le5-core@1`, reject with `E_GROUP_RESOLUBLE`.
6. Otherwise reject with `E_GROUP_UNSUPPORTED`.

## 7) Failure codes
- `E_PREMISE_MISSING` — the required `GaloisGroup(f,G)` premise is absent.
- `E_PREMISE_BINDING` — a `GaloisGroup` premise exists but is malformed.
- `E_TYPE` — invalid claim shape or the referenced group object cannot be decoded canonically.
- `E_GROUP_RESOLUBLE` — the certified group is supported by the ruleset and is resoluble.
- `E_GROUP_UNSUPPORTED` — the certified group is not among the supported groups recognized by this rule.

## 8) Fixtures
- OK:
  - `fixtures/v3/le5-core@1/ok/nonsolvable_by_radicals.QQ.from_galois_group@1_001.json`
- BAD:
  - `fixtures/v3/le5-core@1/bad/nonsolvable_by_radicals.QQ.from_galois_group@1_fail_001.json`
