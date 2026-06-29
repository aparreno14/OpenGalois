from __future__ import annotations

from opengalois.cli import _build_parser


def test_explain_subcommand_accepts_minimal_options() -> None:
    parser = _build_parser()
    args, extras = parser.parse_known_args(
        [
            "explain",
            "cert.json",
            "--format",
            "latex",
            "--target",
            "F16",
            "--out",
            "proof.tex",
            "--no-verify",
        ]
    )

    assert extras == []
    assert args.command == "explain"
    assert args.certificate == "cert.json"
    assert args.format == "latex"
    assert args.target == "F16"
    assert args.out == "proof.tex"
    assert args.no_verify is True


def test_explain_subcommand_accepts_pdf_format() -> None:
    parser = _build_parser()
    args, extras = parser.parse_known_args(
        [
            "explain",
            "cert.json",
            "--format",
            "pdf",
            "--out",
            "proof.pdf",
            "--no-verify",
        ]
    )

    assert extras == []
    assert args.command == "explain"
    assert args.format == "pdf"
    assert args.out == "proof.pdf"
