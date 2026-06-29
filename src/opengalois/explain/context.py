# ruff: noqa: D102,D103
"""Certificate accessors for the explanation layer.

This module deliberately performs no mathematics. It only normalizes access to
objects, fact nodes and proof goals in an already produced certificate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from .errors import ExplainInvalidCertificateError

JsonMap = Mapping[str, Any]


@dataclass(frozen=True)
class FactView:
    """Read-only view of one certificate fact node."""

    index: int
    raw: JsonMap

    @property
    def fact_id(self) -> str:
        value = self.raw.get("id")
        if not isinstance(value, str) or not value:
            raise ExplainInvalidCertificateError("fact node has no valid id")
        return value

    @property
    def claim(self) -> JsonMap:
        value = self.raw.get("claim")
        if not isinstance(value, Mapping):
            raise ExplainInvalidCertificateError(f"fact {self.fact_id} has no claim")
        return cast(JsonMap, value)

    @property
    def pred(self) -> str:
        value = self.claim.get("pred")
        if not isinstance(value, str) or not value:
            raise ExplainInvalidCertificateError(f"fact {self.fact_id} has no predicate")
        return value

    @property
    def args(self) -> tuple[JsonMap, ...]:
        value = self.claim.get("args")
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise ExplainInvalidCertificateError(f"fact {self.fact_id} has invalid args")
        out: list[JsonMap] = []
        for arg in value:
            if not isinstance(arg, Mapping):
                raise ExplainInvalidCertificateError(
                    f"fact {self.fact_id} has a non-object argument"
                )
            out.append(cast(JsonMap, arg))
        return tuple(out)

    @property
    def rule_id(self) -> str:
        value = self.raw.get("rule")
        if not isinstance(value, str) or not value:
            raise ExplainInvalidCertificateError(f"fact {self.fact_id} has no rule")
        return value

    @property
    def premises(self) -> tuple[str, ...]:
        value = self.raw.get("premises", [])
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise ExplainInvalidCertificateError(
                f"fact {self.fact_id} has invalid premises"
            )
        premises: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item:
                raise ExplainInvalidCertificateError(
                    f"fact {self.fact_id} has an invalid premise id"
                )
            premises.append(item)
        return tuple(premises)

    def ref_arg(self, index: int) -> str:
        try:
            arg = self.args[index]
        except IndexError as exc:
            raise ExplainInvalidCertificateError(
                f"fact {self.fact_id} has no argument {index}"
            ) from exc
        ref = arg.get("ref")
        if not isinstance(ref, str) or not ref:
            raise ExplainInvalidCertificateError(
                f"fact {self.fact_id} argument {index} is not an object ref"
            )
        return ref


@dataclass(frozen=True)
class ExplainContext:
    """Normalized access to a certificate for explanation rendering."""

    certificate: JsonMap
    meta: JsonMap
    input_block: JsonMap
    objects: JsonMap
    proof: JsonMap
    facts: tuple[FactView, ...]
    fact_by_id: Mapping[str, FactView]
    goals: tuple[str, ...]

    @property
    def ruleset_id(self) -> str:
        value = self.meta.get("ruleset_id", "")
        return value if isinstance(value, str) else ""

    def get_fact(self, fact_id: str) -> FactView:
        try:
            return self.fact_by_id[fact_id]
        except KeyError as exc:
            raise ExplainInvalidCertificateError(f"unknown fact id: {fact_id}") from exc

    def get_object(self, ref: str) -> JsonMap:
        if ref == "$input":
            coeffs = self.input_block.get("coeffs_qq")
            if not isinstance(coeffs, Sequence) or isinstance(coeffs, (str, bytes)):
                raise ExplainInvalidCertificateError("input has no valid coeffs_qq")
            return {"kind": "PolyQQ", "coeffs_qq": list(coeffs)}
        value = self.objects.get(ref)
        if not isinstance(value, Mapping):
            raise ExplainInvalidCertificateError(f"unknown object ref: {ref}")
        return cast(JsonMap, value)


def _as_mapping(value: Any, name: str) -> JsonMap:
    if not isinstance(value, Mapping):
        raise ExplainInvalidCertificateError(f"certificate field {name!r} is missing")
    return cast(JsonMap, value)


def _load_facts(proof: JsonMap) -> tuple[FactView, ...]:
    raw_facts = proof.get("facts")
    if not isinstance(raw_facts, Sequence) or isinstance(raw_facts, (str, bytes)):
        raise ExplainInvalidCertificateError("certificate proof has no fact list")
    facts: list[FactView] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_facts):
        if not isinstance(raw, Mapping):
            raise ExplainInvalidCertificateError("proof.facts contains a non-object node")
        fact = FactView(index=index, raw=cast(JsonMap, raw))
        if fact.fact_id in seen:
            raise ExplainInvalidCertificateError(f"duplicate fact id: {fact.fact_id}")
        seen.add(fact.fact_id)
        facts.append(fact)
    if not facts:
        raise ExplainInvalidCertificateError("certificate proof has no facts")
    return tuple(facts)


def _load_goals(proof: JsonMap) -> tuple[str, ...]:
    raw_goals = proof.get("goals", [])
    if not isinstance(raw_goals, Sequence) or isinstance(raw_goals, (str, bytes)):
        raise ExplainInvalidCertificateError("proof.goals is not a list")
    goals: list[str] = []
    for goal in raw_goals:
        if not isinstance(goal, str) or not goal:
            raise ExplainInvalidCertificateError("proof.goals contains an invalid fact id")
        goals.append(goal)
    return tuple(goals)


def build_explain_context(certificate: JsonMap) -> ExplainContext:
    """Build a typed context from a certificate mapping."""
    meta = _as_mapping(certificate.get("meta"), "meta")
    input_block = _as_mapping(certificate.get("input"), "input")
    proof = _as_mapping(certificate.get("proof"), "proof")
    objects_raw = certificate.get("objects", {})
    objects = _as_mapping(objects_raw, "objects")
    facts = _load_facts(proof)
    fact_by_id = {fact.fact_id: fact for fact in facts}
    goals = _load_goals(proof)
    for goal in goals:
        if goal not in fact_by_id:
            raise ExplainInvalidCertificateError(f"proof goal {goal!r} is not a fact id")
    return ExplainContext(
        certificate=certificate,
        meta=meta,
        input_block=input_block,
        objects=objects,
        proof=proof,
        facts=facts,
        fact_by_id=fact_by_id,
        goals=goals,
    )
