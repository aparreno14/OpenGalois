# Lemma kind: `opengalois.analyze`

## 1) Purpose

`opengalois.analyze` is a **container** node used as the root of the proof.

It does not express a mathematical theorem by itself; it is the anchor that ties the proof DAG to the top-level input polynomial.

## 2) Inputs / outputs

Inputs (normative):

- `inputs`: a list of length 1 containing a single `object_ref`.
- Typically this is `{ "ref": "$input" }`.

Outputs (normative):

- `outputs` MUST be omitted or an empty list.
- `outputs` MUST NOT contain `{ "ref": "$input" }`.

Witness (normative):

- `witness` MUST be omitted.

Children:

- `children` MAY be present.
- The meaning of the overall certificate is determined by the conjunction / sequencing of the children lemmas, as defined by conformance sets or application conventions.

## 3) Verification obligations

A verifier checking this lemma kind MUST:

1. Check the node has exactly one input reference.
2. Resolve the reference (either `$input` or an `objects` key).
3. Check there is no witness and no outputs.

No further mathematical recomputation is required.
