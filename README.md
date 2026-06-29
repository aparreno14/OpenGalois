# OpenGalois

OpenGalois is an open-source **glass-box** library for polynomials over (\mathbb{Q}) of degree **1..5**.

Instead of returning an opaque statement such as “(G = S_5)”, OpenGalois produces a
**proof-carrying certificate** (JSON) whose mathematical claims can be checked by an
**independent verifier** using exact arithmetic and an explicit ruleset.

The project is aimed at **auditable mathematics**:

* every accepted conclusion is backed by explicit facts and rules,
* the verifier checks only the normative proof payload,
* human-readable explanations are derived from the same certificate, with no hidden reasoning.

Core outputs:

* a **certificate** (JSON; proof-carrying),
* an **independent verifier**: `verify(certificate)`,
* an **explanation renderer** derived only from the certificate.

---

## Project status

Pre-alpha / under active development.

The project is currently transitioning from a legacy **v2** model to a more explicit and verifier-friendly
**v3** model.

### Formats: v2 vs v3

* **v2 (schema 2.0.0)**: legacy implemented format, based on proof trees and lemma-oriented reasoning.
* **v3 (schema 3.0.0)**: current target architecture, based on **Facts + Objects + Rules** and an explicit
  fact graph.

The public contract that matters is the **certificate format + verifier**.
Internal algorithms, backend choices, UI summaries, and convenience metadata are secondary and
non-normative unless explicitly referenced by the proof.

---

## What “glass-box” means in OpenGalois

OpenGalois is designed so that a verifier does not need to trust an internal CAS session, a hidden search
procedure, or a prose explanation.

A certificate is accepted only because its **normative proof payload** is valid.

In particular:

* facts are explicit,
* referenced mathematical objects are explicit,
* rules are explicit,
* premises are explicit,
* rule-local evidence is explicit whenever needed.

This makes OpenGalois different from a black-box algebra package: the result is not merely a label,
but a checkable derivation.

---

## What “proof-carrying” means in the v3 model

A v3 certificate is meant to be read as a derivation over a **fact graph**.

### Objects

Mathematical objects live in an `objects` store and are referenced by stable ids.
Typical object kinds include:

* `PolyQQ`
* `MPolyQQ`
* `RatQQ`
* `PolyQQList`
* `GroupId`
* `IntZ`

The top-level polynomial is referenced via the reserved identifier `$input`.

### Facts

The proof is stored as a list `proof.facts[]` of fact nodes.
Each fact node contains:

* `claim`: a typed predicate application `pred(args...)` (**normative**),
* `rule`: the rule id used to justify the claim (**normative**),
* `premises`: references to earlier facts (**normative**),
* `evidence`: optional rule-defined computational evidence (**normative** when required).

Non-normative fields such as `summary`, `statement`, or auxiliary display data must never affect acceptance.

### Rulesets

A verifier checks facts relative to an active `ruleset_id`.
This allows OpenGalois to make the trusted surface explicit:

* which predicates exist,
* which rules are allowed,
* which rule ids are implemented,
* and how each fact type is verified.

> v2 uses a lemma-tree representation.
> v3 generalizes this into an explicit fact graph with a smaller and clearer trusted core.

---

## Determinism and mathematical identity

Mathematical identity is pinned by the normalized polynomial input, not by runtime metadata.

The input identity is:

* `input.hash = sha256( JCS(input_v1_scope) )`

where `input_v1_scope` is the canonical JSON object containing only:

* `domain`
* `variable`
* `ordering`
* `degree`
* `coeffs_qq`

Timestamps, UI options, backend metadata, and similar runtime details are non-normative and must not affect identity.

---

## Normative vs non-normative content

This distinction is fundamental.

### Normative

A verifier may use only:

* the applicable schema,
* the active ruleset,
* the object payloads,
* the fact graph,
* and any rule-defined evidence required by the ruleset.

### Non-normative

The following must never affect acceptance:

* summaries,
* prose statements,
* renderer-specific output,
* backend notes,
* convenience metadata,
* UI-facing explanation fields.

This separation is essential to the OpenGalois design.

---

## Current mathematical scope

OpenGalois is intended for polynomials over (\mathbb{Q}) of degree at most 5.

At the proof level, the project is being developed incrementally by adding:

* canonical object kinds,
* fact predicates,
* rulesets,
* verifier support,
* and degree-specific classification pipelines.

The intended direction is:

* factor/reducibility analysis,
* explicit derived facts such as degree, discriminant, square/non-square status,
* resolvent-based classification where appropriate,
* and final `GaloisGroup(...)` claims justified by explicit rule applications.

The exact set of implemented rules depends on the active branch and ruleset version.
For the normative source of truth, always consult the ruleset files and verifier implementation.

---

## Documentation (read in this order)

### Normative (source of truth)

* `docs/spec/v3/overview.md`
* `docs/spec/v3/certificate-format.md`
* `docs/spec/v3/objects.md`
* `docs/spec/v3/facts.md`
* `docs/spec/v3/rules.md`
* `docs/spec/v3/ruleset.md`

Machine-readable fact catalog:

* `spec/facts.yaml`

Rulesets:

* `rulesets/<ruleset_id>/`

### Verification and explainability

* `docs/verification.md`
* `docs/explain.md`

### Developer documentation

* `docs/dev/adding-a-fact.md`
* `docs/dev/adding-a-rule.md`

### Legacy (v2)

For v2 certificates, the following remain authoritative:

* `schemas/certificate/2.0.0.json`
* `docs/certificates/schema-v2.0.0.md`
* `examples/certificates/v2.0.0/`
* `docs/lemmas/`
* `docs/objects/`

### Conflict rule

If a derived or explanatory document disagrees with the applicable normative schema or ruleset,
the schema/ruleset is authoritative.

---

## Quickstart (developer)

1. Create a virtual environment and install dependencies

   python -m venv .venv
   . .venv/bin/activate    # Linux/macOS

   # .venv\Scripts\activate  # Windows PowerShell

   pip install -U pip
   pip install -e ".[dev]"

2. Run tests

   pytest -q

3. Minimal smoke check

   python -c "from opengalois import analyze, verify; print(verify(analyze([1,0,0,0,-1,-1], explain=False).certificate).verified)"

---

## Intended API (stable surface)

* `analyze(polynomial, explain=False, **opts) -> Result`
* `verify(certificate, **opts) -> VerifiedResult`
* `render_explanation(result|certificate, format="md"|"tex"|"json")`

Planned CLI:

* `opengalois analyze`
* `opengalois verify`
* `opengalois explain`

---

## Design principles

OpenGalois is guided by a small number of design principles:

* **exact arithmetic over trust in heuristics**
* **explicit proof obligations over implicit backend behaviour**
* **normative certificates over renderer-dependent summaries**
* **glass-box verification over black-box classification**
* **mathematical auditability over convenience shortcuts**

---

## License

MIT (see `LICENSE`).

Si quieres, te preparo ahora una **versión aún más afinada** para pegarla directamente en `README.md`, ajustada al estado exacto en que has dejado ya grado 4.
