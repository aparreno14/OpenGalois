from collections.abc import Sequence
from fractions import Fraction


def _frac_to_str(f: Fraction) -> str:
    """Convert a Fraction to a canonical string representation."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"

def _parse_fraction(s: str) -> Fraction:
    if "/" in s:
        p, q = s.split("/", 1)
        return Fraction(int(p.strip()), int(q.strip()))
    return Fraction(int(s.strip()), 1)

def _is_canonical_rational_str(s: str) -> bool:
    """Strong canonicality: Fraction(s) re-encodes to exactly s."""
    try:
        f = _parse_fraction(s)
    except Exception:
        return False
    return _frac_to_str(f) == s

def _poly_to_str(coeffs_qq: Sequence[str], *, var: str = "x") -> str:
    """Render descending QQ coefficients as a compact polynomial string.

    Args:
        coeffs_qq: Polynomial coefficients in descending-degree order.
        var: Variable name.

    Returns:
        Compact polynomial rendering.
    """
    terms: list[str] = []
    degree = len(coeffs_qq) - 1

    for i, coeff_s in enumerate(coeffs_qq):
        coeff = Fraction(coeff_s)
        if coeff == 0:
            continue

        exp = degree - i
        sign = "-" if coeff < 0 else "+"
        abs_coeff = -coeff if coeff < 0 else coeff
        abs_coeff_s = _frac_to_str(abs_coeff)

        if exp == 0:
            body = abs_coeff_s
        else:
            coeff_part = "" if abs_coeff == 1 else f"{abs_coeff_s}*"
            if exp == 1:
                body = f"{coeff_part}{var}"
            else:
                body = f"{coeff_part}{var}^{exp}"

        if not terms:
            terms.append(body if coeff > 0 else f"-{body}")
        else:
            terms.append(f" {sign} {body}")

    return "".join(terms) if terms else "0"