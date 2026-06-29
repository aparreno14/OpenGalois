from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.schemes import deg3_cardano_depressed_monic, lift_depressed_monic


def test_deg3_cardano_scheme_matches_fixture_shape() -> None:
    """Builds the canonical Cardano ASTs for ``x^3 - 3x + 1``."""
    roots = deg3_cardano_depressed_monic.build(p=Fraction(-3, 1), q=Fraction(1, 1))

    expected = [
        {
            "kind": "add",
            "left": {
                "kind": "root",
                "n": 3,
                "arg": {
                    "kind": "add",
                    "left": {"kind": "qq", "value_qq": "-1/2"},
                    "right": {
                        "kind": "root",
                        "n": 2,
                        "arg": {"kind": "qq", "value_qq": "-3/4"},
                    },
                },
            },
            "right": {
                "kind": "root",
                "n": 3,
                "arg": {
                    "kind": "sub",
                    "left": {"kind": "qq", "value_qq": "-1/2"},
                    "right": {
                        "kind": "root",
                        "n": 2,
                        "arg": {"kind": "qq", "value_qq": "-3/4"},
                    },
                },
            },
        },
        {
            "kind": "add",
            "left": {
                "kind": "mul",
                "left": {"kind": "zeta", "n": 3, "k": 1},
                "right": {
                    "kind": "root",
                    "n": 3,
                    "arg": {
                        "kind": "add",
                        "left": {"kind": "qq", "value_qq": "-1/2"},
                        "right": {
                            "kind": "root",
                            "n": 2,
                            "arg": {"kind": "qq", "value_qq": "-3/4"},
                        },
                    },
                },
            },
            "right": {
                "kind": "mul",
                "left": {"kind": "zeta", "n": 3, "k": 2},
                "right": {
                    "kind": "root",
                    "n": 3,
                    "arg": {
                        "kind": "sub",
                        "left": {"kind": "qq", "value_qq": "-1/2"},
                        "right": {
                            "kind": "root",
                            "n": 2,
                            "arg": {"kind": "qq", "value_qq": "-3/4"},
                        },
                    },
                },
            },
        },
        {
            "kind": "add",
            "left": {
                "kind": "mul",
                "left": {"kind": "zeta", "n": 3, "k": 2},
                "right": {
                    "kind": "root",
                    "n": 3,
                    "arg": {
                        "kind": "add",
                        "left": {"kind": "qq", "value_qq": "-1/2"},
                        "right": {
                            "kind": "root",
                            "n": 2,
                            "arg": {"kind": "qq", "value_qq": "-3/4"},
                        },
                    },
                },
            },
            "right": {
                "kind": "mul",
                "left": {"kind": "zeta", "n": 3, "k": 1},
                "right": {
                    "kind": "root",
                    "n": 3,
                    "arg": {
                        "kind": "sub",
                        "left": {"kind": "qq", "value_qq": "-1/2"},
                        "right": {
                            "kind": "root",
                            "n": 2,
                            "arg": {"kind": "qq", "value_qq": "-3/4"},
                        },
                    },
                },
            },
        },
    ]

    assert roots == expected


def test_lift_depressed_monic_with_zero_shift_is_identity() -> None:
    """Leaves the Cardano roots unchanged when the Tschirnhaus shift is zero."""
    roots = deg3_cardano_depressed_monic.build(p=Fraction(-3, 1), q=Fraction(1, 1))
    lifted = lift_depressed_monic.build(roots=roots, shift=Fraction(0, 1))
    assert lifted == roots
