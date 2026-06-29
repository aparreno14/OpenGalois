# Object contracts (v2.0.0)

This directory specifies the **semantic meaning** of object kinds stored in `certificate.objects`.

Objects are used to:
- deduplicate intermediate artefacts (DAG store),
- allow multiple proof nodes to reference the same mathematical value,
- provide a stable interface between generators and independent verifiers.

A verifier MUST validate the object kind expected by each lemma it checks.
