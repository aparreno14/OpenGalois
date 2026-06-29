---
name: Bug report
about: Report incorrect classification, verification failure, or non-deterministic outputs
title: "[BUG] <short title>"
labels: ["bug"]
assignees: []
---

## What happened?
Describe the observed behavior.

## Expected behavior
What should have happened?

## Reproduction steps
Minimal steps.
1.
2.
3.

## Input / Artifacts
Provide one or more:
- Polynomial input (exact):
- Options used:
- Certificate JSON (attach or link):
- Command output / logs:

## Environment
- OS:
- Python version:
- OpenGalois version/commit:
- Backend (`sympy`, etc.) version:

## Impact
- Classification wrong? Which group expected vs returned?
- `verify()` false positive/negative?
- Non-deterministic certificate?

## Suspected root cause (optional)
Any hypothesis.

## Acceptance criteria
How we know it’s fixed.
- [ ] Repro no longer fails
- [ ] Regression test added (unit/golden)
- [ ] CI green
