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


def test_zassenhaus_trace_accepts_modular_irreducible_fixture() -> None:
    cert = _load(OK_DIR / "irreducible.QQ.zassenhaus_trace@1_mod_irred_001.json")
    result = verify_certificate(cert)
    assert result.verified is True


def test_zassenhaus_trace_rejects_wrong_modular_factorization() -> None:
    cert = _load(BAD_DIR / "irreducible.QQ.zassenhaus_trace@1_bad_factorization_001.json")
    result = verify_certificate(cert)
    assert result.verified is False


def test_zassenhaus_trace_rejects_reducible_claim() -> None:
    cert = _load(BAD_DIR / "irreducible.QQ.zassenhaus_trace@1_reducible_claim_001.json")
    result = verify_certificate(cert)
    assert result.verified is False
