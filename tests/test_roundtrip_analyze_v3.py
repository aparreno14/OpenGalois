from __future__ import annotations

import pytest

from opengalois.api import analyze
from opengalois.verify import verify_certificate


@pytest.mark.parametrize(
    "coeffs_qq",
    [
        # deg 1: x - 1
        ["1", "-1"],
        # deg 5: x^5 - x - 1 (expected irreducible for le5-core)
        ["1", "0", "0", "0", "-1", "-1"],
        # deg 5: (x^2+1)(x^3-x+1) = x^5 + x^2 - x + 1 (reducible, factorization rule)
        ["1", "0", "0", "1", "-1", "1"],
    ],
)
def test_roundtrip_analyze_verify_v3(coeffs_qq: list[str]) -> None:

    res = analyze(polynomial=coeffs_qq) 

    # Support common return styles.
    if isinstance(res, dict) and "certificate" in res:
        cert = res["certificate"]
    elif hasattr(res, "certificate"):
        cert = res.certificate
    else:
        cert = res

    assert isinstance(cert, dict), "analyze() must return a certificate dict (or an object containing it)"
    vres = verify_certificate(cert)
    for c in vres.checks:
        if not c.ok:
            print(f"Check failed: {c.name} - {c.details}")
    assert vres.verified is True
