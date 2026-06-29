#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    print("ERROR: PyYAML is required to run this script (dev/CI only).")
    print("Install with: pip install pyyaml")
    raise

from opengalois.rulesets import get_ruleset


@dataclass(frozen=True)
class Issue:
    """Represents an issue found during ruleset consistency checks.

    Attributes:
        code (str): The error code associated with the issue.
        message (str): A detailed message describing the issue.
    """
    code: str
    message: str


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary.

    Args:
        path (Path): The path to the YAML file.

    Returns:
        dict[str, Any]: The contents of the YAML file.

    Raises:
        TypeError: If the root of the YAML file is not a mapping.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"YAML root must be a mapping: {path}")
    return data


def _collect_yaml_predicates(facts_yaml: Path) -> dict[str, int]:
    """Collect predicates and their arities from a facts.yaml file.

    Args:
        facts_yaml (Path): The path to the facts.yaml file.

    Returns:
        dict[str, int]: A dictionary mapping predicate names to their arities.

    Raises:
        TypeError: If the predicates or their specifications are invalid.
    """
    data = _load_yaml(facts_yaml)
    preds = data.get("predicates")
    if not isinstance(preds, dict):
        raise TypeError(f"facts.yaml missing 'predicates' mapping: {facts_yaml}")
    out: dict[str, int] = {}
    for name, spec in preds.items():
        if not isinstance(name, str) or not name:
            raise TypeError(f"Invalid predicate name in {facts_yaml}: {name!r}")
        if not isinstance(spec, dict):
            raise TypeError(f"Invalid predicate spec for {name} in {facts_yaml}")
        args = spec.get("args")
        if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
            raise TypeError(f"Predicate {name} in {facts_yaml} must have args: [<kind>, ...]")
        out[name] = len(args)
    return out


def _collect_yaml_rule_ids(rules_dir: Path) -> dict[str, Path]:
    """Collect rule IDs and their file paths from a directory of YAML rule files.

    Args:
        rules_dir (Path): The directory containing YAML rule files.

    Returns:
        dict[str, Path]: A dictionary mapping rule IDs to their file paths.

    Raises:
        TypeError: If a rule file is missing an 'id' field or has an invalid ID.
        ValueError: If duplicate rule IDs are found.
    """
    out: dict[str, Path] = {}
    for p in sorted(rules_dir.glob("*.yaml")):
        data = _load_yaml(p)
        rid = data.get("id")
        if not isinstance(rid, str) or not rid:
            raise TypeError(f"Rule YAML missing string 'id': {p}")
        if rid in out:
            raise ValueError(f"Duplicate rule id {rid!r} in {p} and {out[rid]}")
        out[rid] = p
    return out


def _fixture_path(root: Path, ruleset_id: str, kind: str, rule_id: str) -> Path:
    """Construct the path to a fixture file based on its ruleset, kind, and rule ID.

    Args:
        root (Path): The root directory of the repository.
        ruleset_id (str): The ID of the ruleset.
        kind (str): The kind of fixture ('ok' or 'bad').
        rule_id (str): The ID of the rule.

    Returns:
        Path: The constructed path to the fixture file.

    Raises:
        ValueError: If the kind is not 'ok' or 'bad'.
    """
    # Convention used in this repo:
    #   ok:  <rule_id>_001.json
    #   bad: <rule_id>_fail_001.json
    if kind == "ok":
        name = f"{rule_id}_001.json"
    elif kind == "bad":
        name = f"{rule_id}_fail_001.json"
    else:
        raise ValueError(kind)
    return root / "fixtures" / "v3" / ruleset_id / kind / name


def main(argv: list[str]) -> int:
    """Perform consistency checks between YAML ruleset specifications and Python catalogs.

    This script verifies that the YAML ruleset specifications match the compiled Python
    catalogs and that all required fixtures are present.

    Args:
        argv (list[str]): Command-line arguments passed to the script.

    Returns:
        int: Exit code (0 if all checks pass, 1 otherwise).
    """
    ap = argparse.ArgumentParser(
        description="CI-only consistency checks: YAML ruleset spec ↔"
        " compiled Python catalog + fixture coverage."
    )
    ap.add_argument("--ruleset", default="le5-core@1",
                    help="Ruleset id to check (default: le5-core@1).")
    ap.add_argument(
        "--repo-root",
        default=".",
        help="Repo root (default: current directory).",
    )
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    ruleset_id = args.ruleset

    issues: list[Issue] = []

    facts_yaml = repo_root / "rulesets" / ruleset_id / "facts.yaml"
    rules_dir = repo_root / "rulesets" / ruleset_id / "rules"

    if not facts_yaml.is_file():
        issues.append(Issue("E_PATH", f"Missing facts.yaml: {facts_yaml}"))
        facts_yaml_ok = False
    else:
        facts_yaml_ok = True

    if not rules_dir.is_dir():
        issues.append(Issue("E_PATH", f"Missing rules directory: {rules_dir}"))
        rules_dir_ok = False
    else:
        rules_dir_ok = True

    # Load compiled ruleset (runtime catalog)
    try:
        compiled = get_ruleset(ruleset_id)
    except Exception as e:
        issues.append(Issue("E_COMPILED", f"Cannot load compiled ruleset {ruleset_id!r}: {e}"))
        compiled = None

    # Predicates: YAML ↔ compiled
    if facts_yaml_ok and compiled is not None:
        yaml_pred_arity = _collect_yaml_predicates(facts_yaml)
        compiled_pred_arity = {name: len(spec.arg_kinds) for name, spec 
                               in compiled.predicates.items()}

        yaml_names = set(yaml_pred_arity)
        comp_names = set(compiled_pred_arity)

        extra_yaml = sorted(yaml_names - comp_names)
        extra_comp = sorted(comp_names - yaml_names)

        if extra_yaml:
            issues.append(Issue("E_PRED", 
                                f"Predicates present in YAML but missing in "
                                f"compiled: {extra_yaml}"))
        if extra_comp:
            issues.append(Issue("E_PRED", 
                                f"Predicates present in compiled but missing "
                                f"in YAML: {extra_comp}"))

        for name in sorted(yaml_names & comp_names):
            if yaml_pred_arity[name] != compiled_pred_arity[name]:
                issues.append(
                    Issue(
                        "E_PRED_ARITY",
                        f"Arity mismatch for predicate {name}: YAML={yaml_pred_arity[name]}"
                        f" compiled={compiled_pred_arity[name]}",
                    )
                )

    # Rules: YAML ↔ compiled allowed_rules
    yaml_rules: dict[str, Path] = {}
    if rules_dir_ok:
        yaml_rules = _collect_yaml_rule_ids(rules_dir)

    if compiled is not None:
        compiled_rule_ids = sorted(str(x) for x in compiled.allowed_rules)
        yaml_rule_ids = sorted(yaml_rules.keys())

        extra_yaml_rules = sorted(set(yaml_rule_ids) - set(compiled_rule_ids))
        extra_compiled_rules = sorted(set(compiled_rule_ids) - set(yaml_rule_ids))

        if extra_yaml_rules:
            issues.append(Issue("E_RULE", 
                                f"Rules present in YAML but missing in "
                                f"compiled allowed_rules: {extra_yaml_rules}"))
        if extra_compiled_rules:
            issues.append(Issue("E_RULE",
                                f"Rules present in compiled "
                                f"allowed_rules but missing YAML file: {extra_compiled_rules}"))

    # Fixture coverage per rule id (based on YAML rule ids)
    for rid in sorted(yaml_rules.keys()):
        okp = _fixture_path(repo_root, ruleset_id, "ok", rid)
        badp = _fixture_path(repo_root, ruleset_id, "bad", rid)
        if not okp.is_file():
            issues.append(Issue("E_FIXTURE", f"Missing OK fixture for rule {rid}: {okp}"))
        if not badp.is_file():
            issues.append(Issue("E_FIXTURE", f"Missing BAD fixture for rule {rid}: {badp}"))

    if issues:
        print(f"[FAIL] ruleset consistency checks for {ruleset_id}")
        for it in issues:
            print(f"  - {it.code}: {it.message}")
        return 1

    print(f"[OK] ruleset consistency checks passed for {ruleset_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
