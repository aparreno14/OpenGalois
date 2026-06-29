---
name: Feature / Implementation
about: Implement a new capability in OpenGalois (core/backend/cli/docs)
title: "[P?][type:?] <short, imperative title>"
labels: []
assignees: []
---

## Context
Explain why this is needed and how it relates to the spec/flow.
- Spec section(s):
- Flow node(s):
- Certificate section(s):
- Verification obligations:

## Scope
What is explicitly in scope / out of scope.
- In scope:
- Out of scope:
- Non-goals / deferrals:

## Design constraints
Hard constraints this change must respect.
- Determinism requirements:
- Backend-agnostic core (no direct SymPy imports):
- Certificate schema compatibility:
- Runtime / complexity expectations (if relevant):

## Implementation plan
Concrete steps (small, reviewable).
1.
2.
3.

## Definition of Done (DoD)
Must be true to close the issue.
- [ ] Code implemented
- [ ] Certificate updated (fields added/filled)
- [ ] `verify()` updated (minimal recomputation)
- [ ] `explain()` updated (if affects decision_path/reject_log)
- [ ] Unit tests added
- [ ] Golden tests added/updated (if applicable)
- [ ] Docs updated (`docs/flow.md` / `docs/certificate_v1.md` / `docs/verification.md`)
- [ ] CI green

## Tests
List concrete tests to add or update.
- Unit:
- Golden:
- Negative (tampered certificate):
- Snapshot (explain/DOT):

## Risks / Edge cases
Anything that might break.
- Mathematical preconditions:
- Coefficient blowup:
- Backend limitations:
- Determinism hazards:

## Review checklist
For the reviewer.
- [ ] Core does not import backend libraries directly
- [ ] Evidence is sufficient and minimal
- [ ] Verification rejects manipulated evidence
- [ ] Output is deterministic
