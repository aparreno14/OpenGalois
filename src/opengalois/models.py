from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Status(str, Enum):
    """High-level classification outcome for the analyzed polynomial."""
    ok = "ok"
    irreducible = "irreducible"
    reducible = "reducible"
    unclassified = "unclassified"
    error = "error"


class GaloisGroup(str, Enum):
    """Supported/declared Galois group labels for degree-5 workflows."""
    C5 = "C5"
    D5 = "D5"
    F20 = "F20"
    A5 = "A5"
    S5 = "S5"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class AnalysisOptions:
    """Options controlling certificate generation and optional explanation output."""
    explain: bool = False

@dataclass(frozen=True)
class CheckResult:
    """One named verification check with boolean status and optional details."""
    name: str
    ok: bool
    details: str = ""


@dataclass(frozen=True)
class Result:
    """Top-level API result returned by :func:`opengalois.analyze`."""
    status: Status
    solvable_by_radicals: bool | None
    galois_group: GaloisGroup
    certificate: dict[str, Any]
    explanation: str | None = None


@dataclass(frozen=True)
class VerifiedResult:
    """Aggregate outcome of running certificate verification checks."""
    verified: bool
    checks: tuple[CheckResult, ...]
