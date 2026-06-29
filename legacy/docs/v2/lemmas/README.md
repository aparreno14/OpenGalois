# Lemma contracts (v2.0.0)

This directory contains **semantic contracts** for each `proof_node.kind` currently supported by the reference verifier.

These documents are **normative for verification** in the following sense:

- The core schema (`schemas/certificate/2.0.0.json`) validates structure only.
- The meaning of each proof node kind is defined here: inputs, outputs, witness fields, and the **obligations** an independent verifier must replay.

If a lemma contract document conflicts with `docs/certificates/schema-v2.0.0.md`, the certificate semantics document takes precedence.

## Conventions

- `ref` denotes an `object_ref` string.
- `$input` is a reserved `ref` denoting the top-level polynomial in `certificate.input`.
- Objects referenced by `ref != "$input"` must exist in `certificate.objects`.
- Rational strings are always in canonical form (see `docs/verification.md`, §4.3).

## Supported lemma kinds (reference verifier)

- `opengalois.analyze` (root container)
- `normalize.depressed_monic_QQ`
- `factorization.QQ.monic`
- `irreducible.QQ`
