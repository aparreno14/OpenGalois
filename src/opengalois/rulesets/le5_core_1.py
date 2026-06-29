from __future__ import annotations

from .registry import register_ruleset
from .types import PredicateSpec, RuleId, RulesetSpec

"""Compiled ruleset: le5-core@1 (v1).

This module is part of the verifier's TCB. It intentionally does not parse YAML at runtime.

Human-readable spec sources:
  - rulesets/le5-core@1/facts.yaml
  - rulesets/le5-core@1/rules/*.yaml
"""

RULESET_ID = "le5-core@1"
VERSION = 1

PREDICATES: dict[str, PredicateSpec] = {
    "IrreducibleQQ": PredicateSpec(
        name="IrreducibleQQ",
        arg_kinds=("PolyQQ",),
        doc="f is irreducible in QQ[x].",
    ),
    "FactorizationMonicQQ": PredicateSpec(
        name="FactorizationMonicQQ",
        arg_kinds=("PolyQQ", "PolyQQList", "RatQQ"),
        doc=(
            "f = unit * Π factors[i] in QQ[x], with each factor monic and deg>=1. "
            "Multiplicity is encoded by duplicates in PolyQQList.items."
        ),
    ),
    "DepressedMonicEq": PredicateSpec(
        name="DepressedMonicEq",
        arg_kinds=("PolyQQ", "PolyQQ"),
        doc="g is the depressed-monic normalization of f over QQ, as defined by le5-core@1.",
    ),
    "GaloisGroup": PredicateSpec(
        name="GaloisGroup",
        arg_kinds=("PolyQQ", "GroupId"),
        doc="G is a Galois group of polynomial f over QQ.",
    ),
    "SolvableByRadicals": PredicateSpec(
        name="SolvableByRadicals",
        arg_kinds=("PolyQQ",),
        doc="f is solvable by radicals over QQ.",
    ),
    "NonSolvableByRadicals": PredicateSpec(
        name="NonSolvableByRadicals",
        arg_kinds=("PolyQQ",),
        doc="f is not solvable by radicals over QQ.",
    ),
    "RadicalRoots": PredicateSpec(
        name="RadicalRoots",
        arg_kinds=("PolyQQ", "RadicalExprList"),
        doc="roots is the canonical ordered list of roots of"
        " f expressed by radicals under the rule-specific scheme.",
    ),
    "Degree": PredicateSpec(
        name="Degree",
        arg_kinds=("PolyQQ", "IntZ"),
        doc="The degree of f is n.",
    ),
    "Discriminant": PredicateSpec(
        name="Discriminant",
        arg_kinds=("PolyQQ", "RatQQ"),
        doc="D is the discriminant of the polynomial f.",
    ),
    "SqrtQQ": PredicateSpec(
        name="SqrtQQ",
        arg_kinds=("RatQQ", "RatQQ"),
        doc="k is a rational square root of q: k^2 = q in QQ.",
    ),
    "IsSquareQQ": PredicateSpec(
        name="IsSquareQQ",
        arg_kinds=("RatQQ",),
        doc="q is a square in QQ.",
    ),
    "NonSquareQQ": PredicateSpec(
        name="NonSquareQQ",
        arg_kinds=("RatQQ",),
        doc="q is not a square in QQ.",
    ),
    "DiscSquareQQ": PredicateSpec(
        name="DiscSquareQQ",
        arg_kinds=("PolyQQ",),
        doc="Discriminant of f is a square in QQ.",
    ),
    "DiscNonSquareQQ": PredicateSpec(
        name="DiscNonSquareQQ",
        arg_kinds=("PolyQQ",),
        doc="Discriminant of f is not a square in QQ.",
    ),
    "ResolventQQ": PredicateSpec(
        name="ResolventQQ",
        arg_kinds=("PolyQQ", "PolyQQ", "MPolyQQ"),
        doc="R is the specialized resolvent over QQ of p at f.",
    ),
}

# Rules allowed by this ruleset (certificates may reference them).
ALLOWED_RULES = frozenset(
    {
        RuleId("irreducible.QQ.deg5_recompute@1"),
        RuleId("factorization.QQ.monic@1"),
        RuleId("normalize.depressed_monic_QQ@1"),
        RuleId("irreducible.QQ.deg1_trivial@1"),
        RuleId("galois_group.QQ.deg1.trivial@1"),
        RuleId("degree.QQ@1"),
        RuleId("galois_group.QQ.deg2.C2@1"),
        RuleId("disc.QQ.compute@1"),
        RuleId("sqrt.QQ.check@1"),
        RuleId("is_square.QQ.lift@1"),
        RuleId("nonsquare.QQ.isqrt@1"),
        RuleId("nonsquare.QQ.isqrt@2"),
        RuleId("disc.square.QQ.lift@1"),
        RuleId("disc.nonsquare.QQ.lift@1"),
        RuleId("galois_group.QQ.deg3.C3@1"),
        RuleId("galois_group.QQ.deg3.S3@1"),
        RuleId("resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1"),
        RuleId("resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1"),
        RuleId("galois_group.QQ.deg4.S4@1"),
        RuleId("galois_group.QQ.deg4.A4@1"),
        RuleId("galois_group.QQ.deg4.V4@1"),
        RuleId("galois_group.QQ.deg4.C4@1"),
        RuleId("galois_group.QQ.deg4.D4.w1@1"),
        RuleId("galois_group.QQ.deg4.D4.w2@1"),
        RuleId("galois_group.QQ.deg4.S4@2"),
        RuleId("galois_group.QQ.deg4.A4@2"),
        RuleId("galois_group.QQ.deg4.V4@2"),
        RuleId("galois_group.QQ.deg4.V4@3"),
        RuleId("galois_group.QQ.deg4.C4@2"),
        RuleId("galois_group.QQ.deg4.D4.w1@2"),
        RuleId("galois_group.QQ.deg4.D4.w2@2"),
        RuleId("galois_group.QQ.reducible.all_linear.trivial@1"),
        RuleId("galois_group.QQ.reducible.single_nonlinear.inherit@1"),
        RuleId("galois_group.QQ.reducible.double_quadratic.C2@1"),
        RuleId("galois_group.QQ.reducible.double_quadratic.V4@1"),
        RuleId("galois_group.QQ.reducible.quadratic_cubic.C6@1"),
        RuleId("galois_group.QQ.reducible.quadratic_cubic.S3@1"),
        RuleId("galois_group.QQ.reducible.quadratic_cubic.D6@1"),
        RuleId("galois_group.QQ.reducible.quadratic_cubic.S3@2"),
        RuleId("galois_group.QQ.reducible.quadratic_cubic.D6@2"),
        RuleId("resolvent.QQ.compute.deg5.sextic_dummit_F20@1"),
        RuleId("galois_group.QQ.deg5.S5@1"),
        RuleId("galois_group.QQ.deg5.A5@1"),
        RuleId("galois_group.QQ.deg5.F20@1"),
        RuleId("galois_group.QQ.deg5.D5@1"),
        RuleId("galois_group.QQ.deg5.C5@1"),
        RuleId("galois_group.QQ.lift.depressed_monic@1"),
        RuleId("irreducible.QQ.dummit_resolvent@1"),
        RuleId("solvable_by_radicals.QQ.from_galois_group@1"),
        RuleId("nonsolvable_by_radicals.QQ.from_galois_group@1"),
        RuleId("radical_roots.QQ.reducible.compose@1"),
        RuleId("radical_roots.QQ.reducible.compose@2"),
        RuleId("radical_roots.QQ.deg1.trivial@1"),
        RuleId("radical_roots.QQ.deg2.quadratic_formula@1"),
        RuleId("radical_roots.QQ.deg3.cardano.depressed_monic@1"),
        RuleId("radical_roots.QQ.deg3.cardano.depressed_monic@2"),
        RuleId("radical_roots.QQ.deg4.ferrari.depressed_monic@1"),
        RuleId("radical_roots.QQ.deg4.ferrari.depressed_monic@2"),
        RuleId("radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1"),
        RuleId("radical_roots.QQ.lift.depressed_monic@1"),
        RuleId("irreducible.QQ.to.depressed_monic@1"),
        RuleId("radical_roots.QQ.deg5.mcclintock.depressed_monic@1"),
        RuleId("irreducible.QQ.zassenhaus_trace@1"),
    }
)

# Rules actually implemented by the reference verifier (informational).
IMPLEMENTED_RULES = frozenset({RuleId("irreducible.QQ.deg5_recompute@1"), 
                                RuleId("irreducible.QQ.deg1_trivial@1"),
                                RuleId("factorization.QQ.monic@1"), 
                                RuleId("normalize.depressed_monic_QQ@1"),
                                RuleId("galois_group.QQ.deg1.trivial@1"),
                                RuleId("degree.QQ@1"),
                                RuleId("galois_group.QQ.deg2.C2@1"),
                                RuleId("disc.QQ.compute@1"),
                                RuleId("sqrt.QQ.check@1"),
                                RuleId("is_square.QQ.lift@1"),
                                RuleId("nonsquare.QQ.isqrt@1"),
                                RuleId("nonsquare.QQ.isqrt@2"),
                                RuleId("disc.square.QQ.lift@1"),
                                RuleId("disc.nonsquare.QQ.lift@1"),
                                RuleId("galois_group.QQ.deg3.C3@1"),
                                RuleId("galois_group.QQ.deg3.S3@1"),
                                RuleId("resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1"),
                                RuleId("resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1"),
                                RuleId("galois_group.QQ.deg4.S4@1"),
                                RuleId("galois_group.QQ.deg4.A4@1"),
                                RuleId("galois_group.QQ.deg4.V4@1"),
                                RuleId("galois_group.QQ.deg4.C4@1"),
                                RuleId("galois_group.QQ.deg4.D4.w1@1"),
                                RuleId("galois_group.QQ.deg4.D4.w2@1"),
                                RuleId("galois_group.QQ.deg4.S4@2"),
                                RuleId("galois_group.QQ.deg4.A4@2"),
                                RuleId("galois_group.QQ.deg4.V4@2"),
                                RuleId("galois_group.QQ.deg4.V4@3"),
                                RuleId("galois_group.QQ.deg4.C4@2"),
                                RuleId("galois_group.QQ.deg4.D4.w1@2"),
                                RuleId("galois_group.QQ.deg4.D4.w2@2"),
                                RuleId("galois_group.QQ.reducible.all_linear.trivial@1"),
                                RuleId("galois_group.QQ.reducible.single_nonlinear.inherit@1"),
                                RuleId("galois_group.QQ.reducible.double_quadratic.C2@1"),
                                RuleId("galois_group.QQ.reducible.double_quadratic.V4@1"),
                                RuleId("galois_group.QQ.reducible.quadratic_cubic.C6@1"),
                                RuleId("galois_group.QQ.reducible.quadratic_cubic.S3@1"),
                                RuleId("galois_group.QQ.reducible.quadratic_cubic.D6@1"),
                                RuleId("galois_group.QQ.reducible.quadratic_cubic.S3@2"),
                                RuleId("galois_group.QQ.reducible.quadratic_cubic.D6@2"),
                                RuleId("resolvent.QQ.compute.deg5.sextic_dummit_F20@1"),
                                RuleId("galois_group.QQ.deg5.S5@1"),
                                RuleId("galois_group.QQ.deg5.A5@1"),
                                RuleId("galois_group.QQ.deg5.F20@1"),
                                RuleId("galois_group.QQ.deg5.D5@1"),
                                RuleId("galois_group.QQ.deg5.C5@1"),
                                RuleId("galois_group.QQ.lift.depressed_monic@1"),
                                RuleId("irreducible.QQ.dummit_resolvent@1"),
                                RuleId("solvable_by_radicals.QQ.from_galois_group@1"),
                                RuleId("nonsolvable_by_radicals.QQ.from_galois_group@1"),
                                RuleId("radical_roots.QQ.reducible.compose@1"),
                                RuleId("radical_roots.QQ.reducible.compose@2"),
                                RuleId("radical_roots.QQ.deg1.trivial@1"),
                                RuleId("radical_roots.QQ.deg2.quadratic_formula@1"),
                                RuleId("radical_roots.QQ.deg3.cardano.depressed_monic@1"),
                                RuleId("radical_roots.QQ.deg3.cardano.depressed_monic@2"),
                                RuleId("radical_roots.QQ.deg4.ferrari.depressed_monic@1"),
                                RuleId("radical_roots.QQ.deg4.ferrari.depressed_monic@2"),
                                RuleId("radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1"),
                                RuleId("radical_roots.QQ.lift.depressed_monic@1"),
                                RuleId("irreducible.QQ.to.depressed_monic@1"),
                                RuleId("radical_roots.QQ.deg5.mcclintock.depressed_monic@1"),
                                RuleId("irreducible.QQ.zassenhaus_trace@1"),
                              })

RULESET = RulesetSpec(
    ruleset_id=RULESET_ID,
    version=VERSION,
    predicates=PREDICATES,
    allowed_rules=ALLOWED_RULES,
    doc="le5 ruleset.",
)

register_ruleset(RULESET)


