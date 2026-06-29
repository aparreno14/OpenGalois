from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from opengalois import verify

FIXTURES_OK = [
    "galois_group.QQ.reducible.all_linear.trivial@1_001.json",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1_001.json",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1_002.json",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1_003.json",
]

FIXTURES_BAD = [
    "galois_group.QQ.reducible.all_linear.trivial@1_fail_001.json",
    "galois_group.QQ.reducible.all_linear.trivial@1_fail_002.json",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1_fail_001.json",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1_fail_002.json",
    "galois_group.QQ.reducible.single_nonlinear.inherit@1_fail_003.json",
]


def _load(rel: str, kind: str) -> dict[str, Any]:
    here = Path(__file__).resolve().parents[1]
    path = here / "fixtures" / "v3" / "le5-core@1" / kind / rel
    with path.open("r", encoding="utf-8") as fh:
        return cast(dict[str, Any], json.load(fh))


@pytest.mark.parametrize("name", FIXTURES_OK)
def test_reducible_case_rule_ok_fixtures_verify(name: str) -> None:
    cert = _load(name, "ok")
    result = verify(cert)
    assert result.verified, f"fixture should verify: {name}\n{result}"


@pytest.mark.parametrize("name", FIXTURES_BAD)
def test_reducible_case_rule_bad_fixtures_reject(name: str) -> None:
    cert = _load(name, "bad")
    result = verify(cert)
    assert not result.verified, f"fixture should be rejected: {name}"
