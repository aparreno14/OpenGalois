from __future__ import annotations

from opengalois.cli import _extract_input_radical_roots


def test_extract_input_radical_roots_renders_unicode_output() -> None:
    """The CLI helper should decode and render the certified root list."""
    certificate = {
        "objects": {
            "rexpr.1": {
                "kind": "RadicalExpr",
                "expr": {"kind": "root", "n": 2, "arg": {"kind": "qq", "value_qq": "2"}},
            },
            "rlist.1": {
                "kind": "RadicalExprList",
                "items": ["rexpr.1"],
            },
        },
        "proof": {
            "facts": [
                {
                    "id": "F1",
                    "claim": {
                        "pred": "RadicalRoots",
                        "args": [{"ref": "$input"}, {"ref": "rlist.1"}],
                    },
                }
            ]
        },
    }

    lines = _extract_input_radical_roots(certificate)
    assert lines is not None
    assert lines.aliases == []
    assert lines.roots == ["√(2)"]


def test_extract_input_radical_roots_reports_invalid_payload() -> None:
    """The CLI helper should report malformed radical-root payloads."""
    certificate: dict[str, object] = {
        "objects": {
            "rlist.1": {"kind": "RadicalExprList", "items": ["missing.expr"]},
        },
        "proof": {
            "facts": [
                {
                    "id": "F1",
                    "claim": {
                        "pred": "RadicalRoots",
                        "args": [{"ref": "$input"}, {"ref": "rlist.1"}],
                    },
                }
            ]
        },
    }

    lines = _extract_input_radical_roots(certificate)
    assert lines is not None
    assert lines.aliases == []
    assert lines.roots == ["<invalid RadicalRoots payload>"]
