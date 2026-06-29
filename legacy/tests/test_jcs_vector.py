# tests/test_jcs_vector.py

import hashlib

import pytest

from opengalois.certificate import _jcs_encode, compute_input_hash


def test_jcs_sorts_object_keys_and_has_no_whitespace():
    """Test jcs sorts object keys and has no whitespace."""
    # Key sorting is required by JCS (recursive object property sorting).
    obj = {"b": 2, "a": 1}
    assert _jcs_encode(obj) == '{"a":1,"b":2}'
    assert " " not in _jcs_encode(obj)
    assert "\n" not in _jcs_encode(obj)


def test_jcs_string_escaping_control_and_specials_matches_rfc8785_subset():
    """Test jcs string escaping control and specials matches rfc8785 subset."""
    # RFC 8785 string serialization rules:
    # - Control chars U+0000..U+001F -> \uhhhh (lowercase) except \b\t\n\f\r
    # - Backslash and quote must be escaped as \\ and \"
    # See RFC 8785 §3.2.2.2.
    s = "€$\u000f\nA'B\"\\\\\"/"  # contains U+000F, newline, quote, two backslashes, quote, slash
    expected = "\"€$\\u000f\\nA'B\\\"\\\\\\\\\\\"/\""
    assert _jcs_encode(s) == expected


def test_input_v1_canonical_string_is_exact_and_stable():
    """Test input v1 canonical string is exact and stable."""
    # Canonical key order for input_v1 is lexicographic:
    # coeffs_qq, degree, domain, ordering, variable.
    scope = {
        "variable": "x",
        "ordering": "descending_degree",
        "domain": "Q",
        "coeffs_qq": ["1", "0", "0", "0", "-1", "-1"],
        "degree": 5,
    }
    expected = (
        '{"coeffs_qq":["1","0","0","0","-1","-1"],'
        '"degree":5,'
        '"domain":"Q",'
        '"ordering":"descending_degree",'
        '"variable":"x"}'
    )
    assert _jcs_encode(scope) == expected


def test_input_v1_golden_hash_matches_sha256_of_canonical_bytes():
    """Test input v1 golden hash matches sha256 of canonical bytes."""
    scope = {
        "domain": "Q",
        "variable": "x",
        "ordering": "descending_degree",
        "degree": 5,
        "coeffs_qq": ["1", "0", "0", "0", "-1", "-1"],
    }
    # Golden digest of the canonical UTF-8 bytes of the object above.
    expected_hex = "71f8fe8d34ac4cbf906f15065f9c901dff7c0cb56dfcf0fc735ee8a9f23fbd4d"
    assert compute_input_hash(scope) == expected_hex

    # Cross-check: compute it locally the “obvious” way for this fixed expected string.
    canonical = _jcs_encode(scope).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == expected_hex


def test_jcs_rejects_floats():
    """Test jcs rejects floats."""
    with pytest.raises(TypeError):
        _jcs_encode({"x": 1.0})
    with pytest.raises(TypeError):
        compute_input_hash({"x": 1.0})
