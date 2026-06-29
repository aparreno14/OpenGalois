from __future__ import annotations

from fractions import Fraction

from opengalois.verify import _cardano_v2_root_payloads_for_depressed_cubic


def test_cardano_v2_helper_generic_branch_uses_u_and_alpha_over_u() -> None:
    payloads = _cardano_v2_root_payloads_for_depressed_cubic(
        [Fraction(1), Fraction(0), Fraction(1), Fraction(1)]
    )
    assert payloads is not None

    root1 = payloads[0]["expr"]
    assert root1["kind"] == "add"
    assert root1["left"]["kind"] == "root"
    assert root1["right"]["kind"] == "div"
    assert root1["right"]["left"] == {"kind": "qq", "value_qq": "-1/3"}
    assert root1["right"]["right"] == root1["left"]


def test_cardano_v2_helper_p_zero_branch_uses_cbrt_minus_q_not_div_zero() -> None:
    payloads = _cardano_v2_root_payloads_for_depressed_cubic(
        [Fraction(1), Fraction(0), Fraction(0), Fraction(2)]
    )
    assert payloads is not None

    root1 = payloads[0]["expr"]
    assert root1 == {
        "kind": "root",
        "n": 3,
        "arg": {"kind": "qq", "value_qq": "-2"},
    }
    assert payloads[1]["expr"] == {
        "kind": "mul",
        "left": {"kind": "zeta", "n": 3, "k": 1},
        "right": root1,
    }
    assert payloads[2]["expr"] == {
        "kind": "mul",
        "left": {"kind": "zeta", "n": 3, "k": 2},
        "right": root1,
    }
