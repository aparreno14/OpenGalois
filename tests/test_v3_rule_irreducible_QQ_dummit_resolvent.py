from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]
OK_FIXTURE = ROOT / "fixtures" / "v3" / "le5-core@1" / "ok" / "irreducible.QQ.dummit_resolvent@1_001.json"
BAD_FIXTURE = ROOT / "fixtures" / "v3" / "le5-core@1" / "bad" / "irreducible.QQ.dummit_resolvent@1_fail_001.json"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_v3_rule_irreducible_QQ_dummit_resolvent_ok() -> None:
    cert = _load(OK_FIXTURE)
    res = verify_certificate(cert)
    assert res.verified is True


def test_v3_rule_irreducible_QQ_dummit_resolvent_bad_rational_root_present() -> None:
    cert = _load(BAD_FIXTURE)
    res = verify_certificate(cert)
    assert res.verified is False
