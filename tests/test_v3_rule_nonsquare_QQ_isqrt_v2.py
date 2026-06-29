from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]
OK_DIR = ROOT / "fixtures" / "v3" / "le5-core@1" / "ok"
BAD_DIR = ROOT / "fixtures" / "v3" / "le5-core@1" / "bad"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_nonsquare_v2_negative_ok() -> None:
    res = verify_certificate(_load(OK_DIR / "nonsquare.QQ.isqrt@2_negative_001.json"))
    assert res.verified is True


def test_nonsquare_v2_numerator_interval_ok() -> None:
    res = verify_certificate(_load(OK_DIR / "nonsquare.QQ.isqrt@2_numerator_interval_001.json"))
    assert res.verified is True


def test_nonsquare_v2_denominator_interval_ok() -> None:
    res = verify_certificate(_load(OK_DIR / "nonsquare.QQ.isqrt@2_denominator_interval_001.json"))
    assert res.verified is True


def test_nonsquare_v2_bad_interval_rejected() -> None:
    res = verify_certificate(_load(BAD_DIR / "nonsquare.QQ.isqrt@2_bad_interval_001.json"))
    assert res.verified is False


def test_nonsquare_v2_bad_negative_rejected() -> None:
    res = verify_certificate(_load(BAD_DIR / "nonsquare.QQ.isqrt@2_bad_negative_001.json"))
    assert res.verified is False
