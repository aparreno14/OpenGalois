from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.explain import explain_certificate

ROOT = Path(__file__).resolve().parents[1]
OK_FIXTURE = (
    ROOT
    / "fixtures"
    / "v3"
    / "le5-core@1"
    / "ok"
    / "irreducible.QQ.zassenhaus_trace@1_mod_irred_001.json"
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_explain_zassenhaus_trace_mentions_prime_and_recombination() -> None:
    cert = _load(OK_FIXTURE)
    text = explain_certificate(cert, target="F2", strict=True, verify_first=True)

    assert "primitive integer part" in text
    assert "chosen prime" in text
    assert "3" in text
    assert "modular factorization" in text
    assert "irreducible in" in text
