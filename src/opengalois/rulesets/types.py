from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import NewType

"""Types for OpenGalois v3 compiled rulesets.

Design goals:
  - Python-native (no YAML parsing in runtime / verifier TCB).
  - Small, explicit, stable.
  - Sufficient to gate: ruleset_id, predicate catalog (arity + kinds), allowed rules.

Rule id format convention:
  "<rule_name>@<int_version>"  e.g. "irreducible.QQ.deg5_recompute@1".
"""

RuleId = NewType("RuleId", str)


@dataclass(frozen=True, slots=True)
class PredicateSpec:
    """Specification of a predicate (fact) accepted by a ruleset.

    Attributes:
        name: Predicate name (e.g. "IrreducibleQQ").
        arg_kinds: Kind names for each argument, e.g. ("PolyQQ",).
        doc: Human-readable description (non-normative but useful in errors/UI).
    """

    name: str
    arg_kinds: tuple[str, ...]
    doc: str = ""


@dataclass(frozen=True, slots=True)
class RulesetSpec:
    """Compiled ruleset specification consumed by the verifier.

    Attributes:
        ruleset_id: Versioned identifier, e.g. "le5-core@1".
        version: Integer version (usually matches suffix after '@').
        predicates: Mapping from predicate name to its spec.
        allowed_rules: Set of rule ids allowed by this ruleset.
        doc: Optional short description of the ruleset.
    """

    ruleset_id: str
    version: int
    predicates: Mapping[str, PredicateSpec]
    allowed_rules: frozenset[RuleId]
    doc: str = ""


def parse_rule_id(rule_id: str) -> tuple[str, int]:
    """Parse a rule id of the form '<name>@<int>'.

    Args:
        rule_id: Rule identifier string.

    Returns:
        (name, version) where version is an int.

    Raises:
        ValueError: If the rule id does not match the expected format.
    """
    if "@" not in rule_id:
        raise ValueError(f"Invalid rule id (missing '@'): {rule_id!r}")
    name, ver = rule_id.rsplit("@", 1)
    if not name or not ver.isdigit():
        raise ValueError(f"Invalid rule id format: {rule_id!r}")
    return name, int(ver)
