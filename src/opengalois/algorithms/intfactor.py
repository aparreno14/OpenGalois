from __future__ import annotations

import random
from functools import lru_cache
from math import gcd


def _small_primes(limit: int = 1000) -> list[int]:
    """Return all prime numbers up to and including ``limit``.

    This uses a simple sieve of Eratosthenes and is intended for bootstrapping
    the small-prime table used by the primality and factorization routines.

    Args:
        limit: Upper bound for the sieve, inclusive.

    Returns:
        A list of all primes ``p`` such that ``2 <= p <= limit``.
    """
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    p = 2
    while p * p <= limit:
        if sieve[p]:
            start = p * p
            sieve[start : limit + 1 : p] = b"\x00" * (((limit - start) // p) + 1)
        p += 1
    return [i for i, ok in enumerate(sieve) if ok]


_SMALL_PRIMES = _small_primes(1000)
_MR64_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)


def _ctz(n: int) -> int:
    """Return the number of trailing zero bits in a positive integer.

    Args:
        n: A positive integer.

    Returns:
        The largest integer ``k >= 0`` such that ``2**k`` divides ``n``.

    Raises:
        ValueError: This function is mathematically undefined for ``n <= 0``.
            The current implementation assumes callers only pass positive
            integers.
    """
    return (n & -n).bit_length() - 1


def is_probable_prime(n: int) -> bool:
    """Test whether ``n`` is prime using Miller-Rabin.

    The routine first strips divisibility by a table of small primes. It then
    runs Miller-Rabin on a fixed set of bases.

    For ``n < 2**64``, the selected bases are deterministic and give an exact
    primality test. For larger integers, the test remains a strong probable
    prime test using a fixed heuristic base set.

    Args:
        n: Integer to test.

    Returns:
        ``True`` if ``n`` is prime or a strong probable prime to the chosen
        bases, and ``False`` if ``n`` is definitely composite.
    """
    if n < 2:
        return False

    for p in _SMALL_PRIMES:
        if n % p == 0:
            return n == p

    d = n - 1
    s = _ctz(d)
    d >>= s

    bases: tuple[int, ...]

    if n < (1 << 64):
        bases = _MR64_BASES
    else:
        bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _pollard_brent(n: int, rng: random.Random) -> int:
    """Return a non-trivial factor of a composite integer.

    This implements Pollard's rho method with Brent's cycle detection variant.
    It is intended for odd composite integers not divisible by 3, though the
    function also handles the trivial factors 2 and 3 directly.

    Args:
        n: Integer to factor. Expected to be composite and greater than 1.
        rng: Random generator used to choose the polynomial parameters.

    Returns:
        A non-trivial factor ``d`` such that ``1 < d < n``.
    """
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3

    while True:
        y = rng.randrange(1, n - 1)
        c = rng.randrange(1, n - 1)
        m = 128

        g = 1
        r = 1
        q = 1
        x = 0
        ys = 0

        while g == 1:
            x = y
            for _ in range(r):
                y = (y * y + c) % n

            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n
                    q = (q * abs(x - y)) % n
                g = gcd(q, n)
                k += m

            r <<= 1

        if g == n:
            while True:
                ys = (ys * ys + c) % n
                g = gcd(abs(x - ys), n)
                if g > 1:
                    break

        if 1 < g < n:
            return g


def factorint(n: int) -> dict[int, int]:
    """Factor an integer into its prime-power decomposition.

    The factorization pipeline is:

    1. Normalize the sign with ``abs``.
    2. Strip a table of small prime factors.
    3. Recursively split the remaining cofactor using Miller-Rabin and
       Pollard-Brent.

    The returned mapping contains only positive prime factors. Sign handling is
    intentionally left to the caller.

    Args:
        n: Integer to factor.

    Returns:
        A dictionary mapping each prime divisor of ``|n|`` to its exponent.
        For ``|n| < 2``, returns an empty dictionary.
    """
    n = abs(n)
    if n < 2:
        return {}

    fac: dict[int, int] = {}

    for p in _SMALL_PRIMES:
        if p * p > n:
            break
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        if e:
            fac[p] = e

    if n == 1:
        return fac

    # Deterministic seed per input value for stable behavior across runs.
    rng = random.Random(n)
    stack = [n]

    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if is_probable_prime(m):
            fac[m] = fac.get(m, 0) + 1
            continue
        d = _pollard_brent(m, rng)
        stack.append(d)
        stack.append(m // d)

    return dict(sorted(fac.items()))


def divisors_from_factorization(fac: dict[int, int]) -> list[int]:
    """Enumerate all positive divisors from a prime factorization.

    Args:
        fac: Prime factorization represented as ``{prime: exponent}``.

    Returns:
        A sorted list of all positive divisors represented by ``fac``.

    Example:
        ``{2: 2, 3: 1}`` produces ``[1, 2, 3, 4, 6, 12]``.
    """
    divs = [1]
    for p, e in fac.items():
        next_divs: list[int] = []
        pe = 1
        for _ in range(e + 1):
            for d in divs:
                next_divs.append(d * pe)
            pe *= p
        divs = next_divs
    return sorted(divs)


@lru_cache(maxsize=4096)
def int_divisors(n: int) -> tuple[int, ...]:
    """Return all positive divisors of ``|n|``.

    Results are cached because divisor enumeration may be requested repeatedly
    for the same integers during polynomial factorization workflows.

    Args:
        n: Integer whose divisors are requested.

    Returns:
        A sorted tuple of all positive divisors of ``|n|``. For ``n == 0``,
        returns ``(0,)`` as a sentinel value used by the caller's existing
        conventions.
    """
    n = abs(n)
    if n == 0:
        return (0,)
    return tuple(divisors_from_factorization(factorint(n)))