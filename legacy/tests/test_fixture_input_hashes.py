import json
from pathlib import Path
from typing import Any

from opengalois.certificate import compute_input_hash


def _scope_from_cert(cert: dict[str, Any]) -> dict[str, Any]:
    inp = cert["input"]
    return {
        "domain": inp["domain"],
        "variable": inp["variable"],
        "ordering": inp["ordering"],
        "degree": inp["degree"],
        "coeffs_qq": inp["coeffs_qq"],
    }


def test_all_fixture_input_hashes_match_input_v1_scope():
    """Test all fixture input hashes match input v1 scope."""
    root = Path(__file__).resolve().parents[1]
    fx_dir = root / "examples" / "certificates" / "v1.1.0"

    for p in sorted(fx_dir.glob("*.json")):
        cert = json.loads(p.read_text(encoding="utf-8"))
        expected = compute_input_hash(_scope_from_cert(cert))
        assert cert["input"]["hash"] == expected, f"{p.name}: input.hash mismatch"
