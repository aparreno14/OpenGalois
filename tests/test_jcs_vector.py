# tests/test_jcs_vector.py

import hashlib

import pytest

from opengalois.certificate import _jcs_encode, compute_input_hash


def test_jcs_sorts_object_keys_and_has_no_whitespace():
    """JCS sorts keys and emits compact JSON."""
    obj = {"b": 2, "a": 1}
    assert _jcs_encode(obj) == '{"a":1,"b":2}'
    assert " " not in _jcs_encode(obj)
    assert "\n" not in _jcs_encode(obj)


def test_jcs_string_escaping_control_and_specials_matches_rfc8785_subset():
    """String escaping follows RFC8785 subset (as implemented in certificate._jcs_encode)."""
    s = "€$\u000f\nA'B\"\\\\\"/"
    expected = "\"€$\\u000f\\nA'B\\\"\\\\\\\\\\\"/\""
    assert _jcs_encode(s) == expected


def test_input_v1_canonical_string_is_exact_and_stable():
    """The input_v1 hash scope canonicalization is stable."""
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
    """Golden hash for the fixed input_v1 scope."""
    scope = {
        "domain": "Q",
        "variable": "x",
        "ordering": "descending_degree",
        "degree": 5,
        "coeffs_qq": ["1", "0", "0", "0", "-1", "-1"],
    }
    expected_hex = "71f8fe8d34ac4cbf906f15065f9c901dff7c0cb56dfcf0fc735ee8a9f23fbd4d"
    assert compute_input_hash(scope) == expected_hex

    canonical = _jcs_encode(scope).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == expected_hex


def test_jcs_rejects_floats():
    """JCS must reject floats to avoid non-canonical number rendering."""
    with pytest.raises(TypeError):
        _jcs_encode({"x": 1.0})
    with pytest.raises(TypeError):
        compute_input_hash({"x": 1.0})
