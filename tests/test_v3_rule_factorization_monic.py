from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_v3_factorization_monic_ok_fixture_verifies() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / "fixtures" / "v3" / "le5-core@1" / "ok" / "factorization.QQ.monic@1_001.json"
    res = verify_certificate(_load(p))
    for c in res.checks:
        if not c.ok:
            print(f"Check {c.name} failed with message: {c.details}")
    assert res.verified is True


def test_v3_factorization_monic_bad_fixture_rejects() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / "fixtures" / "v3" / "le5-core@1" / "bad" / "factorization.QQ.monic@1_fail_001.json"
    res = verify_certificate(_load(p))
    assert res.verified is False
    assert any(c.name == "v3.rule.factorization.QQ.monic@1" and (c.ok is False) for c in res.checks)
