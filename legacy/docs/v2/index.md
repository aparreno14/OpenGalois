# OpenGalois documentation index (v2.0.0)

This documentation set targets two audiences simultaneously:

- **Mathematicians**: the certificate should read like a derivation, with explicit witnesses and locally-checkable steps.
- **Software engineers**: the format should be implementable and verifiable by an independent program without access to OpenGalois internals.

The source of truth is the **certificate format** and the **independent verification model**. Any statement about correctness must be backed by `proof` replay under the verifier rules.

---

## 1) What OpenGalois claims today

OpenGalois produces a **proof-carrying certificate** (JSON) for polynomials over \(\mathbb{Q}\) of degree \(1\) to \(5\).

A certificate contains:

- `input`: the polynomial \(f(x)\) in \(\mathbb{Q}[x]\) (descending coefficient order),
- `proof`: a derivation tree of **lemma nodes** (`proof_node.kind`),
- `objects`: a shared store of intermediate artefacts (a DAG),
- `summary`: a non-normative UX summary (ignored by verification).

The *meaning* of `verified=true` is defined by `docs/verification.md`.

---

## 2) Reading order (recommended)

If you want to understand the project end-to-end, read in this order:

1. Certificate semantics (normative): `docs/certificates/schema-v2.0.0.md`
2. Verification model (normative for implementation): `docs/verification.md`
3. Lemma contracts (what each proof node means): `docs/lemmas/`
4. Object contracts (what each object kind means): `docs/objects/`
5. Examples / fixtures: `examples/certificates/v2.0.0/`

---

## 3) Normative vs derived documents

The documentation is structured with an explicit precedence order.

### 3.1 Normative (highest authority)

- `docs/certificates/schema-v2.0.0.md`
- `schemas/certificate/2.0.0.json`
- `examples/certificates/v2.0.0/` (schema-conformance vectors)

These define the certificate structure and its normative interpretation rules (e.g., `$input`, object references, what is structural vs semantic).

### 3.2 Derived (must not contradict normative)

- `docs/verification.md` (verifier pipeline, threat model, TCB, strictness policy)
- `docs/lemmas/*.md` (semantic contracts for `proof_node.kind`)
- `docs/objects/*.md` (semantic contracts for `objects[*].kind`)

If a derived document conflicts with the normative semantics, the derived document is wrong.

### 3.3 Non-normative (engineering / planning)

- `docs/dev/`
- UI notes, roadmaps, refactor plans, etc.

These may describe intended future behavior but do not define correctness.

---

## 4) The certificate as a mathematical object

### 4.1 Proof-first
In v2.0.0 the only normative carrier of mathematical claims is the **proof**:

- Each `proof_node` corresponds to a lemma of the form:
  
      (inputs, witness)  ⟹  outputs

- A verifier checks each lemma locally by recomputation in exact arithmetic.

### 4.2 Object store (DAG)
Intermediate artefacts live in `objects` so they can be shared:

- A node consumes objects via `inputs[i].ref`.
- A node produces objects via `outputs[j].ref` (which must be keys in `objects`).
- The reserved reference `$input` denotes the immutable top-level polynomial and MUST NOT appear as an object key.

This makes the global structure a DAG even though `proof` is syntactically a tree.

---

## 5) Quickstart for auditors (mathematical workflow)

Minimal end-to-end workflow:

1) Generate a certificate (API or CLI)

   - API: `analyze(...)` returns a certificate JSON.

2) Verify the certificate independently

   - Call `verify(certificate)`.
   - Treat `summary` as UX-only; correctness is established only by successful verification.

3) Read the proof for human understanding

   - Use `explain.py` or a custom renderer.
   - The explanation is non-normative; it is a view over the certificate, not a proof by itself.

---

## 6) Legacy documentation (v1.x)

Older documents written for schema v1.x are kept under:

- `docs/legacy/v1.1.0/`

They are historical design notes and MUST NOT be used to interpret v2.0.0 certificates.

---

## 7) Glossary

The glossary is maintained in:

- `docs/glossary.md`

It defines the central terms: lemma kind, object kind, witness, canonical rationals, `$input`, conformance sets, etc.
