# Engineering plan (non-normative)

This document is an internal implementation plan. It must not be read as part of the mathematical specification.

If this document conflicts with the normative certificate semantics, it is wrong.

---

## Design stance (v1)

- Reference backend: SymPy.
- The project should expose a minimal algebra boundary (a façade) so that future backends can be swapped
  without changing the certificate meaning.

This is not a commitment to implement a second backend in the TFG; it is a containment mechanism:
it prevents SymPy types and incidental behavior from leaking into the public certificate.

---

## Implementation checklist (suggested order)

1) Make `analyze()` emit a schema v1.0.1-conformant certificate even for `status="unclassified"`.
2) Make `verify()` validate:
   - schema conformance
   - `input.hash` (JCS RFC8785)
   - core cross-field consistency
3) Implement M1 (separability + reducible envelope).
4) Implement canonical basis (`depressed_monic_QQ`) as a pure function that can be reimplemented.
5) Add goldens after every decisive node (Δ, Sturm shortcut, mod-p witness, f20 witness, C5/D5).
