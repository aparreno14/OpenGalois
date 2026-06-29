from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate


def _load_fixture(name: str) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / "fixtures" / "v3" / "le5-core@1" / name
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8")))


def test_verify_ok_radical_roots_deg5_mcclintock() -> None:
    cert = _load_fixture("ok/radical_roots.QQ.deg5.mcclintock.depressed_monic@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_verify_bad_radical_roots_deg5_mcclintock() -> None:
    cert = _load_fixture("bad/radical_roots.QQ.deg5.mcclintock.depressed_monic@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert any("E_MISMATCH" in c.details for c in result.checks)
