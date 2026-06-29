from __future__ import annotations

from opengalois.cli import _print_aligned_rows, _print_wrapped_value


def test_print_aligned_rows_aligns_labels(capsys) -> None:
    _print_aligned_rows(
        [
            ("Polynomial:", "x^4 + 15"),
            ("Degree:", 4),
            ("Galois group:", "D4"),
        ]
    )
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "Polynomial:    x^4 + 15",
        "Degree:        4",
        "Galois group:  D4",
    ]


def test_print_wrapped_value_uses_hanging_indent(capsys) -> None:
    _print_wrapped_value(
        "  r1 = ",
        "alpha beta gamma delta epsilon zeta eta theta iota kappa",
        width=30,
    )
    out = capsys.readouterr().out.splitlines()
    assert len(out) > 1
    assert out[0].startswith("  r1 = ")
    assert all(line.startswith(" " * 7) for line in out[1:])
