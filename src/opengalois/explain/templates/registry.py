# ruff: noqa: D102,D103
"""Rule-template registry for clean mathematical explanations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..context import ExplainContext, FactView
from ..errors import ExplainMissingTemplateError, MissingTemplate
from ..proof_model import ProofBlock

Template = Callable[[FactView, ExplainContext], tuple[ProofBlock, ...]]
StatementTemplate = Callable[[FactView, ExplainContext], tuple[ProofBlock, ...]]


@dataclass
class TemplateRegistry:
    """Registry of narrative templates keyed by rule id."""

    rule_templates: dict[str, Template] = field(default_factory=dict)
    statement_templates: dict[str, StatementTemplate] = field(default_factory=dict)

    def register_rule(self, rule_id: str, template: Template) -> None:
        self.rule_templates[rule_id] = template

    def register_statement(self, pred: str, template: StatementTemplate) -> None:
        self.statement_templates[pred] = template

    def rule(self, rule_id: str) -> Template | None:
        return self.rule_templates.get(rule_id)

    def statement(self, pred: str) -> StatementTemplate | None:
        return self.statement_templates.get(pred)

    def require_templates(self, facts: tuple[FactView, ...]) -> None:
        missing = [
            MissingTemplate(rule_id=fact.rule_id, fact_id=fact.fact_id)
            for fact in facts
            if fact.rule_id not in self.rule_templates
        ]
        if missing:
            raise ExplainMissingTemplateError(missing)


def rule_template(rule_id: str) -> Callable[[Template], Template]:
    """Decorator registering a rule template in the default registry."""

    def decorator(template: Template) -> Template:
        get_default_registry().register_rule(rule_id, template)
        return template

    return decorator


def statement_template(pred: str) -> Callable[[StatementTemplate], StatementTemplate]:
    """Decorator registering a goal-statement template in the default registry."""

    def decorator(template: StatementTemplate) -> StatementTemplate:
        get_default_registry().register_statement(pred, template)
        return template

    return decorator


_DEFAULT_REGISTRY = TemplateRegistry()


def get_default_registry() -> TemplateRegistry:
    return _DEFAULT_REGISTRY
