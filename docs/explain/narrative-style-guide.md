# OpenGalois explain narrative style guide

This note fixes the intended style for human-readable explanations generated from
OpenGalois certificates.

## Principle

The verifier speaks in facts, rules and objects.  The explanation layer should
not.  The main proof should read like a mathematical proof written for a human:
it should describe the invariant being used, the classification step, and the
reason why the remaining alternatives collapse.

The proof may still be generated rule-by-rule, but the prose should avoid
announcing rule boundaries.  In particular, avoid sentences such as "by rule X"
or "the checker verifies" in the main text.  Those details belong in an optional
technical appendix, not in the mathematical narrative.

## Equations

Use displayed equations only when they clarify a structural step.  Good cases are:

- a group classification being narrowed down;
- a containment such as `G_f \subseteq A_5`;
- a quotient or intermediate field relation such as
  `\operatorname{Gal}(L/K) \cong G_f/C_5`;
- a formula that is mathematically central, such as a discriminant, a resolvent,
  or a radical expression.

Do not use displayed equations for routine checks such as "the degree is 5" or
"the polynomial is irreducible".

## Diagrams

Use diagrams only where they are explicitly part of the explanation or where they
make the mathematical argument genuinely clearer.  Do not insert a field diagram
for every rule.

Recommended uses:

- the cubic `S_3` case, where the splitting field is naturally described as
  `Q(alpha, sqrt(Delta))`;
- the quintic `D_5/C_5` distinction, if we want to emphasize the fixed field of
  the cyclic subgroup `C_5`;
- any future proof where a lattice of intermediate fields is the argument, not
  merely decoration.

For LaTeX, use `tikz-cd` in displayed math:

    \[
    \begin{tikzcd}[row sep=large, column sep=large]
    K_f \arrow[d, dash, "C_5"'] \\
    L \arrow[d, dash, "G_f/C_5"'] \\
    K
    \end{tikzcd}
    \]

The current renderer includes `\usepackage{tikz-cd}` so such blocks compile in
LaTeX output.  Markdown output will preserve the same block as display math.

## Voice

Use direct mathematical prose.  Prefer:

> Since `f` is irreducible of degree 5, its Galois group is a transitive
> subgroup of `S_5`.

Avoid:

> The rule proves that the predicate `GaloisGroup(f,G)` is valid.

The goal is not to hide the certificate, but to separate the human proof from the
machine proof.  A later appendix can expose the certificate internals if needed.
