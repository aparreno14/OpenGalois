# Glossary

This glossary collects terms used across the OpenGalois documentation and certificate format.

- Certificate: JSON artifact that encodes claim + evidence + trace, designed to be independently verifiable.
- Proof-carrying: positive claims come with witnesses usable by a verifier.
- Glass-box: human-readable explanation can be reconstructed from the certificate (not from hidden computation).
- Status: `result.status` determines the meaning of the certificate (`ok`, `reducible`, `unclassified`, `error`).
- Canonicalization (hashing): RFC8785 JSON canonicalization used to compute `input.hash`.
- Hash scope: `input.hash_scope` defines which fields are hashed (`input_v1` in v1.1.0).
- Canonical basis: the fixed polynomial basis on which invariants/evidence are interpreted (`depressed_monic_QQ`).
- Tschirnhaus shift: translation x ↦ x + s used to eliminate the x⁴ term after monic scaling.
- Witness: an explicit value that makes an existential claim checkable (e.g., a square root or a rational root).
- Negative claim: a claim of non-existence (e.g., “no rational root”). In v1.1.0 these may carry no witness.
- Decision path: `trace.decision_path`, ordered steps taken by the generator.
- Reject log: `trace.reject_log`, optional diagnostic reasons for eliminating candidates (not always normative).
- Transitive group id: `result.transitive_group_id` in {5T1..5T5}, consistent with `result.galois_group`.
- f20: Dummit’s sextic resolvent used to decide solvability for quintics.
