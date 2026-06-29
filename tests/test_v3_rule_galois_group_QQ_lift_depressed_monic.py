from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]
OK_FIXTURE = ROOT / "fixtures" / "v3" / "le5-core@1" / "ok" / "galois_group.QQ.lift.depressed_monic@1_001.json"
BAD_FIXTURE = ROOT / "fixtures" / "v3" / "le5-core@1" / "bad" / "galois_group.QQ.lift.depressed_monic@1_fail_001.json"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_v3_rule_galois_group_QQ_lift_depressed_monic_ok() -> None:
    cert = _load(OK_FIXTURE)
    res = verify_certificate(cert)
    for c in res.checks:
        if not c.ok:
            print(f"Check {c.name} failed with message: {c.details}")
    assert res.verified is True


def test_v3_rule_galois_group_QQ_lift_depressed_monic_bad_wrong_g_binding() -> None:
    cert = _load(BAD_FIXTURE)
    res = verify_certificate(cert)
    assert res.verified is False
