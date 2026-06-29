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
            "rat.disc": {"kind": "RatQQ", "value": "256"},
            "rat.sqrt": {"kind": "RatQQ", "value": "16"},
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
            "rexpr.1": {"kind": "RadicalExpr", "expr": {"kind": "qq", "value_qq": "2"}},
            "rexpr.2": {"kind": "RadicalExpr", "expr": {"kind": "qq", "value_qq": "0"}},
            "rlist.roots": {"kind": "RadicalExprList", "items": ["rexpr.1", "rexpr.2"]},
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
                        "pred": "Discriminant",
                        "args": [_ref("$input"), _ref("rat.disc")],
                    },
                    "rule": "disc.QQ.compute@1",
                },
                {
                    "id": "F4",
                    "claim": {
                        "pred": "SqrtQQ",
                        "args": [_ref("rat.disc"), _ref("rat.sqrt")],
                    },
                    "rule": "sqrt.QQ.check@1",
                },
                {
                    "id": "F5",
                    "claim": {"pred": "IsSquareQQ", "args": [_ref("rat.disc")]},
                    "rule": "is_square.QQ.lift@1",
                    "premises": ["F4"],
                },
                {
                    "id": "F6",
                    "claim": {"pred": "DiscSquareQQ", "args": [_ref("$input")]},
                    "rule": "disc.square.QQ.lift@1",
                    "premises": ["F3", "F5"],
                },
                {
                    "id": "F7",
                    "claim": {
                        "pred": "ResolventQQ",
                        "args": [_ref("poly.R"), _ref("$input"), _ref("mpoly.p")],
                    },
                    "rule": "resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1",
                    "premises": ["F1"],
                },
                {
                    "id": "F8",
                    "claim": {
                        "pred": "FactorizationMonicQQ",
                        "args": [_ref("poly.R"), _ref("list.factors"), _ref("rat.unit")],
                    },
                    "rule": "factorization.QQ.monic@1",
                },
                {
                    "id": "F9",
                    "claim": {
                        "pred": "GaloisGroup",
                        "args": [_ref("$input"), _ref("group.V4")],
                    },
                    "rule": "galois_group.QQ.deg4.V4@1",
                    "premises": ["F1", "F2", "F6", "F7", "F8"],
                },
                {
                    "id": "F10",
                    "claim": {
                        "pred": "RadicalRoots",
                        "args": [_ref("$input"), _ref("rlist.roots")],
                    },
                    "rule": "radical_roots.QQ.deg1.trivial@1",
                    "premises": ["F1"],
                },
            ],
            "goals": ["F9", "F10"],
        },
    }


def test_latex_renders_group_resolvent_factorization_and_string_ref_roots() -> None:
    rendered = explain_certificate(_certificate(), format="latex", verify_first=False)

    assert "group.V4" not in rendered
    assert "\\cong V_4" in rendered
    assert "R(y) = y^{3} - 4y" in rendered
    assert "R(y) = y^{4} + 1" not in rendered
    assert r"\cdot \left[\right]" not in rendered
    assert r"\left[\right]" not in rendered
    assert r"\left[2, 0\right]" in rendered
