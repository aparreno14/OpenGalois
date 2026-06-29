from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.explain import explain_certificate

ROOT = Path(__file__).resolve().parents[1]
OK_DIR = ROOT / "fixtures" / "v3" / "le5-core@1" / "ok"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_explain_nonsquare_v2_interval_mentions_inequality_not_isqrt() -> None:
    cert = _load(OK_DIR / "nonsquare.QQ.isqrt@2_numerator_interval_001.json")
    text = explain_certificate(cert, target="F1", strict=True, verify_first=True)

    assert "4^2 = 16 < 18 < 25 = 5^2" in text
    assert "isqrt" not in text


def test_explain_nonsquare_v2_negative() -> None:
    cert = _load(OK_DIR / "nonsquare.QQ.isqrt@2_negative_001.json")
    text = explain_certificate(cert, target="F1", strict=True, verify_first=True)

    assert "negative" in text
    assert "isqrt" not in text
