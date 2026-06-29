from __future__ import annotations

from opengalois.explain import explain_certificate


def _quartic_v4_certificate() -> dict[str, object]:
    return {
        "meta": {
            "schema_version": "3.0.0",
            "generator": "test",
            "backend": "sympy",
            "ruleset_id": "le5-core@1",
        },
        "input": {
            "domain": "Q",
            "variable": "x",
            "ordering": "descending_degree",
            "degree": 4,
            "coeffs_qq": ["1", "0", "0", "0", "1"],
            "canonicalization": "jcs-rfc8785",
            "hash_alg": "sha256",
            "hash_scope": "input_v1",
            "hash": "0" * 64,
        },
        "objects": {
            "int.4": {"kind": "IntZ", "value": 4},
            "rat.disc.1": {"kind": "RatQQ", "value_qq": "256"},
            "rat.disc.1.sqrt": {"kind": "RatQQ", "value_qq": "16"},
            "group.V4": {"kind": "GroupId", "value": "V4"},
            "poly.resolvent.1": {
                "kind": "PolyQQ",
                "coeffs_qq": ["1", "0", "-4", "0"],
            },
            "rat.unit.1": {"kind": "RatQQ", "value_qq": "1"},
            "poly.f4": {"kind": "PolyQQ", "coeffs_qq": ["1", "-2"]},
            "poly.f5": {"kind": "PolyQQ", "coeffs_qq": ["1", "0"]},
            "poly.f6": {"kind": "PolyQQ", "coeffs_qq": ["1", "2"]},
            "list.factors.1": {
                "kind": "PolyQQList",
                "items": [
                    {"ref": "poly.f4"},
                    {"ref": "poly.f5"},
                    {"ref": "poly.f6"},
                ],
            },
        },
        "proof": {
            "version": "1.0",
            "facts": [
                {
                    "id": "F1",
                    "claim": {
                        "pred": "Degree",
                        "args": [{"ref": "$input"}, {"ref": "int.4"}],
                    },
                    "rule": "degree.QQ@1",
                },
                {
                    "id": "F2",
                    "claim": {
                        "pred": "IrreducibleQQ",
                        "args": [{"ref": "$input"}],
                    },
                    "rule": "irreducible.QQ.deg5_recompute@1",
                    "premises": ["F1"],
                },
                {
                    "id": "F3",
                    "claim": {
                        "pred": "Discriminant",
                        "args": [{"ref": "$input"}, {"ref": "rat.disc.1"}],
                    },
                    "rule": "disc.QQ.compute@1",
                },
                {
                    "id": "F5",
                    "claim": {
                        "pred": "SqrtQQ",
                        "args": [
                            {"ref": "rat.disc.1"},
                            {"ref": "rat.disc.1.sqrt"},
                        ],
                    },
                    "rule": "sqrt.QQ.check@1",
                },
                {
                    "id": "F6",
                    "claim": {
                        "pred": "IsSquareQQ",
                        "args": [{"ref": "rat.disc.1"}],
                    },
                    "rule": "is_square.QQ.lift@1",
                    "premises": ["F5"],
                },
                {
                    "id": "F7",
                    "claim": {
                        "pred": "DiscSquareQQ",
                        "args": [{"ref": "$input"}],
                    },
                    "rule": "disc.square.QQ.lift@1",
                    "premises": ["F3", "F6"],
                },
                {
                    "id": "F4",
                    "claim": {
                        "pred": "ResolventQQ",
                        "args": [{"ref": "$input"}, {"ref": "poly.resolvent.1"}],
                    },
                    "rule": "resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1",
                    "premises": ["F1"],
                },
                {
                    "id": "F15",
                    "claim": {
                        "pred": "FactorizationMonicQQ",
                        "args": [
                            {"ref": "poly.resolvent.1"},
                            {"ref": "list.factors.1"},
                            {"ref": "rat.unit.1"},
                        ],
                    },
                    "rule": "factorization.QQ.monic@1",
                },
                {
                    "id": "F16",
                    "claim": {
                        "pred": "GaloisGroup",
                        "args": [{"ref": "$input"}, {"ref": "group.V4"}],
                    },
                    "rule": "galois_group.QQ.deg4.V4@1",
                    "premises": ["F1", "F2", "F7", "F4", "F15"],
                },
            ],
            "goals": ["F16"],
        },
        "summary": {},
    }


def test_clean_markdown_has_statement_and_proof_without_trace_noise():
    text = explain_certificate(_quartic_v4_certificate(), format="markdown")

    assert "## Statement 1" in text
    assert "## Proof" in text
    assert "$f(x) = x^{4} + 1$" in text
    assert "Artifacts" not in text
    assert "Verified fact" not in text
    assert "No rule-specific narrative" not in text


def test_clean_latex_uses_math_mode_not_texttt_polynomials():
    text = explain_certificate(_quartic_v4_certificate(), format="latex")

    assert r"\(f(x) = x^{4} + 1\)" in text
    assert r"\textasciicircum" not in text
    assert r"\texttt" not in text
    assert "Verified fact" not in text



def _cubic_s3_certificate() -> dict[str, object]:
    return {
        "meta": {
            "schema_version": "3.0.0",
            "generator": "test",
            "backend": "sympy",
            "ruleset_id": "le5-core@1",
        },
        "input": {
            "domain": "Q",
            "variable": "x",
            "ordering": "descending_degree",
            "degree": 3,
            "coeffs_qq": ["1", "0", "-1", "1"],
            "canonicalization": "jcs-rfc8785",
            "hash_alg": "sha256",
            "hash_scope": "input_v1",
            "hash": "0" * 64,
        },
        "objects": {
            "int.3": {"kind": "IntZ", "value": 3},
            "group.S3": {"kind": "GroupId", "value": "S3"},
        },
        "proof": {
            "version": "1.0",
            "facts": [
                {
                    "id": "F1",
                    "claim": {
                        "pred": "Degree",
                        "args": [{"ref": "$input"}, {"ref": "int.3"}],
                    },
                    "rule": "degree.QQ@1",
                },
                {
                    "id": "F2",
                    "claim": {
                        "pred": "IrreducibleQQ",
                        "args": [{"ref": "$input"}],
                    },
                    "rule": "irreducible.QQ.deg5_recompute@1",
                    "premises": ["F1"],
                },
                {
                    "id": "F3",
                    "claim": {
                        "pred": "DiscNonSquareQQ",
                        "args": [{"ref": "$input"}],
                    },
                    "rule": "disc.nonsquare.QQ.lift@1",
                },
                {
                    "id": "F4",
                    "claim": {
                        "pred": "GaloisGroup",
                        "args": [{"ref": "$input"}, {"ref": "group.S3"}],
                    },
                    "rule": "galois_group.QQ.deg3.S3@1",
                    "premises": ["F1", "F2", "F3"],
                },
            ],
            "goals": ["F4"],
        },
        "summary": {},
    }


def test_cubic_s3_latex_tikz_cd_labels_are_not_escaped():
    text = explain_certificate(_cubic_s3_certificate(), format="latex")

    assert r'\"3\"' not in text
    assert r'\"2\"' not in text
    assert "\\arrow[dr, dash, \"3\"\']" in text
    assert "\\arrow[dl, dash, \"2\"]" in text
