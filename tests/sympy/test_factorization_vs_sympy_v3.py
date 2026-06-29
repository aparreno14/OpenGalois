# type: ignore

from __future__ import annotations

import itertools
import math
import os
import random
from collections.abc import Iterator
from fractions import Fraction

import pytest

if os.getenv("OPENGALOIS_RUN_SYMPY_CROSSCHECK") != "1":
    pytest.skip(
        "local SymPy cross-check disabled; set OPENGALOIS_RUN_SYMPY_CROSSCHECK=1",
        allow_module_level=True,
    )

sp = pytest.importorskip("sympy")

from opengalois.algorithms.factorization import (
    factorize_le5,
    factorize_le5_multiplicity,
    zassenhaus_irreducibility_trace_le5,
)

x = sp.Symbol("x")


# =============================================================================
# Conversion and comparison helpers
# =============================================================================


def _trim_desc_q(poly: list[Fraction]) -> list[Fraction]:
    """Return a descending QQ polynomial without leading zeroes."""
    i = 0
    while i < len(poly) and poly[i] == 0:
        i += 1
    return poly[i:]


def _to_sympy_poly(coeffs: list[Fraction]) -> sp.Poly:
    """Convert descending Fraction coefficients to a SymPy polynomial over QQ."""
    coeffs = _trim_desc_q([Fraction(c) for c in coeffs])
    if not coeffs:
        return sp.Poly(0, x, domain=sp.QQ)

    degree = len(coeffs) - 1
    expr = sp.Integer(0)
    for i, coeff in enumerate(coeffs):
        expr += sp.Rational(coeff.numerator, coeff.denominator) * x ** (degree - i)
    return sp.Poly(expr, x, domain=sp.QQ)


def _sympy_poly_to_monic_fraction_coeffs(poly: sp.Poly) -> list[Fraction]:
    """Return the monic QQ coefficient list associated to a nonzero SymPy poly."""
    poly = sp.Poly(poly, x, domain=sp.QQ)
    if poly.degree() <= 0:
        raise ValueError("expected a nonconstant polynomial")

    lc = sp.Rational(poly.LC())
    return [
        Fraction(int(sp.Rational(coeff).p), int(sp.Rational(coeff).q))
        / Fraction(int(lc.p), int(lc.q))
        for coeff in poly.all_coeffs()
    ]


def _poly_key_from_fraction_coeffs(coeffs: list[Fraction]) -> tuple[tuple[int, int], ...]:
    """Return a canonical key for a monic QQ factor represented by Fractions."""
    coeffs = _trim_desc_q([Fraction(c) for c in coeffs])
    return tuple((coeff.numerator, coeff.denominator) for coeff in coeffs)


def _poly_key_from_sympy(poly: sp.Poly) -> tuple[tuple[int, int], ...]:
    """Return the same canonical key for a SymPy QQ polynomial."""
    poly = sp.Poly(poly, x, domain=sp.QQ).monic()
    return tuple(
        (int(sp.Rational(coeff).p), int(sp.Rational(coeff).q))
        for coeff in poly.all_coeffs()
    )


def _expanded_sympy_factor_keys(poly: sp.Poly) -> list[tuple[tuple[int, int], ...]]:
    """Return the sorted list of monic irreducible QQ factor keys from SymPy."""
    _, factor_data = poly.factor_list()

    keys: list[tuple[tuple[int, int], ...]] = []
    for factor, multiplicity in factor_data:
        factor = sp.Poly(factor, x, domain=sp.QQ)
        if factor.degree() <= 0:
            continue
        keys.extend([_poly_key_from_sympy(factor)] * int(multiplicity))

    return sorted(keys)


def _assert_factorization_matches_sympy(coeffs: list[Fraction]) -> None:
    """Check product, irreducibility and uniqueness against SymPy over QQ."""
    coeffs = _trim_desc_q([Fraction(c) for c in coeffs])
    original = _to_sympy_poly(coeffs)

    try:
        factors = factorize_le5(coeffs)
    except Exception as exc:  # pragma: no cover - failure path only
        pytest.fail(f"factorize_le5 raised {exc!r} for input {coeffs!r}")

    assert factors, f"empty factorization for nonconstant input {coeffs!r}"

    product = sp.Poly(1, x, domain=sp.QQ)
    observed_keys: list[tuple[tuple[int, int], ...]] = []

    for factor_coeffs in factors:
        factor_coeffs = _trim_desc_q([Fraction(c) for c in factor_coeffs])
        factor_poly = _to_sympy_poly(factor_coeffs)

        assert factor_poly.degree() >= 1, (
            f"constant factor {factor_coeffs!r} returned for input {coeffs!r}"
        )
        assert factor_poly.LC() == 1, (
            f"non-monic factor {factor_coeffs!r} returned for input {coeffs!r}"
        )
        assert factor_poly.is_irreducible, (
            f"reducible factor {factor_coeffs!r} returned for input {coeffs!r}; "
            f"SymPy factorization is {factor_poly.factor_list()}"
        )

        product *= factor_poly
        observed_keys.append(_poly_key_from_fraction_coeffs(factor_coeffs))

    assert product == original, (
        f"factor product does not recover input {coeffs!r}; "
        f"got {product.as_expr()}, expected {original.as_expr()}"
    )

    expected_keys = _expanded_sympy_factor_keys(original)
    assert sorted(observed_keys) == expected_keys, (
        f"factorization differs from SymPy for input {coeffs!r};\n"
        f"observed={sorted(observed_keys)!r}\n"
        f"expected={expected_keys!r}"
    )

    compressed = factorize_le5_multiplicity(coeffs)
    expanded_from_compressed: list[tuple[tuple[int, int], ...]] = []
    for factor_coeffs, multiplicity in compressed:
        expanded_from_compressed.extend(
            [_poly_key_from_fraction_coeffs(factor_coeffs)] * int(multiplicity)
        )
    assert sorted(expanded_from_compressed) == sorted(observed_keys), (
        f"factorize_le5_multiplicity is inconsistent with factorize_le5 for {coeffs!r}"
    )


def _assert_zassenhaus_trace_matches_sympy(coeffs: list[Fraction]) -> None:
    """Check trace emission on inputs satisfying the Zassenhaus preconditions.

    ``zassenhaus_irreducibility_trace_le5`` is a trace helper for square-free
    primitive Zassenhaus inputs.  The full factorization pipeline handles
    repeated factors before reaching this helper, via Yun square-free
    decomposition.  Therefore this differential test skips non-square-free
    inputs instead of requiring the helper to accept them directly.
    """
    coeffs = _trim_desc_q([Fraction(c) for c in coeffs])
    poly = _to_sympy_poly(coeffs)

    if poly.degree() <= 1:
        return

    # The helper is only exercised on square-free inputs.  Non-square-free
    # examples such as 4*x**2 - 4*x + 1 = (2*x - 1)**2 have no good
    # Zassenhaus prime, so calling the helper directly is outside its contract.
    if sp.Poly(poly.gcd(poly.diff()), x, domain=sp.QQ).degree() > 0:
        return

    trace = zassenhaus_irreducibility_trace_le5(coeffs)

    if poly.is_irreducible:
        assert trace is not None, (
            f"irreducible polynomial did not emit a Zassenhaus trace: {coeffs!r}"
        )
    else:
        assert trace is None, (
            f"reducible polynomial emitted a false irreducibility trace: {coeffs!r}; "
            f"SymPy factorization is {poly.factor_list()}"
        )


# =============================================================================
# Deterministic bounded inputs
# =============================================================================


def _iter_monic_integer_inputs(max_degree: int, coeff_bound: int) -> Iterator[list[Fraction]]:
    """Yield all monic integer polynomials in the bounded coefficient box."""
    for degree in range(1, max_degree + 1):
        for tail in itertools.product(range(-coeff_bound, coeff_bound + 1), repeat=degree):
            yield [Fraction(1), *(Fraction(c) for c in tail)]


def _iter_monic_rational_inputs(
    max_degree: int,
    coeff_bound: int,
    leading_bound: int,
) -> Iterator[list[Fraction]]:
    """Yield bounded monic QQ polynomials obtained from primitive Z[x] inputs.

    A primitive integer polynomial

        b*x^n + a_{n-1}*x^{n-1} + ... + a_0

    is converted to the monic rational polynomial obtained by dividing by b.
    This deliberately stresses denominator-clearing and non-integral monic inputs.
    """
    for degree in range(1, max_degree + 1):
        for leading_coeff in range(2, leading_bound + 1):
            for tail in itertools.product(
                range(-coeff_bound, coeff_bound + 1),
                repeat=degree,
            ):
                coeffs_z = [leading_coeff, *tail]
                yield [Fraction(c, leading_coeff) for c in coeffs_z]


def _bounded_test_inputs() -> Iterator[list[Fraction]]:
    """Yield deterministic bounded test inputs, with duplicates removed."""
    max_degree = int(os.getenv("OPENGALOIS_FACTOR_TEST_MAX_DEGREE", "5"))
    coeff_bound = int(os.getenv("OPENGALOIS_FACTOR_TEST_COEFF_BOUND", "2"))
    leading_bound = int(os.getenv("OPENGALOIS_FACTOR_TEST_LEADING_BOUND", "3"))

    seen: set[tuple[tuple[int, int], ...]] = set()

    streams = [
        _iter_monic_integer_inputs(max_degree, coeff_bound),
        _iter_monic_rational_inputs(max_degree, coeff_bound, leading_bound),
    ]

    for stream in streams:
        for coeffs in stream:
            key = _poly_key_from_fraction_coeffs(coeffs)
            if key in seen:
                continue
            seen.add(key)
            yield coeffs


# =============================================================================
# Targeted historical and structural edge cases
# =============================================================================


def _known_edge_cases() -> list[list[Fraction]]:
    """Return targeted cases that should never depend on random coverage."""
    return [
        # Non-integral monic polynomial: 6*x^2 - 5*x + 1 = (2*x - 1)(3*x - 1).
        [Fraction(1), Fraction(-5, 6), Fraction(1, 6)],
        # Repeated rational linear factor.
        [Fraction(1), Fraction(-1), Fraction(1, 4)],
        # Cyclotomic split: x^5 - 1.
        [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(-1)],
        # Repeated zero root.
        [Fraction(1), Fraction(0), Fraction(0), Fraction(0)],
        # Product with mixed degrees.
        [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(1), Fraction(1)],
        # Quartic pair-sums resolvent from x^4 + 7*x^3 - 16*x^2 - 4*x + 13:
        # 64*R = (4*x + 69)*(16*x^2 + 824*x + 8349).
        [
            Fraction(1),
            Fraction(275, 4),
            Fraction(22563, 16),
            Fraction(576081, 64),
        ],
        # Quartic pair-sums resolvent from x^4 - 3*x^3 - x^2 - 3*x + 1:
        # 64*R = (4*x + 21)*(16*x^2 + 56*x + 189).
        [
            Fraction(1),
            Fraction(35, 4),
            Fraction(483, 16),
            Fraction(3969, 64),
        ],
        # Same non-monic primitive products, written directly as monic QQ inputs.
        _integer_product_to_monic_q([[4, 69], [16, 824, 8349]]),
        _integer_product_to_monic_q([[4, 21], [16, 56, 189]]),
    ]


def _integer_product_to_monic_q(factors_desc_z: list[list[int]]) -> list[Fraction]:
    """Multiply primitive integer factors and return the associated monic QQ poly."""
    product = sp.Poly(1, x, domain=sp.QQ)
    for factor_desc in factors_desc_z:
        if not factor_desc or factor_desc[0] == 0:
            raise ValueError(f"invalid integer factor: {factor_desc!r}")
        factor = _to_sympy_poly([Fraction(c) for c in factor_desc])
        product *= factor
    return _sympy_poly_to_monic_fraction_coeffs(product)


def test_factorize_le5_known_edge_cases_vs_sympy() -> None:
    """Check targeted cases that have historically exposed factorization bugs."""
    for coeffs in _known_edge_cases():
        _assert_factorization_matches_sympy(coeffs)


# =============================================================================
# Non-monic primitive product stress tests
# =============================================================================


def _content_desc_z(coeffs: list[int]) -> int:
    """Return the integer content of a Z[x] coefficient list."""
    content = 0
    for coeff in coeffs:
        content = math.gcd(content, abs(coeff))
    return content


def _random_nonzero_int(rng: random.Random, bits: int, *, min_abs: int = 1) -> int:
    """Return a deterministic pseudo-random nonzero integer."""
    if bits <= 0:
        raise ValueError("bits must be positive")
    while True:
        value = rng.getrandbits(bits)
        if value >= min_abs:
            return -value if rng.randrange(2) else value


def _random_primitive_nonmonic_integer_factor(
    rng: random.Random,
    degree: int,
    bits: int,
) -> list[int]:
    """Return a primitive non-monic integer factor of the requested degree."""
    if degree <= 0:
        raise ValueError("factor degree must be positive")

    while True:
        leading = _random_nonzero_int(rng, bits, min_abs=2)
        tail = [_random_large_int(rng, bits) for _ in range(degree)]
        coeffs = [leading, *tail]
        if _content_desc_z(coeffs) == 1:
            return coeffs


def _factor_degree_partitions(max_degree: int) -> list[tuple[int, ...]]:
    """Return deterministic degree partitions with at least two factors."""
    base = [
        (1, 1),
        (1, 2),
        (2, 2),
        (1, 3),
        (2, 3),
        (1, 4),
        (1, 1, 1),
        (1, 1, 2),
        (1, 1, 3),
        (1, 2, 2),
    ]
    return [partition for partition in base if sum(partition) <= max_degree]


def _iter_random_nonmonic_primitive_products() -> Iterator[list[Fraction]]:
    """Yield products of primitive non-monic integer factors, monicized over QQ.

    This directly stresses the Zassenhaus case where the primitive integer model
    has a nontrivial leading coefficient split across the true factors.
    """
    cases = int(os.getenv("OPENGALOIS_FACTOR_PRODUCT_CASES", "120"))
    bits = int(os.getenv("OPENGALOIS_FACTOR_PRODUCT_BITS", "40"))
    seed = int(os.getenv("OPENGALOIS_FACTOR_PRODUCT_SEED", "20260624"))
    max_degree = int(os.getenv("OPENGALOIS_FACTOR_PRODUCT_MAX_DEGREE", "5"))

    rng = random.Random(seed)
    partitions = _factor_degree_partitions(max_degree)
    if not partitions:
        return

    for case_index in range(cases):
        partition = partitions[case_index % len(partitions)]
        factors = [
            _random_primitive_nonmonic_integer_factor(rng, degree, bits)
            for degree in partition
        ]
        yield _integer_product_to_monic_q(factors)


def test_factorize_le5_random_nonmonic_primitive_products_vs_sympy() -> None:
    """Differential test for non-monic primitive Z[x] products over QQ."""
    checked = 0
    for coeffs in _iter_random_nonmonic_primitive_products():
        _assert_factorization_matches_sympy(coeffs)
        checked += 1

    assert checked > 0


# =============================================================================
# Quartic resolvent stress tests
# =============================================================================


def _quartic_pair_sums_resolvent(coeffs: list[Fraction]) -> list[Fraction]:
    """Return the pair-sums cubic resolvent of a monic quartic over QQ.

    For x^4 + a*x^3 + b*x^2 + c*x + d, first depress the quartic:

        y^4 + C*y^2 + D*y + E.

    The pair-sums resolvent is

        T^3 - 2*C*T^2 + (C^2 - 4*E)*T + D^2.
    """
    coeffs = _trim_desc_q([Fraction(c) for c in coeffs])
    if len(coeffs) != 5 or coeffs[0] != 1:
        raise ValueError(f"expected a monic quartic, got {coeffs!r}")

    _, a, b, c, d = coeffs
    C = b - Fraction(3, 8) * a * a
    D = c - Fraction(1, 2) * a * b + Fraction(1, 8) * a * a * a
    E = (
        d
        - Fraction(1, 4) * a * c
        + Fraction(1, 16) * a * a * b
        - Fraction(3, 256) * a**4
    )
    return _trim_desc_q([Fraction(1), -2 * C, C * C - 4 * E, D * D])


def _iter_quartic_resolvent_inputs() -> Iterator[list[Fraction]]:
    """Yield cubic resolvents produced by bounded monic integer quartics."""
    bound = int(os.getenv("OPENGALOIS_FACTOR_RESOLVENT_BOUND", "3"))

    seen: set[tuple[tuple[int, int], ...]] = set()
    for tail in itertools.product(range(-bound, bound + 1), repeat=4):
        quartic = [Fraction(1), *(Fraction(c) for c in tail)]
        resolvent = _quartic_pair_sums_resolvent(quartic)
        key = _poly_key_from_fraction_coeffs(resolvent)
        if key in seen:
            continue
        seen.add(key)
        yield resolvent


def test_factorize_le5_quartic_pair_sums_resolvents_vs_sympy() -> None:
    """Differential test on resolvents actually produced by the quartic pipeline."""
    checked = 0
    for coeffs in _iter_quartic_resolvent_inputs():
        _assert_factorization_matches_sympy(coeffs)
        checked += 1

    assert checked > 0


# =============================================================================
# Existing broad coverage: bounded boxes and large random integer inputs
# =============================================================================


def test_factorize_le5_bounded_exhaustive_vs_sympy() -> None:
    """Bounded exhaustive differential test against SymPy over QQ.

    Defaults are intentionally moderate. Increase the explored box with:

        OPENGALOIS_FACTOR_TEST_COEFF_BOUND=3
        OPENGALOIS_FACTOR_TEST_LEADING_BOUND=5
        OPENGALOIS_FACTOR_TEST_MAX_DEGREE=5

    The test is exhaustive over the finite box selected by those parameters.
    """
    checked = 0
    for coeffs in _bounded_test_inputs():
        _assert_factorization_matches_sympy(coeffs)
        checked += 1

    assert checked > 0


def _random_large_int(rng: random.Random, bits: int) -> int:
    """Return a deterministic pseudo-random integer with up to ``bits`` bits."""
    if bits <= 0:
        raise ValueError("bits must be positive")

    value = rng.getrandbits(bits)
    if value == 0:
        return 0
    return -value if rng.randrange(2) else value


def _random_monic_integer_poly(
    rng: random.Random,
    degree: int,
    bits: int,
) -> list[Fraction]:
    """Return a random monic integer polynomial of the requested degree."""
    return [Fraction(1), *[Fraction(_random_large_int(rng, bits)) for _ in range(degree)]]


def _random_monic_integer_factor(
    rng: random.Random,
    degree: int,
    bits: int,
) -> sp.Poly:
    """Return a random monic integer factor as a SymPy polynomial."""
    coeffs = _random_monic_integer_poly(rng, degree, bits)
    return _to_sympy_poly(coeffs)


def _random_reducible_monic_integer_poly(
    rng: random.Random,
    degree: int,
    bits: int,
) -> list[Fraction]:
    """Return a random reducible monic integer polynomial of total degree ``degree``."""
    if degree <= 1:
        return _random_monic_integer_poly(rng, degree, bits)

    remaining = degree
    factor_degrees: list[int] = []
    while remaining > 0:
        if remaining == 1:
            next_degree = 1
        else:
            next_degree = rng.randint(1, remaining - 1)
        factor_degrees.append(next_degree)
        remaining -= next_degree

    product_poly = sp.Poly(1, x, domain=sp.QQ)
    for factor_degree in factor_degrees:
        product_poly *= _random_monic_integer_factor(rng, factor_degree, bits)

    return [Fraction(int(coeff)) for coeff in product_poly.all_coeffs()]


def _random_large_integer_inputs() -> Iterator[list[Fraction]]:
    """Yield random monic integer inputs with configurable large coefficients.

    The default is deliberately moderate for normal CI, but the bit-size and
    sample count can be increased without changing the test code:

        OPENGALOIS_FACTOR_RANDOM_CASES=100
        OPENGALOIS_FACTOR_RANDOM_BITS=512
        OPENGALOIS_FACTOR_RANDOM_SEED=12345
    """
    cases = int(os.getenv("OPENGALOIS_FACTOR_RANDOM_CASES", "30"))
    bits = int(os.getenv("OPENGALOIS_FACTOR_RANDOM_BITS", "128"))
    seed = int(os.getenv("OPENGALOIS_FACTOR_RANDOM_SEED", "8675309"))
    max_degree = int(os.getenv("OPENGALOIS_FACTOR_RANDOM_MAX_DEGREE", "5"))

    rng = random.Random(seed)
    for case_index in range(cases):
        degree = 1 + (case_index % max_degree)
        if case_index % 2 == 0:
            yield _random_monic_integer_poly(rng, degree, bits)
        else:
            yield _random_reducible_monic_integer_poly(rng, degree, bits)


def test_factorize_le5_random_large_integer_coefficients_vs_sympy() -> None:
    """Differential test with deterministic large random integer coefficients."""
    checked = 0
    for coeffs in _random_large_integer_inputs():
        _assert_factorization_matches_sympy(coeffs)
        checked += 1

    assert checked > 0


# =============================================================================
# Irreducibility-trace coverage
# =============================================================================


def _iter_trace_stress_inputs() -> Iterator[list[Fraction]]:
    """Yield inputs used to validate Zassenhaus irreducibility-trace emission."""
    yield from _known_edge_cases()

    max_bounded = int(os.getenv("OPENGALOIS_FACTOR_TRACE_BOUNDED_CASES", "200"))
    yield from itertools.islice(_bounded_test_inputs(), max_bounded)

    max_resolvents = int(os.getenv("OPENGALOIS_FACTOR_TRACE_RESOLVENT_CASES", "400"))
    yield from itertools.islice(_iter_quartic_resolvent_inputs(), max_resolvents)

    max_products = int(os.getenv("OPENGALOIS_FACTOR_TRACE_PRODUCT_CASES", "80"))
    yield from itertools.islice(_iter_random_nonmonic_primitive_products(), max_products)


def test_zassenhaus_irreducibility_trace_agrees_with_sympy() -> None:
    """The trace helper must never certify a reducible polynomial as irreducible."""
    checked = 0
    for coeffs in _iter_trace_stress_inputs():
        _assert_zassenhaus_trace_matches_sympy(coeffs)
        checked += 1

    assert checked > 0
