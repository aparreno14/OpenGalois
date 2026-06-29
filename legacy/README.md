# OpenGalois

OpenGalois is an open-source **glass-box** library for **quintic polynomials over ℚ**.
It decides **solvability by radicals** and classifies the **transitive Galois group** (irreducible, separable case), producing:

- the **claim** (group / solvability),
- the **evidence** (witnesses + decision path),
- a **proof-carrying certificate** (JSON),
- an **independent verifier** (`verify(certificate)`),
- and a **step-by-step explanation** derived only from the certificate.

Unlike black-box CAS output (e.g., “G = S₅”), OpenGalois is designed so that a third party can audit why the claim holds.

---

## Project status

Pre-alpha / under active development.

The repository currently prioritizes:

- the certificate format (schema v1.1.0 + fixtures),
- the verification model,
- and the mathematics-first decision procedure.

---

## Documentation (read this in order)

Source of truth (normative):

- Certificate schema v1.1.0: `docs/certificates/schema-v1.md`
- Certificate examples v1.1.0: `docs/certificates/examples-v1.md`

Derived documentation (must not contradict the schema):

- Documentation map: `docs/index.md`
- Claims / non-claims (1-page): `docs/claims.md`
- Certificate contract entry point: `docs/certificate_v1.md`
- Specification (scope, claims, non-claims): `docs/spec.md`
- Decision procedure (math-first): `docs/algorithm.md`
- Verification model (proof obligations): `docs/verification.md`
- Traceability (issues ↔ artifacts): `docs/traceability.md`
- Milestones (math-first): `docs/plan.md`

Developer-only notes (non-normative):

- Backend portability notes: `docs/dev/backend.md`
- Implementation plan (engineering): `docs/dev/plan.md`

---

## Key ideas

- Proof-carrying output: `analyze()` returns result + certificate, where every positive claim includes a witness usable by a verifier (except explicit negative claims in v1).
- Independent verification: `verify()` recomputes the minimum required evidence and rejects tampered certificates.
- Determinism: input identity is defined by `input.hash` (JCS RFC8785 + SHA-256, scope `input_v1`).
- Backend portability: v1 uses SymPy as a reference implementation, but the backend is **non-normative**. A future backend is acceptable if it can emit schema-conformant certificates and pass the same golden fixtures.

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

3. Lint / typecheck (if enabled)

   ruff check .
   mypy .

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
