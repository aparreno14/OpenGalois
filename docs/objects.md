# OpenGalois v3 Objects (Canonical Encodings)

This document specifies canonical encodings for object kinds used by OpenGalois v3 certificates.
It is normative unless explicitly marked as non-normative.

## 1. Object store model

A certificate MAY include an `objects` map:

```json
"objects": {
  "<object_id>": { "kind": "<KindName>", ...payload... }
}
```

Objects exist to share derived mathematical entities across multiple facts and to anchor
computations to immutable, referencable values.

### 1.1 Object identity and references

* An object is referenced by `ObjectRef = {"ref": "$input" | "<object_id>"}`.
* `$input` refers to the input polynomial defined by `input` (not an object store entry).
* Every referenced `<object_id>` MUST exist in `objects`.

### 1.2 Object ids

Object ids MUST match the regex:

* `[A-Za-z0-9_.:-]+`

(Examples: `int:D`, `poly:R_f20`, `list:factors_1`.)

### 1.3 Canonicality requirement

For any object kind used by a rule, the verifier MUST enforce that the object payload is in the
canonical form defined for that kind (either in this spec or in the active ruleset).

If a ruleset tightens canonical constraints for a kind, those constraints are normative under that ruleset.

### 1.4 Minimal vs enriched payloads

The schema permits `additionalProperties` in object records. Canonicality, however, is defined by
the **kind specification**. Payload fields not recognized by the kind specification MUST be ignored
by the verifier for correctness (MAY be used by explainers).

---

## 2. Built-in object kinds (v3 core)

This section defines object kinds expected to be common across rulesets. Rulesets MAY define additional
kinds.

### 2.1 `IntZ`

An arbitrary-precision integer.

**Record shape:**

```json
{ "kind": "IntZ", "value": "<canonical integer string>" }
```

**Canonical integer string:**

* MUST match `^(?:0|-?[1-9][0-9]*)$`
* MUST NOT use `+` prefix
* MUST NOT use `-0`
* MUST NOT contain leading zeros (except the literal `0`)

**Examples:**

* OK: `"0"`, `"17"`, `"-283"`
* Reject: `"00"`, `"+7"`, `"-0"`

---

### 2.2 `RatQQ`

A rational number in canonical Q encoding.

**Record shape:**

```json
{ "kind": "RatQQ", "value": "<canonical rational string>" }
```

**Canonical rational string:**
Same as `input.coeffs_qq` canonical encoding:

* `0`
* nonzero integer `-?[1-9][0-9]*`
* reduced fraction `p/q` where:

  * `q >= 2`
  * `q > 0`
  * `gcd(|p|, q) = 1`
  * `p != 0`

Examples:

* OK: `"0"`, `"-3"`, `"7/10"`
* Reject: `"1/1"`, `"-0"`, `"2/4"`, `"3/-5"`

---

### 2.3 `PolyQQ`

A polynomial over Q in the single variable `x`.

**Record shape:**

```json
{ "kind": "PolyQQ", "coeffs_qq": ["a_n", ..., "a_0"] }
```

**Canonical encoding:**

* `coeffs_qq` MUST be an array of canonical Q strings.
* The array MUST be **descending degree**: `[a_n, ..., a_0]`.
* Zero polynomial is allowed ONLY as `["0"]`.
* If not the zero polynomial:

  * the first coefficient `a_n` MUST be a canonical nonzero Q string
  * the array length MUST be >= 2 (degree >= 1) unless a ruleset explicitly allows constants

**Notes:**

* This encoding does not force monicity or content normalization. Those are mathematical properties
  proven as facts (e.g., a rule may prove “monic” or “primitive”).
* Derived polynomials (e.g., resolvents) MAY have degrees > 5.

**Examples:**

* `x^2 - 1`:

  ```json
  {"kind":"PolyQQ","coeffs_qq":["1","0","-1"]}
  ```
* `0`:

  ```json
  {"kind":"PolyQQ","coeffs_qq":["0"]}
  ```

---


### 2.4 `MPolyQQ`

A polynomial over Q in the variables `x1, ..., xn`.

**Record shape:**

```json
{
  "kind": "MPolyQQ",
  "nvars": 4,
  "terms": [
    {"exp": [1, 0, 1, 0], "coeff_qq": "1"},
    {"exp": [1, 0, 0, 1], "coeff_qq": "1"},
    {"exp": [0, 1, 1, 0], "coeff_qq": "1"},
    {"exp": [0, 1, 0, 1], "coeff_qq": "1"}
  ]
}
```

This represents the polynomial
\[
x_1x_3 + x_1x_4 + x_2x_3 + x_2x_4 \in \mathbb{Q}[x_1,x_2,x_3,x_4].
\]

**Canonical encoding:**

* `nvars` MUST be an integer `>= 1`.
* `terms` MUST be an array of objects of the form:

  ```json
  { "exp": [e_1, ..., e_n], "coeff_qq": "c" }
  ```

  where:

  * `exp` is a list of length exactly `nvars`,
  * each `e_i` is an integer `>= 0`,
  * `coeff_qq` is a canonical Q string.
* No term may have `coeff_qq = "0"`.
* No two terms may have the same exponent vector.
* Terms MUST be ordered canonically by **descending lexicographic order** on `exp`.
* The zero polynomial is represented uniquely by:

  ```json
  { "kind": "MPolyQQ", "nvars": n, "terms": [] }
  ```

  for the ambient ring \(\mathbb{Q}[x_1,\dots,x_n]\).

**Notes:**

* Variable names are implicit and fixed by position: `x1, ..., xn`.
* This representation is sparse and is intended to model elements of
  \(\mathbb{Q}[x_1,\dots,x_n]\), not syntax trees or factored expressions.
* The symmetric-group action used for resolvents acts by permuting variable indices.

---

### 2.5 `PolyQQList`

An ordered list of references to `PolyQQ` objects.

**Record shape:**

```json
{ "kind": "PolyQQList", "items": ["<object_id>", ...] }
```

**Canonical encoding:**

* `items` MUST be an array of object ids (strings).
* Each referenced object id MUST exist in `objects` and MUST have `kind == "PolyQQ"`.
* Order is **normative** (significant).
* Duplicates are permitted (multiplicity matters).

Rules may impose additional constraints (e.g., non-empty, no constants, monic factors).

**Example:**

```json
{
  "kind": "PolyQQList",
  "items": ["poly:g1", "poly:g2", "poly:g3"]
}
```
---

### 2.6 `RadicalExpr`

A canonical scalar syntax tree for a radical expression.

**Record shape:**

```json
{
  "kind": "RadicalExpr",
  "expr": { ... }
}
```

**Normative notes:**

- `RadicalExpr` is intentionally **syntactic**. The verifier checks only structural
  well-formedness of the payload.
- Mathematical interpretation, rule-specific canonical form, and any claim that a given
  expression denotes a root of a polynomial belong to the proving rule, not to the object kind.
- Equality of `RadicalExpr` objects is **structural exact equality** of canonical payloads.
  Verifiers MUST NOT attempt general algebraic equivalence checking of radical expressions.
- See `docs/rulesets/le5-core@1/radical_expr_canonicality.md` for the ruleset-local
  canonicality policy used by `RadicalRoots`.

**Allowed node kinds inside `expr`:**

#### `qq`

A rational literal or a reference to an existing `RatQQ` object.

```json
{ "kind": "qq", "value_qq": "3/2" }
```

or

```json
{ "kind": "qq", "ref": "rat:alpha" }
```

Canonical constraints:

- Exactly one of `value_qq` or `ref` MUST be present.
- If `value_qq` is present, it MUST be a canonical Q string.
- If `ref` is present, it MUST reference an existing object whose `kind` is `RatQQ`.

#### `zeta`

A root of unity node.

```json
{ "kind": "zeta", "n": 5, "k": 1 }
```

Canonical constraints:

- `n` MUST be an integer `>= 1`.
- `k` MUST be an integer with `0 <= k < n`.

#### `neg`

Unary negation.

```json
{ "kind": "neg", "arg": { ... } }
```

#### Binary arithmetic nodes

```json
{ "kind": "add", "left": { ... }, "right": { ... } }
{ "kind": "sub", "left": { ... }, "right": { ... } }
{ "kind": "mul", "left": { ... }, "right": { ... } }
{ "kind": "div", "left": { ... }, "right": { ... } }
```

#### `pow_int`

An integer power.

```json
{ "kind": "pow_int", "base": { ... }, "exp": -3 }
```

Canonical constraints:

- `exp` MUST be an integer (negative, zero, and positive values are allowed).

#### `root`

Radical extraction.

```json
{ "kind": "root", "n": 5, "arg": { ... } }
```

Canonical constraints:

- `n` MUST be an integer `>= 2`.

**Structural canonicality:**

- Every AST node MUST be an object with a recognized `kind`.
- Every node MUST use the exact key set specified by its `kind`; extra keys are not canonical.
- Child nodes are recursively subject to the same constraints.

---

### 2.7 `RadicalExprList`

An ordered list of references to `RadicalExpr` objects.

**Record shape:**

```json
{ "kind": "RadicalExprList", "items": ["<object_id>", ...] }
```

**Canonical encoding:**

- `items` MUST be an array of object ids (strings).
- Each referenced object id MUST exist in `objects` and MUST have `kind == "RadicalExpr"`.
- Order is **normative** (significant).
- Duplicates are permitted. Rules may use duplicates, for example, to encode repeated roots.

Rules may impose additional constraints (for example, list length or degree-specific order).

**Example:**

```json
{
  "kind": "RadicalExprList",
  "items": ["rexpr:r1", "rexpr:r2"]
}
```

---

### 2.8 `GroupId`

An abstract group identified by a universal catalog system (such as the GAP/Magma SmallGroup library).

**Record shape:**

```
{
  "kind": "GroupId",
  "system": "smallgroup",
  "order": 20,
  "index": 3,
  "alias": "F20"
}

```

**Canonical encoding:**

* `system`: MUST be the exact string `"smallgroup"`.
* `order`: MUST be an integer `>= 1` representing the size of the group.
* `index`: MUST be an integer `>= 1` representing the specific catalog index for that order.
* `alias`: (Optional) A string representing a common human-readable name (e.g., `"F20"`, `"A5"`, `"D5"`). This field is **non-normative** and MUST be ignored by the verifier's mathematical logic; it is strictly for UX and explainers.

**Examples:**

* Frobenius group of order 20 (F20):
```
{
  "kind": "GroupId",
  "system": "smallgroup",
  "order": 20,
  "index": 3,
  "alias": "F20"
}

```


* Symmetric group of degree 5 (S5):
```
{
  "kind": "GroupId",
  "system": "smallgroup",
  "order": 120,
  "index": 34,
  "alias": "S5"
}

```

---

## 3. Recommendations (non-normative)

### 3.1 Content-addressed object ids

For reproducibility and diff-friendly certificates, generators SHOULD consider content-addressed ids,
e.g. `poly:sha256(<canonical payload>)[:12]`.

This is not required by v3 format; it is an engineering recommendation.

### 3.2 Avoid storing enumerations as objects

Small enumerated values that do not require mathematical decoding (e.g., group labels like `S5`)
are typically better expressed as predicate names (e.g., `IsGaloisGroupS5($input)`) rather than
object store entries.

---
