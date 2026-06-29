from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois import verify

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "v3" / "le5-core@1"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_ferrari_v2_ok_biquadratic_fixture_verifies() -> None:
    cert = _load(FIXTURES / "ok" / "radical_roots.QQ.deg4.ferrari.depressed_monic@2_001.json")
    assert verify(cert).verified


def test_ferrari_v2_ok_general_fixture_verifies() -> None:
    cert = _load(FIXTURES / "ok" / "radical_roots.QQ.deg4.ferrari.depressed_monic@2_002.json")
    assert verify(cert).verified


def test_ferrari_v2_bad_fixture_rejects() -> None:
    cert = _load(FIXTURES / "bad" / "radical_roots.QQ.deg4.ferrari.depressed_monic@2_fail_001.json")
    assert not verify(cert).verified
