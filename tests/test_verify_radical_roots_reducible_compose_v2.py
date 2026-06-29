from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois import verify


def _load_fixture(name: str) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / 'fixtures' / 'v3' / 'le5-core@1' / name
    return cast(dict[str, Any], json.loads(p.read_text(encoding='utf-8')))


def test_radical_roots_reducible_compose_v2_ok() -> None:
    cert = _load_fixture('ok/radical_roots.QQ.reducible.compose@2_001.json')
    result = verify(cert)
    assert result.verified


def test_radical_roots_reducible_compose_v2_fail_mismatch() -> None:
    cert = _load_fixture('bad/radical_roots.QQ.reducible.compose@2_fail_001.json')
    result = verify(cert)
    assert not result.verified
    assert any('E_MISMATCH' in check.details for check in result.checks)
