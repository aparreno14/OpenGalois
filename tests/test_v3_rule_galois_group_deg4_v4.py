from __future__ import annotations

import json
from pathlib import Path

from opengalois.verify import verify_certificate

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "v3" / "le5-core@1"


def _load(rel: str):
    with (FIXTURES / rel).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_deg4_v4_fixtures_ok():
    for rel in [
        "ok/galois_group.QQ.deg4.V4@1_001.json",
        "ok/galois_group.QQ.deg4.V4@1_002.json",
    ]:
        result = verify_certificate(_load(rel))
        assert result.verified, rel


def test_deg4_v4_fixtures_bad():
    for rel in [
        "bad/galois_group.QQ.deg4.V4@1_fail_001.json",
        "bad/galois_group.QQ.deg4.V4@1_fail_002.json",
        "bad/galois_group.QQ.deg4.V4@1_fail_003.json",
    ]:
        result = verify_certificate(_load(rel))
        assert not result.verified, rel
