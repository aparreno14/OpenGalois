from __future__ import annotations

from .types import RulesetSpec

"""Ruleset registry for OpenGalois v3.

This registry is intentionally *compiled* and Python-native.
It must not parse YAML at runtime.

Pattern:
  - Each built-in ruleset module defines a `RULESET: RulesetSpec` constant.
  - That module calls `register_ruleset(RULESET)` at import time (or you import it
    from a central place during application init).

In early migrations, the registry can be empty; the verifier will reject unknown
`meta.ruleset_id` values.
"""

_REGISTRY: dict[str, RulesetSpec] = {}


def register_ruleset(ruleset: RulesetSpec) -> None:
    """Register a compiled ruleset.

    Args:
        ruleset: The compiled ruleset specification.

    Raises:
        ValueError: If a ruleset with the same id is already registered.
    """
    existing = _REGISTRY.get(ruleset.ruleset_id)
    if existing is not None:
        raise ValueError(
            f"Ruleset already registered: {ruleset.ruleset_id!r} "
            f"(existing version={existing.version}, new version={ruleset.version})"
        )
    _REGISTRY[ruleset.ruleset_id] = ruleset


def get_ruleset(ruleset_id: str) -> RulesetSpec:
    """Look up a ruleset by id.

    Args:
        ruleset_id: Versioned ruleset identifier.

    Returns:
        The compiled RulesetSpec.

    Raises:
        KeyError: If the ruleset is not registered.
    """
    try:
        return _REGISTRY[ruleset_id]
    except KeyError as e:
        known = ", ".join(sorted(_REGISTRY.keys())) or "<none>"
        raise KeyError(f"Unknown ruleset_id: {ruleset_id!r}. Known: {known}") from e


def list_rulesets() -> list[str]:
    """Return a sorted list of registered ruleset ids."""
    return sorted(_REGISTRY.keys())
