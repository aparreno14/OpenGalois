# Certificate examples (schema v1.1.0)

This folder provides **schema-conformance fixtures** for the OpenGalois proof-carrying certificate JSON Schema (v1.1.0).

These examples are intended to:

- exercise **all major branches** of the schema (`ok` / `reducible` / `unclassified` / `error`),
- test the **cross-field constraints** (e.g., `5T5` ⇒ non-square discriminant and `real_roots.count = 3`),
- support CI validation via `check-jsonschema`.

> Note: the `input.hash` values are real (they are checked in `tests/test_fixture_input_hashes.py`).

---

## Valid fixtures

Location: `examples/certificates/v1.1.0/`

- `ok-*.json` — successful irreducible quintic classifications
- `reducible.json` — reducible quintic with explicit ℚ-factorization (with multiplicities)
- `unclassified.json` — structurally valid certificate with no group claim
- `error.json` — structurally valid error certificate

## Invalid fixtures

Location: `examples/certificates/v1.1.0/invalid-*.json`

These are expected to **fail** schema validation.

---

## CI hook

See `.github/workflows/schema-fixtures.yaml`.
