from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "v3" / "le5-core@1"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _failure_trace(res) -> str:
    failed_checks = [chk for chk in res.checks if not chk.ok]
    if not failed_checks:
        return "No failing checks."

    return "\n".join(
        f"{chk.name}: {chk.details}".rstrip()
        for chk in failed_checks
    )


def _collect_cases() -> list[Any]:
    cases = []

    for path in sorted((FIXTURES / "ok").glob("*.json")):
        rel = path.relative_to(FIXTURES)
        cases.append(pytest.param(path, True, id=str(rel)))

    for path in sorted((FIXTURES / "bad").glob("*.json")):
        rel = path.relative_to(FIXTURES)
        cases.append(pytest.param(path, False, id=str(rel)))

    return cases


@pytest.mark.parametrize(("path", "expected"), _collect_cases())
def test_fixture_verification(path: Path, expected: bool) -> None:
    cert = _load(path)
    res = verify_certificate(cert)

    if expected:
        assert res.verified, f"{path.name}\n{_failure_trace(res)}"
    else:
        assert not res.verified, f"bad fixture unexpectedly verified: {path.name}"