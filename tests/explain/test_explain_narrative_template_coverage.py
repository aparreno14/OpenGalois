"""Coverage checks for narrative templates added in the narrative-v2 patch."""

from __future__ import annotations

from opengalois.explain.templates import le5_core_1 as _le5_core_1
from opengalois.explain.templates.registry import get_default_registry

_ = _le5_core_1


NARRATIVE_V1_RULES = {
    "galois_group.QQ.deg4.S4@1",
    "galois_group.QQ.deg4.A4@1",
    "galois_group.QQ.deg4.C4@1",
    "galois_group.QQ.deg4.D4.w1@1",
    "galois_group.QQ.deg4.D4.w2@1",
    "galois_group.QQ.reducible.all_linear.trivial@1",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1",
    "galois_group.QQ.reducible.double_quadratic.C2@1",
    "galois_group.QQ.reducible.double_quadratic.V4@1",
    "galois_group.QQ.reducible.quadratic_cubic.C6@1",
    "galois_group.QQ.reducible.quadratic_cubic.S3@1",
    "galois_group.QQ.reducible.quadratic_cubic.D6@1",
    "galois_group.QQ.reducible.quadratic_cubic.S3@2",
    "galois_group.QQ.reducible.quadratic_cubic.D6@2",
    "resolvent.QQ.compute.deg5.sextic_dummit_F20@1",
    "galois_group.QQ.deg5.S5@1",
    "galois_group.QQ.deg5.A5@1",
    "galois_group.QQ.deg5.F20@1",
    "galois_group.QQ.deg5.D5@1",
    "galois_group.QQ.deg5.C5@1",
    "galois_group.QQ.lift.depressed_monic@1",
    "irreducible.QQ.dummit_resolvent@1",
    "radical_roots.QQ.reducible.compose@1",
    "radical_roots.QQ.deg4.ferrari.depressed_monic@1",
    "radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1",
    "radical_roots.QQ.deg5.mcclintock.depressed_monic@1",
}


def test_narrative_v2_rule_templates_are_registered() -> None:
    registry = get_default_registry()
    missing = sorted(NARRATIVE_V1_RULES - set(registry.rule_templates))
    assert missing == []
