from __future__ import annotations

from dataclasses import dataclass

from opengalois.engine.procedures.irreducible.deg1 import IrreducibleDeg1Procedure
from opengalois.engine.procedures.irreducible.deg2 import IrreducibleDeg2Procedure
from opengalois.engine.procedures.irreducible.deg3 import IrreducibleDeg3Procedure
from opengalois.engine.procedures.irreducible.deg4 import IrreducibleDeg4Procedure
from opengalois.engine.procedures.irreducible.deg5 import IrreducibleDeg5Procedure
from opengalois.engine.procedures.procedure import Procedure
from opengalois.engine.procedures.reducible import ReducibleGaloisGroupProcedure
from opengalois.nodes.discriminant import DiscriminantNode
from opengalois.nodes.kappe_warren import KappeWarrenNode
from opengalois.nodes.normalize import NormalizeDepressedMonicQQ
from opengalois.nodes.reducibility import ReducibilityNode
from opengalois.nodes.resolvent import ResolventNode
from opengalois.nodes.square import SquareNode


@dataclass(frozen=True)
class EngineRegistry:
    """Central registry holding engine steps and procedures.

    Attributes:
        normalize_deg5: Engine step for degree-5 normalization.
        reducibility: Engine step for reducibility gate.
        irreducible_procedures: Degree-indexed procedures for irreducible workflows (1..5).
        reducible: Procedure for reducible workflows.
        discriminant: Node computing exact discriminants.
        square: Node classifying RatQQ objects as square/non-square.
        resolvent: Quartic resolvent node.
        kappe_warren: Kappe-Warren auxiliary node for quartic C4/D4 branching.
    """
    normalize_deg5: NormalizeDepressedMonicQQ
    reducibility: ReducibilityNode
    irreducible_procedures: dict[int, Procedure]
    reducible: ReducibleGaloisGroupProcedure
    discriminant: DiscriminantNode
    square: SquareNode
    resolvent: ResolventNode
    kappe_warren: KappeWarrenNode

    @staticmethod
    def default() -> EngineRegistry:
        """Construct a registry with the default production components."""
        return EngineRegistry(
            normalize_deg5=NormalizeDepressedMonicQQ(),
            reducibility=ReducibilityNode(),
            discriminant=DiscriminantNode(),
            square=SquareNode(),
            resolvent=ResolventNode(),
            kappe_warren=KappeWarrenNode(),
            irreducible_procedures={
                1: IrreducibleDeg1Procedure(),
                2: IrreducibleDeg2Procedure(),
                3: IrreducibleDeg3Procedure(),
                4: IrreducibleDeg4Procedure(),
                5: IrreducibleDeg5Procedure(),
            },
            reducible=ReducibleGaloisGroupProcedure(),
        )