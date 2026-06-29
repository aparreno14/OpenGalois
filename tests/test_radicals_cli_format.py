from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.ast import qq, root
from opengalois.radicals.cli_format import format_cli_radical_lines
from opengalois.radicals.schemes import (
    deg3_cardano_depressed_monic,
    deg4_ferrari_depressed_monic,
)


def test_cardano_cli_format_uses_zeta_note_and_u_v_aliases() -> None:
    exprs = deg3_cardano_depressed_monic.build(p=Fraction(1, 1), q=Fraction(2, 1))
    fact = {"rule": "radical_roots.QQ.deg3.cardano.depressed_monic@1"}

    lines = format_cli_radical_lines({}, fact, exprs)

    assert [name for name, _ in lines.aliases] == ["ζ₃", "u", "v"]
    assert lines.aliases[0][1] == "primitive 3rd root of unity"
    assert lines.roots[0] == "u + v"
    assert "ζ₃" in lines.roots[1]


def test_ferrari_cli_format_uses_only_s_alias_in_general_branch() -> None:
    s_expr = root(3, qq(2))
    exprs = deg4_ferrari_depressed_monic.build(
        c=Fraction(1, 1),
        d=Fraction(2, 1),
        e=Fraction(3, 1),
        resolvent_roots=[s_expr, qq(0), qq(0)],
    )
    fact = {"rule": "radical_roots.QQ.deg4.ferrari.depressed_monic@2"}

    lines = format_cli_radical_lines({}, fact, exprs)

    assert [name for name, _ in lines.aliases] == ["s"]
    assert "√(-s)" in lines.roots[0]
    assert "∛(2)" not in lines.roots[0]