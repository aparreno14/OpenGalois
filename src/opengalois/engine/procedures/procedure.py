from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ..context import EngineContext


@dataclass(frozen=True)
class ProcedureResult:
    """Result of running an engine-level procedure.

    Attributes:
        facts: Fact nodes (JSON dicts).
        out: Non-normative routing/output data for the engine (never verified).
    """
    facts: list[dict[str, Any]]
    out: dict[str, Any]


class Procedure(Protocol):
    """Engine-level decision procedure (implementation), not a proof node.

    A procedure orchestrates engine steps (Python) and emits fact nodes (JSON).
    """
    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Run the procedure on the given input reference, returning facts and output data."""
        ...