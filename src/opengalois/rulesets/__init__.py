"""Built-in (compiled) ruleset registry for OpenGalois v3.

This package intentionally avoids runtime parsing of YAML/JSON ruleset specs.
Human-readable specs may live under `rulesets/` at the repository root, but the
verifier operates on Python-native dataclasses declared in this package.

Public API:
  - get_ruleset(ruleset_id)
  - list_rulesets()
  - register_ruleset(ruleset)
"""

# Import built-in rulesets so they self-register at import time.
# Keep this list explicit (no filesystem scanning) to avoid widening the TCB.
from . import le5_core_1 as _le5_core_1  # noqa: F401
from .registry import get_ruleset, list_rulesets, register_ruleset  # noqa: F401
from .types import PredicateSpec, RuleId, RulesetSpec, parse_rule_id  # noqa: F401
