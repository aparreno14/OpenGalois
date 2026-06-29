from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.cli_format import format_cli_radical_lines
from opengalois.radicals.schemes import deg3_cardano_depressed_monic


def test_cli_cardano_v2_generic_uses_only_u_alias_and_zeta_note() -> None:
    exprs = deg3_cardano_depressed_monic.build_v2(
        p=Fraction(2),
        q=Fraction(2),
    )
    radical_fact = {
        "rule": "radical_roots.QQ.deg3.cardano.depressed_monic@2",
    }

    lines = format_cli_radical_lines({}, radical_fact, exprs, style="unicode")

    assert lines.notes == ()
    assert lines.aliases == [
        ("ζ₃", "primitive 3rd root of unity"),
        ("u", "∛(-1 + √(35/27))"),
    ]
    assert lines.roots == [
        "u - 2 / (3 · u)",
        "ζ₃ · u - ζ₃² · 2 / (3 · u)",
        "ζ₃² · u - ζ₃ · 2 / (3 · u)",
    ]
    assert all("+ -" not in root for root in lines.roots)
