from __future__ import annotations

from opengalois.radicals.ast import add, mul, qq, root
from opengalois.radicals.render import render_text


def test_render_text_uses_unicode_nth_root_for_quintics() -> None:
    expr = root(5, qq(2))
    assert render_text(expr) == "⁵√(2)"


def test_render_text_applies_exact_local_aliases() -> None:
    u_expr = root(5, qq(2))
    expr = add(u_expr, u_expr)
    assert render_text(expr, aliases=[("u", u_expr)]) == "u + u"


def test_render_text_flattens_local_rational_factors_in_products() -> None:
    expr = mul(qq("1/4"), mul(qq("1/2"), add(qq(-2), mul(qq(-1), root(2, qq(-28))))))
    assert render_text(expr) == "1/8 · (-2 - √(-28))"


def test_render_text_preserves_alias_boundaries_inside_products() -> None:
    u_expr = mul(add(qq(-4), qq(3)), root(5, qq(2)))
    expr = mul(root(2, qq(5)), u_expr)
    assert render_text(expr, aliases=[("u2", u_expr)]) == "√(5) · u2"
