from __future__ import annotations

from opengalois import analyze
from opengalois.explain import render_explanation_from_certificate


def test_explain_handles_deg4_pair_sums_v2_rule() -> None:
    result = analyze([1, 0, 0, -1, -1], explain=False)
    cert = result.certificate

    rules = [fact["rule"] for fact in cert["proof"]["facts"]]
    assert "galois_group.QQ.deg4.S4@2" in rules

    text = render_explanation_from_certificate(cert, fmt="md")
    assert "(x_1+x_2)(x_3+x_4)" in text
    assert "S_4" in text
