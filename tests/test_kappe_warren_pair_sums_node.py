from __future__ import annotations

from fractions import Fraction

from opengalois.engine.context import EngineContext
from opengalois.engine.objects import ObjectStore
from opengalois.engine.registry import EngineRegistry
from opengalois.models import AnalysisOptions


def test_kappe_warren_node_uses_pair_sums_coordinate() -> None:
    ctx = EngineContext(
        options=AnalysisOptions(),
        objects=ObjectStore(),
        registry=EngineRegistry.default(),
    )

    poly_ref = "poly.g"
    ctx.objects.put_poly(poly_ref, [Fraction(1), Fraction(3), Fraction(7), Fraction(0), Fraction(-5)])

    delta = Fraction(11)
    ctx.cache["_disc_out_by_poly"] = {
        poly_ref: {
            "disc_ref": "rat.disc",
            "disc_value": str(delta),
            "facts": {"discriminant": "Fdisc"},
        }
    }

    # In pair-sums coordinates, the unique linear factor is x-s0.
    s0 = Fraction(5)
    ctx.objects.put_poly("poly.linear", [Fraction(1), -s0])
    ctx.objects.put_poly("poly.quad", [Fraction(1), Fraction(1), Fraction(1)])

    nodes, out = ctx.registry.kappe_warren.run(
        ctx,
        poly_ref=poly_ref,
        resolvent_ref="poly.R",
        factor_refs=["poly.linear", "poly.quad"],
        resolvent_family="deg4.cubic_x1plusx2_times_x3plusx4",
    )

    assert nodes
    assert out["root_value"] == "5"
    assert out["s0_value"] == "5"
    assert out["r0_value"] == "2"

    expected_w1 = (Fraction(3) * Fraction(3) - 4 * s0) * delta
    expected_w2 = ((Fraction(7) - s0) ** 2 - 4 * Fraction(-5)) * delta

    assert Fraction(out["w1_value"]) == expected_w1
    assert Fraction(out["w2_value"]) == expected_w2
