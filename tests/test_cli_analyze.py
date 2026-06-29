from __future__ import annotations

import json

from opengalois.cli import main


def test_cli_analyze_json_emits_certificate(capsys) -> None:
    rc = main(["analyze", "--json", "1", "0", "0", "0", "-1", "-1"])
    captured = capsys.readouterr()

    assert rc == 0
    assert captured.err == ""

    payload = json.loads(captured.out)
    assert payload["input"]["coeffs_qq"] == ["1", "0", "0", "0", "-1", "-1"]


def test_cli_analyze_accepts_negative_rational_without_double_dash(capsys) -> None:
    rc = main(["analyze", "--json", "1", "0", "0", "0", "-1", "-1/2"])
    captured = capsys.readouterr()

    assert rc == 0
    assert captured.err == ""

    payload = json.loads(captured.out)
    assert payload["input"]["coeffs_qq"] == ["1", "0", "0", "0", "-1", "-1/2"]


def test_cli_analyze_ascending_normalizes_input(capsys) -> None:
    rc = main(
        ["analyze", "--ascending", "--json", "-1/2", "-1", "0", "0", "0", "1"]
    )
    captured = capsys.readouterr()

    assert rc == 0

    payload = json.loads(captured.out)
    assert payload["input"]["coeffs_qq"] == ["1", "0", "0", "0", "-1", "-1/2"]


def test_cli_analyze_writes_output_file(tmp_path, capsys) -> None:
    out_path = tmp_path / "cert.json"

    rc = main(
        ["analyze", "1", "0", "0", "0", "-1", "-1", "--output", str(out_path)]
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert out_path.exists()
    assert "Certificate written to:" in captured.out

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["input"]["coeffs_qq"] == ["1", "0", "0", "0", "-1", "-1"]


def test_cli_analyze_verbose_prints_human_summary(capsys) -> None:
    rc = main(["analyze", "--verbose", "1", "0", "0", "0", "-1", "-1"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "Polynomial:" in captured.out
    assert "Degree:" in captured.out
    assert "Galois group:" in captured.out


def test_cli_analyze_rejects_zero_denominator(capsys) -> None:
    rc = main(["analyze", "1", "0", "0", "0", "-1", "1/0"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "error:" in captured.err
    assert "zero denominator" in captured.err


def test_cli_analyze_rejects_invalid_decimal_token(capsys) -> None:
    rc = main(["analyze", "0.1", "1"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "error:" in captured.err


def test_cli_analyze_rejects_zero_leading_coefficient(capsys) -> None:
    rc = main(["analyze", "0", "1", "-1"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "Leading coefficient" in captured.err


def test_cli_analyze_rejects_too_few_coefficients(capsys) -> None:
    rc = main(["analyze", "1"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "2..6 coefficients" in captured.err


def test_cli_analyze_rejects_too_many_coefficients(capsys) -> None:
    rc = main(["analyze", "1", "0", "0", "0", "0", "0", "1"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "2..6 coefficients" in captured.err