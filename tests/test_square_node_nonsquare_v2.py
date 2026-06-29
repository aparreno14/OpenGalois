from __future__ import annotations

from fractions import Fraction

from opengalois.engine.context import EngineContext
from opengalois.engine.objects import ObjectStore
from opengalois.models import AnalysisOptions
from opengalois.nodes.square import SquareNode


def _ctx_with_rat(value: Fraction) -> EngineContext:
    objects = ObjectStore()
    objects.put_rat("rat:q", value)
    return EngineContext(options=AnalysisOptions(), objects=objects, registry=None)  # type: ignore[arg-type]


def test_square_node_emits_nonsquare_v2_interval() -> None:
    ctx = _ctx_with_rat(Fraction(18, 25))
    facts, out = SquareNode().run(ctx, rat_ref="rat:q")

    assert out["decision"] == "nonsquare"
    assert len(facts) == 1
    fact = facts[0]
    assert fact["rule"] == "nonsquare.QQ.isqrt@2"
    assert fact["evidence"] == {
        "obstruction": {
            "kind": "integer_isqrt_interval",
            "side": "numerator",
            "lower_root": "4",
            "lower_square": "16",
            "upper_root": "5",
            "upper_square": "25",
        }
    }


def test_square_node_emits_nonsquare_v2_negative() -> None:
    ctx = _ctx_with_rat(Fraction(-7, 3))
    facts, out = SquareNode().run(ctx, rat_ref="rat:q")

    assert out["decision"] == "nonsquare"
    assert len(facts) == 1
    fact = facts[0]
    assert fact["rule"] == "nonsquare.QQ.isqrt@2"
    assert fact["evidence"] == {"obstruction": {"kind": "negative"}}
