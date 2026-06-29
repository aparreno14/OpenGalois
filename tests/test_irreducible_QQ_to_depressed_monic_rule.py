from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "v3"
    / "le5-core@1"
)


def _load(rel: str) -> dict[str, Any]:
    path = _FIXTURE_DIR / rel
    assert path.is_file(), f"Missing fixture file: {path}"
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_irreducible_QQ_to_depressed_monic_ok() -> None:
    cert = _load("ok/irreducible.QQ.to.depressed_monic@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_irreducible_QQ_to_depressed_monic_bad() -> None:
    cert = _load("bad/irreducible.QQ.to.depressed_monic@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
