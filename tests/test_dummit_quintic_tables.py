from __future__ import annotations

from fractions import Fraction

from opengalois.algorithms.dummit_quintic_tables import (
    F_POLY,
    eval_b1,
    eval_b2,
    eval_b3,
    eval_F,
    eval_T1,
    eval_T2,
    eval_T3,
    eval_T4,
)

# --- Tests for F ---

def test_F_has_expected_number_of_terms() -> None:
    assert len(F_POLY) == 46


def test_eval_F_at_zero() -> None:
    assert eval_F(p=Fraction(0), q=Fraction(0), r=Fraction(0), s=Fraction(0)) == 0


def test_eval_F_simple_point() -> None:
    assert eval_F(p=Fraction(0), q=Fraction(1), r=Fraction(0), s=Fraction(0)) == Fraction(216, 1)


def test_eval_F_example_f_x5_plus_15x_plus_12_is_nonzero() -> None:
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(15)
    s = Fraction(12)
    assert eval_F(p=p, q=q, r=r, s=s) != 0


# --- Tests for b1 and T1 ---

def test_eval_b10_and_T1_match_dummit_f20_example_with_theta_zero() -> None:
    # Example: f(x) = x^5 + 15x + 12.
    # In the paper, the resolvent sextic has theta = 0 as a rational root.
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(15)
    s = Fraction(12)
    theta = Fraction(0)

    # With theta = 0, T1 collapses to b10 / (2F).
    b10 = eval_b1(0, p=p, q=q, r=r, s=s)
    F = eval_F(p=p, q=q, r=r, s=s)
    assert b10 == -1500 * F
    assert eval_T1(p=p, q=q, r=r, s=s, theta=theta) == Fraction(750)


# --- Tests for b2 and T2 ---

def test_eval_b20_and_F_are_nonzero_on_dummit_dihedral_example() -> None:
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(-5)
    s = Fraction(12)
    assert eval_F(p=p, q=q, r=r, s=s) != 0
    assert eval_b2(0, p=p, q=q, r=r, s=s) != 0


def test_eval_T1_and_T2_match_dummits_dihedral_example() -> None:
    # Paper example: f(x)=x^5-5x+12, theta=40, A=8000.
    # The quadratic factors are:
    #   x^2 + 1250x + 6015625
    #   x^2 - 3750x + 44921875
    #
    # Using equation (7):
    #   coeffs are T1 ± T2*A
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(-5)
    s = Fraction(12)
    theta = Fraction(40)
    D = Fraction(64_000_000)
    A = Fraction(8_000)

    T1 = eval_T1(p=p, q=q, r=r, s=s, theta=theta)
    T2 = eval_T2(p=p, q=q, r=r, s=s, theta=theta, D=D)

    assert T1 == Fraction(-1250)
    assert T2 == Fraction(5, 16)

    assert T1 + T2 * A == Fraction(1250)
    assert T1 - T2 * A == Fraction(-3750)


# --- Tests for b3 and T3 ---

def test_eval_b30_and_F_are_nonzero_on_dummit_f20_example() -> None:
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(15)
    s = Fraction(12)
    assert eval_F(p=p, q=q, r=r, s=s) != 0
    assert eval_b3(0, p=p, q=q, r=r, s=s) != 0


def test_eval_T3_matches_dummits_f20_example() -> None:
    # Appendix-based value for f(x)=x^5+15x+12 with theta=0.
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(15)
    s = Fraction(12)
    theta = Fraction(0)

    T3 = eval_T3(p=p, q=q, r=r, s=s, theta=theta)
    assert T3 == Fraction(6_468_750)


# --- Tests for T4 ---

def test_eval_T3_and_T4_match_dummits_dihedral_example_quadratic_constants() -> None:
    # Paper example: f(x)=x^5-5x+12, theta=40, A=8000.
    # Equation (7) says the constant terms are T3 ± T4*A.
    # The paper gives:
    #   x^2 + 1250x + 6015625
    #   x^2 - 3750x + 4921875
    p = Fraction(0)
    q = Fraction(0)
    r = Fraction(-5)
    s = Fraction(12)
    theta = Fraction(40)
    D = Fraction(64_000_000)
    A = Fraction(8_000)

    T3 = eval_T3(p=p, q=q, r=r, s=s, theta=theta)
    T4 = eval_T4(p=p, q=q, r=r, s=s, theta=theta, D=D)

    assert T3 + T4 * A == Fraction(6_015_625)
    assert T3 - T4 * A == Fraction(4_921_875)

def test_example_3_cyclic_case_matches_dummit_for_T1_T2_T3_T4() -> None:
    # Dummit, Example (3):
    # f(x) = x^5 - 110x^3 - 55x^2 + 2310x + 979
    # theta = -9955
    #
    # The paper gives the quadratic factors in (7) with ordered roots:
    #   l1 = 797500, l4 = -61875
    #   l2 = 281875, l3 = -405625
    #
    # Hence:
    #   (x - 797500)(x + 61875)   = x^2 - 735625 x - 49345312500
    #   (x - 281875)(x + 405625)  = x^2 + 123750 x - 114335546875

    p = Fraction(-110)
    q = Fraction(-55)
    r = Fraction(2310)
    s = Fraction(979)
    theta = Fraction(-9955)

    # Exact discriminant of the polynomial, and its chosen square root A.
    D = Fraction(1_396_274_566_650_390_625)
    A = Fraction(1_181_640_625)

    T1 = eval_T1(p=p, q=q, r=r, s=s, theta=theta)
    T2 = eval_T2(p=p, q=q, r=r, s=s, theta=theta, D=D)
    T3 = eval_T3(p=p, q=q, r=r, s=s, theta=theta)
    T4 = eval_T4(p=p, q=q, r=r, s=s, theta=theta, D=D)

    assert T1 == Fraction(-611_875, 2)
    assert T2 == Fraction(-1, 2750)
    assert T3 == Fraction(-163_680_859_375, 2)
    assert T4 == Fraction(55, 2)

    assert T1 + T2 * A == Fraction(-735_625)
    assert T1 - T2 * A == Fraction(123_750)

    assert T3 + T4 * A == Fraction(-49_345_312_500)
    assert T3 - T4 * A == Fraction(-114_335_546_875)
