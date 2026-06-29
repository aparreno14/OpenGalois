from __future__ import annotations

from opengalois import analyze


def test_analyze_is_deterministic_for_fixed_inputs():
    """Same input/options must yield identical certificates across runs."""
    inputs = [
        [1, 0, 0, 0, -1, -1],  # x^5 - x - 1 (irreducible)
        [1, 0, -1],            # x^2 - 1 (reducible)
    ]

    for coeffs in inputs:
        c0 = analyze(coeffs, explain=False).certificate
        for _ in range(10):
            c = analyze(coeffs, explain=False).certificate
            assert c == c0
