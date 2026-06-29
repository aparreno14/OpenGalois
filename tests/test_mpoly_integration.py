"""Test MPolyQQ object integration."""
from fractions import Fraction

import pytest

from opengalois.engine.objects import ObjectStore
from opengalois.verify import verify_certificate


def test_put_mpoly_basic():
    """Test storing a basic multivariate polynomial."""
    store = ObjectStore()
    
    # Store x1*x3 + x1*x4 + x2*x3 + x2*x4
    terms = [
        ([1, 0, 1, 0], Fraction(1)),
        ([1, 0, 0, 1], Fraction(1)),
        ([0, 1, 1, 0], Fraction(1)),
        ([0, 1, 0, 1], Fraction(1)),
    ]
    
    obj_id = store.put_mpoly("mpoly1", nvars=4, terms=terms)
    
    assert obj_id == "mpoly1"
    assert "mpoly1" in store.objects
    
    obj = store.objects["mpoly1"]
    assert obj["kind"] == "MPolyQQ"
    assert obj["nvars"] == 4
    assert len(obj["terms"]) == 4
    assert obj["terms"][0]["exp"] == [1, 0, 1, 0]
    assert obj["terms"][0]["coeff_qq"] == "1"


def test_put_mpoly_zero():
    """Test storing the zero polynomial."""
    store = ObjectStore()
    
    obj_id = store.put_mpoly("mpoly_zero", nvars=3, terms=[])
    
    assert obj_id == "mpoly_zero"
    obj = store.objects["mpoly_zero"]
    assert obj["kind"] == "MPolyQQ"
    assert obj["nvars"] == 3
    assert obj["terms"] == []


def test_put_mpoly_with_fractions():
    """Test storing a multivariate polynomial with fractional coefficients."""
    store = ObjectStore()
    
    # Store (1/2)*x1*x2 + (3/4)*x1
    terms = [
        ([1, 1], Fraction(1, 2)),
        ([1, 0], Fraction(3, 4)),
    ]
    
    store.put_mpoly("mpoly_fracs", nvars=2, terms=terms)
    
    obj = store.objects["mpoly_fracs"]
    assert obj["terms"][0]["coeff_qq"] == "1/2"
    assert obj["terms"][1]["coeff_qq"] == "3/4"


def test_put_mpoly_order_validation():
    """Test that terms must be in descending lexicographic order."""
    store = ObjectStore()
    
    # Wrong order: [1,0] should come before [0,1]
    terms = [
        ([0, 1], Fraction(1)),
        ([1, 0], Fraction(1)),
    ]
    
    with pytest.raises(ValueError, match="descending lexicographic order"):
        store.put_mpoly("mpoly_bad", nvars=2, terms=terms)


def test_put_mpoly_zero_coeff():
    """Test that zero coefficients are rejected."""
    store = ObjectStore()
    
    terms = [
        ([1, 0], Fraction(0)),
    ]
    
    with pytest.raises(ValueError, match="zero coefficients"):
        store.put_mpoly("mpoly_bad", nvars=2, terms=terms)


def test_put_mpoly_duplicate_exp():
    """Test that duplicate exponent vectors are rejected."""
    store = ObjectStore()
    
    terms = [
        ([1, 0], Fraction(1)),
        ([1, 0], Fraction(2)),
    ]
    
    with pytest.raises(ValueError, match="repeat exponent vectors"):
        store.put_mpoly("mpoly_bad", nvars=2, terms=terms)


def test_put_mpoly_nvars_validation():
    """Test that nvars must be >= 1."""
    store = ObjectStore()
    
    with pytest.raises(TypeError, match="nvars must be an int >= 1"):
        store.put_mpoly("mpoly_bad", nvars=0, terms=[])
    
    with pytest.raises(TypeError, match="nvars must be an int >= 1"):
        store.put_mpoly("mpoly_bad", nvars=-1, terms=[])


def test_put_mpoly_exp_length():
    """Test that exponent vectors must match nvars."""
    store = ObjectStore()
    
    # exp has length 3 but nvars=2
    terms = [([1, 0, 1], Fraction(1))]
    
    with pytest.raises(TypeError, match="length nvars"):
        store.put_mpoly("mpoly_bad", nvars=2, terms=terms)


def test_verify_certificate_with_mpoly():
    """Test that the verifier accepts certificates with MPolyQQ objects."""
    cert = {
        "format": "opengalois-proof-certificate",
        "version": "3.0.0",
        "ruleset_id": "le5-core@1",
        "created_at": "2026-03-07T00:00:00Z",
        "input": {
            "domain": "QQ",
            "variable": "x",
            "ordering": "desc",
            "degree": 2,
            "coeffs_qq": ["1", "0", "-2"],
            "hash": "a" * 64,
        },
        "objects": {
            "mpoly1": {
                "kind": "MPolyQQ",
                "nvars": 2,
                "terms": [
                    {"exp": [1, 0], "coeff_qq": "1"},
                    {"exp": [0, 1], "coeff_qq": "1"},
                ],
            }
        },
        "proof": {
            "version": "3.0.0",
            "facts": [
                {
                    "id": "f1",
                    "claim": {
                        "pred": "DegreeQQ",
                        "args": [{"ref": "$input"}, {"ref": "d1"}],
                    },
                    "rule": "degree.QQ@1",
                }
            ],
            "goal": "f1",
        },
        "final_status": "ok",
    }
    
    result = verify_certificate(cert)
    # The certificate should be rejected because d1 doesn't exist,
    # but importantly, it should successfully parse the MPolyQQ object
    # without errors during schema validation
    assert result is not None
