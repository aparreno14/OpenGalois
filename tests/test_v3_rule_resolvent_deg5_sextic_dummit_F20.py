from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]

OK_FIXTURE = (
    "fixtures/v3/le5-core@1/ok/"
    "resolvent.QQ.compute.deg5.sextic_dummit_F20@1_001.json"
)
BAD_FIXTURE = (
    "fixtures/v3/le5-core@1/bad/"
    "resolvent.QQ.compute.deg5.sextic_dummit_F20@1_fail_001.json"
)


def _load(relpath: str) -> dict[str, Any]:
    return cast(dict[str,Any], json.loads((ROOT / relpath).read_text(encoding="utf-8")))


def _failure_trace(res) -> str:
    return "\n".join(
        f"{chk.name}: {chk.ok} {chk.details}".rstrip() for chk in res.checks
    )


def test_rule_resolvent_deg5_sextic_dummit_F20_ok_fixture_verifies() -> None:
    cert = _load(OK_FIXTURE)
    res = verify_certificate(cert)
    for chk in res.checks:
        if not chk.ok:
            print(f"check failed: {chk.name}\n{chk.details}")
    assert res.verified, _failure_trace(res)


def test_rule_resolvent_deg5_sextic_dummit_F20_bad_fixture_is_rejected() -> None:
    cert = _load(BAD_FIXTURE)
    res = verify_certificate(cert)
    assert not res.verified, "bad fixture unexpectedly verified"
