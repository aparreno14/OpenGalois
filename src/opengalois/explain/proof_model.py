# ruff: noqa: D102,D103
"""Small intermediate representation for clean mathematical explanations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


@dataclass(frozen=True)
class Inline:
    """Inline text or mathematical content."""

    kind: str
    value: str


@dataclass(frozen=True)
class Paragraph:
    """A paragraph made from inline fragments."""

    parts: tuple[Inline, ...]


@dataclass(frozen=True)
class DisplayMath:
    """A displayed mathematical block."""

    value: str


ProofBlock: TypeAlias = Paragraph | DisplayMath


@dataclass(frozen=True)
class ProofStatement:
    """One statement and its generated proof."""

    fact_id: str
    statement: tuple[ProofBlock, ...]
    proof: tuple[ProofBlock, ...]


@dataclass(frozen=True)
class ProofDocument:
    """Clean explanation document: one or more statement/proof blocks."""

    title: str
    introduction: tuple[ProofBlock, ...]
    statements: tuple[ProofStatement, ...]
    metadata: dict[str, str] = field(default_factory=dict)


def text(value: str) -> Inline:
    return Inline("text", value)


def math(value: str) -> Inline:
    return Inline("math", value)


def display_math(value: str) -> DisplayMath:
    return DisplayMath(value)


def par(*parts: Inline | str) -> Paragraph:
    out: list[Inline] = []
    for part in parts:
        if isinstance(part, Inline):
            out.append(part)
        else:
            out.append(text(part))
    return Paragraph(tuple(out))
