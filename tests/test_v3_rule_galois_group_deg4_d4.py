from __future__ import annotations

import json
from pathlib import Path

from opengalois.verify import verify_certificate

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "v3" / "le5-core@1"


def _load(rel: str):
    with (FIXTURES / rel).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_deg4_d4_w1_fixture_ok():
    result = verify_certificate(_load("ok/galois_group.QQ.deg4.D4.w1@1_001.json"))
    assert result.verified


def test_deg4_d4_w2_fixture_ok():
    result = verify_certificate(_load("ok/galois_group.QQ.deg4.D4.w2@1_001.json"))
    assert result.verified


def test_deg4_d4_w1_fixtures_bad():
    for rel in [
        "bad/galois_group.QQ.deg4.D4.w1@1_fail_001.json",
        "bad/galois_group.QQ.deg4.D4.w1@1_fail_002.json",
    ]:
        result = verify_certificate(_load(rel))
        assert not result.verified, rel


def test_deg4_d4_w2_fixtures_bad():
    for rel in [
        "bad/galois_group.QQ.deg4.D4.w2@1_fail_001.json",
        "bad/galois_group.QQ.deg4.D4.w2@1_fail_002.json",
    ]:
        result = verify_certificate(_load(rel))
        assert not result.verified, rel
