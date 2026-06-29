from __future__ import annotations

from typing import Any

from opengalois.explain import explain_certificate


def _ref(name: str) -> dict[str, str]:
    return {"ref": name}


def _certificate() -> dict[str, Any]:
    return {
        "meta": {"ruleset_id": "le5-core@1"},
        "input": {"coeffs_qq": ["1", "0", "0", "0", "1"]},
        "objects": {
            "int.4": {"kind": "IntZ", "value": "4"},
            "group.V4": {"kind": "GroupId", "alias": "V4"},
            "poly.R": {"kind": "PolyQQ", "coeffs_qq": ["1", "0", "-4", "0"]},
            "mpoly.p": {"kind": "MPolyQQ", "text": "x1*x2 + x3*x4"},
            "poly.f1": {"kind": "PolyQQ", "coeffs_qq": ["1", "-2"]},
            "poly.f2": {"kind": "PolyQQ", "coeffs_qq": ["1", "0"]},
            "poly.f3": {"kind": "PolyQQ", "coeffs_qq": ["1", "2"]},
            "list.factors": {
                "kind": "PolyQQList",
                "items": ["poly.f1", "poly.f2", "poly.f3"],
            },
            "rat.unit": {"kind": "RatQQ", "value": "1"},
            "rexpr.1": {
                "kind": "RadicalExpr",
                "expr": {
                    "kind": "root",
                    "n": 2,
                    "arg": {
                        "kind": "div",
                        "left": {
                            "kind": "root",
                            "n": 2,
                            "arg": {"kind": "qq", "value_qq": "-4"},
                        },
                        "right": {"kind": "qq", "value_qq": "2"},
                    },
                },
            },
            "rexpr.2": {
                "kind": "RadicalExpr",
                "expr": {
                    "kind": "neg",
                    "arg": {
                        "kind": "root",
                        "n": 2,
                        "arg": {
                            "kind": "div",
                            "left": {
                                "kind": "root",
                                "n": 2,
                                "arg": {"kind": "qq", "value_qq": "-4"},
                            },
                            "right": {"kind": "qq", "value_qq": "2"},
                        },
                    },
                },
            },
            "rexpr.3": {
                "kind": "RadicalExpr",
                "expr": {
                    "kind": "root",
                    "n": 2,
                    "arg": {
                        "kind": "div",
                        "left": {
                            "kind": "neg",
                            "arg": {
                                "kind": "root",
                                "n": 2,
                                "arg": {"kind": "qq", "value_qq": "-4"},
                            },
                        },
                        "right": {"kind": "qq", "value_qq": "2"},
                    },
                },
            },
            "rexpr.4": {
                "kind": "RadicalExpr",
                "expr": {
                    "kind": "neg",
                    "arg": {
                        "kind": "root",
                        "n": 2,
                        "arg": {
                            "kind": "div",
                            "left": {
                                "kind": "neg",
                                "arg": {
                                    "kind": "root",
                                    "n": 2,
                                    "arg": {"kind": "qq", "value_qq": "-4"},
                                },
                            },
                            "right": {"kind": "qq", "value_qq": "2"},
                        },
                    },
                },
            },
            "rlist.roots": {
                "kind": "RadicalExprList",
                "items": ["rexpr.1", "rexpr.2", "rexpr.3", "rexpr.4"],
            },
        },
        "proof": {
            "facts": [
                {
                    "id": "F1",
                    "claim": {"pred": "Degree", "args": [_ref("$input"), _ref("int.4")]},
                    "rule": "degree.QQ@1",
                },
                {
                    "id": "F2",
                    "claim": {"pred": "IrreducibleQQ", "args": [_ref("$input")]},
                    "rule": "irreducible.QQ.deg5_recompute@1",
                    "premises": ["F1"],
                },
                {
                    "id": "F3",
                    "claim": {
                        "pred": "ResolventQQ",
                        "args": [_ref("poly.R"), _ref("$input"), _ref("mpoly.p")],
                    },
                    "rule": "resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1",
                    "premises": ["F1"],
                },
                {
                    "id": "F4",
                    "claim": {
                        "pred": "FactorizationMonicQQ",
                        "args": [_ref("poly.R"), _ref("list.factors"), _ref("rat.unit")],
                    },
                    "rule": "factorization.QQ.monic@1",
                },
                {
                    "id": "F5",
                    "claim": {
                        "pred": "GaloisGroup",
                        "args": [_ref("$input"), _ref("group.V4")],
                    },
                    "rule": "galois_group.QQ.deg4.V4@1",
                    "premises": ["F1", "F2", "F3", "F4"],
                },
                {
                    "id": "F6",
                    "claim": {
                        "pred": "RadicalRoots",
                        "args": [_ref("$input"), _ref("rlist.roots")],
                    },
                    "rule": "radical_roots.QQ.deg4.ferrari.depressed_monic@2",
                    "premises": ["F1", "F2", "F3", "F4"],
                },
            ],
            "goals": ["F5", "F6"],
        },
    }


def test_latex_uses_display_math_for_long_radical_lists() -> None:
    rendered = explain_certificate(_certificate(), format="latex", strict=False)

    assert r"\setlength{\parindent}{0pt}" in rendered
    assert r"\noindent Let \(f(x) = x^{4} + 1\).\par" in rendered
    assert r"\begin{aligned}" in rendered
    assert "r_{1} &:= " in rendered
    assert r"\right]\)for" not in rendered
    assert r"\left(x\right)" not in rendered
    assert "y^{3} - 4y = \\left(y - 2\\right)\\cdot y" in rendered
    assert r"\sqrt{-\frac{\sqrt{-4}}{2}}" in rendered


def test_identical_display_blocks_are_not_dropped_after_distinct_paragraphs() -> None:
    from opengalois.explain.api import _deduplicate
    from opengalois.explain.proof_model import DisplayMath, display_math, par

    repeated_display = display_math(
        "\n".join(
            [
                r"\begin{aligned}",
                r"r_{1} &:= \sqrt{2}\\",
                r"r_{2} &:= -\sqrt{2}",
                r"\end{aligned}",
            ]
        )
    )

    blocks = [
        par("First derivation gives the following certified roots."),
        repeated_display,
        par("A later rule transports the same displayed roots in a different logical step."),
        repeated_display,
    ]

    deduplicated = _deduplicate(blocks)

    assert len(deduplicated) == 4
    assert deduplicated[0] == blocks[0]
    assert deduplicated[1] == blocks[1]
    assert deduplicated[2] == blocks[2]
    assert deduplicated[3] == blocks[3]
    assert sum(isinstance(block, DisplayMath) for block in deduplicated) == 2