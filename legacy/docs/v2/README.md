# OpenGalois

OpenGalois is an open-source **glass-box** library for polynomials over **\(\mathbb{Q}\)** of degree **1..5**.

The library is designed for **auditable mathematics**: instead of returning a black-box claim such as “\(G = S_5\)”, it emits a **proof-carrying certificate** (JSON) that can be checked by an **independent verifier** and rendered into a human-readable explanation.

Core outputs:

- a **certificate** (schema **v2.0.0**, proof-first),
- an **independent verifier**: `verify(certificate)`,
- an **explanation renderer** derived only from the certificate (no hidden state).

---

## Project status

Pre-alpha / under active development.

The public contract that matters is the **certificate format + verifier**. Everything else (backend choice, internal algorithms, UI summaries) is secondary and treated as non-normative unless explicitly evidenced in the proof.

---

## What “proof-carrying” means in OpenGalois

A certificate is meant to be read like a derivation:

- `proof.root` is the root of a **derivation tree**.
- Each node is a **typed lemma**: `proof_node.kind`.
- Intermediate artefacts (polynomials, discriminants, resolvents, factorizations, …) live in an **object store** `objects`, so multiple nodes can reference the same object (a DAG).
- The top-level polynomial is referenced via the reserved identifier `$input`.

The JSON Schema validates **structure** only. Mathematical correctness is enforced by `verify()` by replaying local obligations (exact arithmetic in \(\mathbb{Q}\), witness checks, reconstruction checks, etc.).

---

## Determinism and identity

Mathematical identity is pinned by:

- `input.hash` = `sha256( JCS(input_v1_scope) )`,
- where the scope is the canonical JSON object containing only
  `domain, variable, ordering, degree, coeffs_qq`.

Timestamps and runtime options are non-normative and must not affect identity.

---

## Documentation (read in this order)

Normative (source of truth):

- Certificate semantics (v2.0.0): `docs/certificates/schema-v2.0.0.md`
- Schema file: `schemas/certificate/2.0.0.json`
- Conformance fixtures: `examples/certificates/v2.0.0/`

Derived (must not contradict the schema notes):

- Lemma contracts (what each `proof_node.kind` means): `docs/lemmas/`
- Object contracts (what each `objects[*].kind` means): `docs/objects/`
- Verification model and threat model: `docs/verification.md`

Developer-only (non-normative):

- Engineering notes and plans: `docs/dev/`

Rule for resolving conflicts:

- If a derived document disagrees with `schema-v2.0.0.md`, the derived document is wrong.

---

## Quickstart (developer)

1. Create a virtual environment and install dependencies

   python -m venv .venv
   . .venv/bin/activate    (Linux/macOS)
   .venv\Scripts\activate  (Windows PowerShell)

   pip install -U pip
   pip install -e ".[dev]"

2. Run tests

   pytest -q

3. Minimal smoke check

   python -c "from opengalois import analyze, verify; print(verify(analyze([1,0,0,0,-1,-1], explain=False).certificate).verified)"

---

## Intended API (stable surface)

- `analyze(polynomial, explain=False, **opts) -> Result`
- `verify(certificate, **opts) -> VerifiedResult`
- `render_explanation(result|certificate, format="md"|"tex"|"json")`

CLI (planned):

- `opengalois analyze`
- `opengalois verify`
- `opengalois explain`

---

## License

MIT (see `LICENSE`).
