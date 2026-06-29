from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois import verify

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(relpath: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((REPO_ROOT / relpath).read_text(encoding="utf-8")))


def test_cardano_v2_fixture_ok_generic_branch() -> None:
    cert = _load(
        "fixtures/v3/le5-core@1/ok/"
        "radical_roots.QQ.deg3.cardano.depressed_monic@2_001.json"
    )
    result = verify(cert)
    assert result.verified


def test_cardano_v2_fixture_ok_p_zero_branch() -> None:
    cert = _load(
        "fixtures/v3/le5-core@1/ok/"
        "radical_roots.QQ.deg3.cardano.depressed_monic@2_002_p0.json"
    )
    result = verify(cert)
    assert result.verified


def test_cardano_v2_fixture_bad_old_v1_shape_rejected() -> None:
    cert = _load(
        "fixtures/v3/le5-core@1/bad/"
        "radical_roots.QQ.deg3.cardano.depressed_monic@2_fail_001.json"
    )
    result = verify(cert)
    assert not result.verified


def test_cardano_v2_fixture_bad_p_zero_wrong_zero_roots_rejected() -> None:
    cert = _load(
        "fixtures/v3/le5-core@1/bad/"
        "radical_roots.QQ.deg3.cardano.depressed_monic@2_fail_002_p0_wrong_zero.json"
    )
    result = verify(cert)
    assert not result.verified
