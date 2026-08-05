#!/usr/bin/env python3
"""Validate canonical Choose UI rules and render their reference matrix."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from rule_engine import RULES_PATH, load_rules


MATRIX_PATH = RULES_PATH.with_name("selection-controls.md")
CONTEXT_FIELDS = {
    "intent",
    "options",
    "effective_options",
    "value_kind",
    "selection",
    "comparison",
    "platform",
    "effect",
    "frequency",
    "search",
    "custom_value",
    "rich_options",
}
NUMERIC_OPERATORS = {
    "min": "≥",
    "max": "≤",
    "min_ref": "≥",
    "max_ref": "≤",
    "min_exclusive_ref": ">",
    "max_exclusive_ref": "<",
}
REQUIRED_RULE_FIELDS = {
    "id",
    "section",
    "when",
    "recommendation",
    "confidence",
    "avoid",
    "reason",
    "states",
    "accessibility",
}


def validate(rulebook: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if rulebook.get("version") != 2:
        errors.append("version must be 2")

    thresholds = rulebook.get("thresholds", {})
    if not isinstance(thresholds, dict) or not thresholds:
        errors.append("thresholds must be a non-empty object")
        thresholds = {}
    for name, value in thresholds.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"threshold {name!r} must be a positive integer")

    sources = rulebook.get("sources", {})
    if not isinstance(sources, dict):
        errors.append("sources must be an object")
        sources = {}

    rules = rulebook.get("rules", [])
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    covered_intents: set[str] = set()
    used_fields: set[str] = set()
    for index, rule in enumerate(rules):
        prefix = f"rule[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = sorted(REQUIRED_RULE_FIELDS - rule.keys())
        if missing:
            errors.append(f"{prefix} missing: {', '.join(missing)}")
        rule_id = rule.get("id")
        if rule_id in seen_ids:
            errors.append(f"duplicate rule id: {rule_id}")
        elif isinstance(rule_id, str):
            seen_ids.add(rule_id)

        confidence = rule.get("confidence")
        if confidence not in {"high", "medium", "low"}:
            errors.append(f"{prefix} confidence must be high, medium, or low")

        when = rule.get("when", {})
        if not isinstance(when, dict) or not when:
            errors.append(f"{prefix} when must be a non-empty object")
            continue
        unknown_fields = set(when) - CONTEXT_FIELDS
        if unknown_fields:
            errors.append(f"{prefix} has unknown condition fields: {sorted(unknown_fields)}")
        used_fields.update(when)

        intents = when.get("intent")
        if isinstance(intents, str):
            covered_intents.add(intents)
        elif isinstance(intents, list):
            covered_intents.update(item for item in intents if isinstance(item, str))

        for field, predicate in when.items():
            if not isinstance(predicate, dict):
                continue
            unknown_operators = set(predicate) - NUMERIC_OPERATORS.keys()
            if unknown_operators:
                errors.append(
                    f"{prefix}.{field} has unknown numeric operators: {sorted(unknown_operators)}"
                )
            for operator, reference in predicate.items():
                if operator.endswith("_ref") and reference not in thresholds:
                    errors.append(f"{prefix}.{field} references unknown threshold: {reference}")
                if not operator.endswith("_ref") and (
                    not isinstance(reference, int) or isinstance(reference, bool)
                ):
                    errors.append(f"{prefix}.{field}.{operator} must be an integer")

        evidence = rule.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{prefix} evidence must be an array")
        else:
            for source_id in evidence:
                if source_id not in sources:
                    errors.append(f"{prefix} references unknown source: {source_id}")

        states = rule.get("states")
        if not isinstance(states, list) or not states:
            errors.append(f"{prefix} states must be a non-empty array")

    required_intents = {"input", "filter", "view-switch", "action", "navigation", "setting"}
    if missing_intents := required_intents - covered_intents:
        errors.append(f"intents without explicit rules: {sorted(missing_intents)}")

    decision_fields = {
        "comparison",
        "frequency",
        "search",
        "custom_value",
        "rich_options",
        "platform",
        "effect",
    }
    if unused := decision_fields - used_fields:
        errors.append(f"decision factors unused by rules: {sorted(unused)}")
    return errors


def display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return " / ".join(str(item) for item in value)
    return str(value)


def describe_conditions(when: dict[str, Any], thresholds: dict[str, int]) -> str:
    parts: list[str] = []
    labels = {
        "effective_options": "options at credible maximum",
        "custom_value": "custom values",
        "rich_options": "rich option content",
    }
    for field, expected in when.items():
        label = labels.get(field, field.replace("_", " "))
        if not isinstance(expected, dict):
            parts.append(f"{label}: {display_value(expected)}")
            continue
        bounds: list[str] = []
        for operator, value in expected.items():
            if operator.endswith("_ref"):
                bounds.append(f"{NUMERIC_OPERATORS[operator]} {thresholds[value]} (`{value}`)")
            else:
                bounds.append(f"{NUMERIC_OPERATORS[operator]} {value}")
        parts.append(f"{label} {' and '.join(bounds)}")
    return "; ".join(parts)


def render(rulebook: dict[str, Any]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in rulebook["rules"]:
        grouped[rule["section"]].append(rule)

    lines = [
        "# Selection Controls",
        "",
        "> Generated from `selection-rules.json`. Do not edit this matrix by hand. Run `python3 .claude/skills/choose-ui/scripts/rules_tool.py --write` after changing canonical rules.",
        "",
        "Rules are ordered: the first matching row wins. Numeric boundaries are defaults, not laws; product research, content, localization, platform conventions, or an established design system may justify an explicit override.",
        "",
        "## Canonical thresholds",
        "",
        "| Name | Value |",
        "| --- | ---: |",
    ]
    for name, value in rulebook["thresholds"].items():
        lines.append(f"| `{name}` | {value} |")

    for section, rules in grouped.items():
        lines.extend(
            [
                "",
                f"## {section}",
                "",
                "| Rule | Match | Choose | Avoid | Why |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for rule in rules:
            condition = describe_conditions(rule["when"], rulebook["thresholds"])
            lines.append(
                f"| `{rule['id']}` | {condition} | {rule['recommendation']} | "
                f"{rule['avoid']} | {rule['reason']} |"
            )

    lines.extend(
        [
            "",
            "## Context beyond the table",
            "",
            "Use `decision-factors.md` when a threshold needs an override. Use `design-system-adapter.md` to translate the generic recommendation to components already present in a product. Use `accessibility.md` before implementing a custom widget.",
            "",
        ]
    )
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    mode = cli.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if the matrix is stale.")
    mode.add_argument("--write", action="store_true", help="Regenerate the matrix.")
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        rulebook = load_rules()
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors = validate(rulebook)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    output = render(rulebook)
    if args.check:
        try:
            current = MATRIX_PATH.read_text(encoding="utf-8")
        except OSError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        if current != output:
            print("error: selection-controls.md is stale; run rules_tool.py --write", file=sys.stderr)
            return 1
        print("rules valid; generated matrix is current")
        return 0
    if args.write:
        MATRIX_PATH.write_text(output, encoding="utf-8")
        print(f"wrote {MATRIX_PATH}")
        return 0
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
