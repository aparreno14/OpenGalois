# OpenGalois

OpenGalois is a Python library for **glass-box Galois analysis** of polynomials over `Q[x]` of degree at most 5.

It computes Galois groups, determines solvability by radicals, and, when supported, produces radical expressions for the roots. Unlike a black-box computer algebra system, OpenGalois also emits a **proof-carrying JSON certificate**: a structured derivation that can be checked by an independent verifier using exact arithmetic and an explicit ruleset.
It computes Galois groups, determines solvability by radicals, and, when supported, produces radical expressions for the roots. Unlike a black-box computer algebra system, OpenGalois also emits a **proof-carrying JSON certificate**: a structured derivation that can be checked by an independent verifier using exact arithmetic and an explicit ruleset.

The guiding principle is simple:

> the result should not only be computed; it should be auditable.

OpenGalois is research software, currently in pre-alpha status.

---

## What OpenGalois is

OpenGalois is designed around three goals.

1. **Exact algebraic computation**

   Computations are performed over `Q`, using exact rational arithmetic. The mathematical core deliberately avoids floating-point approximations.

2. **Proof-carrying output**

   The output is not just a label such as `S5` or `D4`. OpenGalois emits a certificate containing the mathematical objects, facts, rules, premises and evidence used to justify the conclusion.

3. **Human-readable explanations**

   The same certificate can be rendered as a mathematical explanation. The explanation is non-normative: it is derived from the certificate, but the certificate and verifier remain the source of truth.

OpenGalois is not intended to compete with large general-purpose systems such as SageMath, PARI/GP, Magma, Mathematica, or Maple. Its purpose is narrower: to make the computation of Galois groups and radical expressions for low-degree polynomials transparent, reproducible and independently checkable.

---

## Mathematical scope

OpenGalois currently targets polynomials

```text
f in Q[x], 1 <= deg(f) <= 5
```

The current core ruleset is:

```text
le5-core@1
```

Supported analysis includes:

- factorization over `Q[x]`;
- irreducibility detection;
- discriminant computation;
- rational square and non-square checks;
- Galois group classification for degrees 1 through 5;
- reducible cases via the splitting fields of irreducible factors;
- solvability by radicals;
- radical expressions for supported solvable cases;
- certificate verification;
- explanation rendering in Markdown, LaTeX and PDF.

### Irreducible cases

For irreducible polynomials, OpenGalois distinguishes the usual transitive possibilities:

- degree 1: trivial group;
- degree 2: `C2`;
- degree 3: `C3` or `S3`;
- degree 4: `C4`, `V4`, `D4`, `A4`, or `S4`;
- degree 5: `C5`, `D5`, `F20`, `A5`, or `S5`.

The degree-4 classification uses the pair-sums cubic resolvent attached to

```text
(x1 + x2)(x3 + x4)
```

and the `C4/D4` branch is resolved by the corresponding Kappe--Warren discriminant tests.

The degree-5 classification uses Dummit's sextic resolvent to detect the solvable branch and distinguish `S5`, `A5`, and `F20`. In the square-discriminant solvable branch, OpenGalois uses Dummit's auxiliary quadratic criterion to distinguish `D5` from `C5`.

### Reducible cases

For reducible polynomials, OpenGalois factors the polynomial over `Q`, removes repeated factors and rational linear factors for the purpose of the splitting field, and then reasons from the irreducible factors.

The main nontrivial reducible patterns in degree at most 5 are:

- two irreducible quadratic factors, giving `C2` or `C2 x C2`;
- one irreducible quadratic and one irreducible cubic factor, giving `C6`, `S3`, or `D6`.

---

## Installation

Once published on PyPI:

```bash
pip install opengalois
```

For development from source:

```bash
git clone https://github.com/aparreno14/OpenGalois.git
cd OpenGalois
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

PDF explanation output requires a local LaTeX installation.

---

## Quickstart: Python API

```python
from opengalois import analyze, verify, render_explanation

# f(x) = x^5 - x - 1
result = analyze([1, 0, 0, 0, -1, -1])

print(result.galois_group)
print(result.solvable_by_radicals)

certificate = result.certificate
verification = verify(certificate)

print(verification.verified)

explanation = render_explanation(result, format="md")
print(explanation)
```

The coefficient list is given in descending degree order:

```text
[a_n, ..., a_0]
```

for

```text
a_n*x^n + ... + a_0
```

Exact rational coefficients may be given as strings:

```python
result = analyze(["1", "0", "-13/5", "38/25", "667/125", "11672/3125"])
```

---

## Quickstart: CLI

Analyze a polynomial and write the certificate to disk:

```bash
opengalois analyze 1 0 0 0 -1 -1 --output cert.json
```

Verify a certificate:

```bash
opengalois verify cert.json
```

Render a human-readable explanation:

```bash
opengalois explain cert.json --format markdown
```

Write a LaTeX explanation:

```bash
opengalois explain cert.json --format latex --out proof.tex
```

Write a PDF explanation:

```bash
opengalois explain cert.json --format pdf --out proof.pdf
```

---

## Certificates

The central artifact produced by OpenGalois is a JSON certificate.

A certificate contains:

- the normalized input polynomial;
- a store of mathematical objects;
- a topologically ordered list of proved facts;
- the rule used for each fact;
- the premises required by each rule;
- optional rule-defined evidence;
- non-normative summary data for user interfaces.

The verifier accepts a certificate only if the normative proof payload is valid.

In particular, summaries, prose explanations, renderer output and UI metadata do not affect correctness.

---

## The Objects / Facts / Rules model
## The Objects / Facts / Rules model

OpenGalois certificates are based on three concepts.
OpenGalois certificates are based on three concepts.

### Objects

Objects are mathematical values appearing in the proof, such as:

- polynomials over `Q`;
- rational numbers;
- group identifiers;
- lists of factors;
- radical expressions.

Objects are stored canonically and referenced by stable identifiers.

### Facts

Facts are mathematical claims about objects, for example:

```text
IrreducibleQQ(f)
Discriminant(f, D)
IsSquareQQ(D)
NonSquareQQ(D)
ResolventQQ(R, f, p)
GaloisGroup(f, G)
RadicalRoots(f, R)
```

A fact is a statement. It becomes accepted only when justified by a rule.

### Rules

Rules are verifier-known inference steps. A rule specifies:

- what kind of fact it can prove;
- which premises are required;
- which object bindings must agree;
- what evidence, if any, is required;
- what deterministic checks the verifier must perform.

The engine proposes facts. The verifier distrusts the engine and checks every rule application independently.

---

## Radical expressions

Radical expressions in OpenGalois are represented as symbolic abstract syntax trees.

They are not floating-point approximations and they are not globally simplified algebraic numbers. Equality of radical expressions is structural, not equality modulo arbitrary algebraic identities.

This design is intentional. It keeps the verifier small and avoids hiding difficult symbolic simplification inside the trusted core.

For example, OpenGalois treats a symbol such as `sqrt(2)` as an algebraic radical object satisfying `u^2 = 2`, not as a numerical branch of the complex square-root function.

---

## Explanation layer

The explanation layer turns certificates into readable mathematical text.

It is designed to be:

- deterministic;
- derived from the proof graph;
- useful for auditing;
- independent from verification.

The explanation layer is not trusted by the verifier. If an explanation and a verified certificate ever disagree, the certificate and ruleset are authoritative.
The explanation layer is not trusted by the verifier. If an explanation and a verified certificate ever disagree, the certificate and ruleset are authoritative.

---

## Documentation map

Start here:

- `docs/overview.md` — conceptual overview of the certificate model;
- `docs/certificate-format.md` — JSON certificate format;
- `docs/objects.md` — canonical object encodings;
- `docs/facts.md` — generic fact-language overview;
- `docs/rulesets/le5-core@1/facts.md` — fact catalog for the active ruleset;
- `docs/rulesets/le5-core@1/` — rule documentation;
- `docs/verification.md` — verifier model;
- `docs/explain.md` — explanation model;
- `docs/resolvents.md` — mathematical background on resolvents;
- `docs/adding-a-fact.md` — developer guide for adding predicates;
- `docs/adding-a-rule.md` — developer guide for adding rules.

---

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```
## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:
Run tests:

```bash
pytest -q
```

Run Ruff:

```bash
ruff check .
```

Run mypy:

```bash
mypy src
```

Build and check the package metadata:

```bash
python -m build
python -m twine check dist/*
```

---

## Status

OpenGalois is currently pre-alpha research software.

The main public surface is:

```python
analyze(polynomial, explain=False)
verify(certificate)
render_explanation(result_or_certificate, format="md")
```

The certificate schema, ruleset and explanation templates may still evolve.

---

## License

OpenGalois is distributed under the MIT License.

---

## Academic context

OpenGalois was developed as part of the project *The Solvability Problem for Polynomials of Degree at Most 5*. The project studies the classification of Galois groups and solvability by radicals for low-degree polynomials, with an emphasis on exact computation, proof-carrying certificates and transparent mathematical explanations.
