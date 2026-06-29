"""Regression tests for strict RadicalExpr validation guards."""

from __future__ import annotations

import pytest

from opengalois.radicals.ast import pow_int, qq, root, zeta
from opengalois.radicals.canon import canon
from opengalois.radicals.codec import validate_expr_payload
from opengalois.radicals.render import render_text


def test_qq_rejects_boolean_literal() -> None:
    """``qq`` must not silently treat booleans as integers."""
    with pytest.raises(TypeError):
        qq(True)



def test_pow_int_rejects_boolean_exponent() -> None:
    """``pow_int`` must reject boolean exponents."""
    with pytest.raises(ValueError):
        pow_int(qq(2), True)



def test_root_rejects_boolean_index() -> None:
    """``root`` must reject boolean radical indices."""
    with pytest.raises(ValueError):
        root(True, qq(2))



def test_zeta_rejects_boolean_fields() -> None:
    """``zeta`` must reject boolean integer fields."""
    with pytest.raises(ValueError):
        zeta(True, 0)
    with pytest.raises(ValueError):
        zeta(3, False)



def test_canon_rejects_boolean_zeta_fields() -> None:
    """Canonicalization must reject malformed boolean zeta fields."""
    with pytest.raises(ValueError):
        canon({"kind": "zeta", "n": True, "k": 0})



def test_codec_rejects_zeta_extra_keys() -> None:
    """Codec validation must enforce the exact zeta key set."""
    with pytest.raises(ValueError):
        validate_expr_payload({"kind": "zeta", "n": 3, "k": 1, "extra": 99})



def test_codec_rejects_boolean_integer_fields() -> None:
    """Codec validation must reject boolean integer fields."""
    with pytest.raises(ValueError):
        validate_expr_payload(
            {"kind": "pow_int", "base": {"kind": "qq", "value_qq": "2"}, "exp": True}
        )
    with pytest.raises(ValueError):
        validate_expr_payload(
            {"kind": "root", "n": True, "arg": {"kind": "qq", "value_qq": "2"}}
        )



def test_render_rejects_boolean_integer_fields() -> None:
    """Renderer must reject malformed boolean integer fields."""
    with pytest.raises(ValueError):
        render_text({"kind": "zeta", "n": 3, "k": True})
