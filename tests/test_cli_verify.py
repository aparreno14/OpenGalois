from __future__ import annotations

import json

from opengalois import analyze
from opengalois.cli import main


def test_cli_verify_accepts_valid_certificate_json_file(tmp_path, capsys) -> None:
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate
    path = tmp_path / "cert.json"
    path.write_text(json.dumps(cert), encoding="utf-8")

    rc = main(["verify", str(path)])
    captured = capsys.readouterr()

    assert rc == 0
    assert "VERIFIED" in captured.out
    assert captured.err == ""


def test_cli_verify_json_emits_machine_readable_output(tmp_path, capsys) -> None:
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate
    path = tmp_path / "cert.json"
    path.write_text(json.dumps(cert), encoding="utf-8")

    rc = main(["verify", "--json", str(path)])
    captured = capsys.readouterr()

    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["verified"] is True
    assert isinstance(payload["checks"], list)


def test_cli_verify_rejects_missing_file(capsys) -> None:
    rc = main(["verify", "does-not-exist.json"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "error:" in captured.err


def test_cli_verify_rejects_invalid_json(tmp_path, capsys) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json}", encoding="utf-8")

    rc = main(["verify", str(path)])
    captured = capsys.readouterr()

    assert rc == 1
    assert "invalid JSON" in captured.err


def test_cli_verify_rejects_non_object_json(tmp_path, capsys) -> None:
    path = tmp_path / "bad.json"
    path.write_text('["not", "a", "certificate"]', encoding="utf-8")

    rc = main(["verify", str(path)])
    captured = capsys.readouterr()

    assert rc == 1
    assert "top-level value must be an object" in captured.err


def test_cli_verify_returns_one_for_rejected_certificate(tmp_path, capsys) -> None:
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate
    cert["meta"]["schema_version"] = "999.0.0"

    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(cert), encoding="utf-8")

    rc = main(["verify", str(path)])
    captured = capsys.readouterr()

    assert rc == 1
    assert "REJECTED" in captured.out