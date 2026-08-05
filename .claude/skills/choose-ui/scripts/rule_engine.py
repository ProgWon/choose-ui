#!/usr/bin/env python3
"""Shared table-driven rule engine for Choose UI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).resolve().parent.parent / "references" / "selection-rules.json"


@dataclass(frozen=True)
class Decision:
    rule_id: str
    recommendation: str
    confidence: str
    why: str
    avoid: str
    required_states: list[str]
    accessibility: str
    assumptions: list[str]
    evidence: list[str]


def load_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def normalize(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    intent = payload.get("intent", "input")
    options = payload.get("options")
    if options is None:
        raise ValueError("options is required")
    if not isinstance(options, int) or isinstance(options, bool):
        raise ValueError("options must be an integer")
    if options < 0:
        raise ValueError("options cannot be negative")

    expected_max = payload.get("expected_max_options", options)
    if not isinstance(expected_max, int) or isinstance(expected_max, bool):
        raise ValueError("expected_max_options must be an integer")
    if expected_max < options:
        raise ValueError("expected_max_options cannot be smaller than options")

    assumptions: list[str] = []
    value_kind = payload.get("value_kind")
    if value_kind is None:
        value_kind = "boolean" if intent == "setting" and options == 1 else "selection"
        if value_kind == "boolean":
            assumptions.append("Inferred a Boolean setting from intent=setting and options=1.")

    default_effect = "immediate" if intent in {"filter", "view-switch"} else "submit"
    context = {
        "intent": intent,
        "options": options,
        "expected_max_options": expected_max,
        "effective_options": max(options, expected_max),
        "value_kind": value_kind,
        "selection": payload.get("selection", "single"),
        "comparison": payload.get("comparison", "low"),
        "platform": payload.get("platform", "any"),
        "effect": payload.get("effect", default_effect),
        "frequency": payload.get("frequency", "low"),
        "search": bool(payload.get("search", False)),
        "custom_value": bool(payload.get("custom_value", False)),
        "rich_options": bool(payload.get("rich_options", False)),
    }

    allowed = {
        "intent": {"input", "filter", "view-switch", "action", "navigation", "setting"},
        "value_kind": {"selection", "boolean"},
        "selection": {"single", "multiple"},
        "comparison": {"low", "high"},
        "platform": {"any", "mobile", "desktop"},
        "effect": {"submit", "immediate"},
        "frequency": {"low", "high"},
    }
    for field, values in allowed.items():
        if context[field] not in values:
            raise ValueError(f"{field} must be one of: {', '.join(sorted(values))}")

    if expected_max > options:
        assumptions.append(
            f"Designed for the credible upper bound of {expected_max} options, not the current {options}."
        )
    return context, assumptions


def resolve_number(value: Any, thresholds: dict[str, int]) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value in thresholds:
        return thresholds[value]
    raise ValueError(f"unknown numeric value or threshold: {value}")


def numeric_match(actual: int, predicate: dict[str, Any], thresholds: dict[str, int]) -> bool:
    bounds = {
        "min": lambda value: actual >= resolve_number(value, thresholds),
        "max": lambda value: actual <= resolve_number(value, thresholds),
        "min_ref": lambda value: actual >= resolve_number(value, thresholds),
        "max_ref": lambda value: actual <= resolve_number(value, thresholds),
        "min_exclusive_ref": lambda value: actual > resolve_number(value, thresholds),
        "max_exclusive_ref": lambda value: actual < resolve_number(value, thresholds),
    }
    return all(bounds[key](value) for key, value in predicate.items())


def rule_matches(rule: dict[str, Any], context: dict[str, Any], thresholds: dict[str, int]) -> bool:
    for field, expected in rule["when"].items():
        actual = context[field]
        if isinstance(expected, dict):
            if not numeric_match(actual, expected, thresholds):
                return False
        elif isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def choose_ui(payload: dict[str, Any], rulebook: dict[str, Any] | None = None) -> Decision:
    rulebook = rulebook or load_rules()
    context, assumptions = normalize(payload)
    thresholds = rulebook["thresholds"]
    source_urls = rulebook["sources"]

    for rule in rulebook["rules"]:
        if not rule_matches(rule, context, thresholds):
            continue
        rule_assumptions = assumptions.copy()
        if rule.get("assumption"):
            rule_assumptions.append(rule["assumption"])
        return Decision(
            rule_id=rule["id"],
            recommendation=rule["recommendation"],
            confidence=rule["confidence"],
            why=rule["reason"],
            avoid=rule["avoid"],
            required_states=rule["states"],
            accessibility=rule["accessibility"],
            assumptions=rule_assumptions,
            evidence=[source_urls[source_id] for source_id in rule.get("evidence", [])],
        )

    return Decision(
        rule_id="manual-context-required",
        recommendation="manual product decision",
        confidence="low",
        why="The canonical rules do not cover this combination without more product context.",
        avoid="Do not force the request through a different intent's fallback rule.",
        required_states=["default", "focus", "disabled", "loading", "empty", "error"],
        accessibility="Preserve native semantics and keyboard behavior while the pattern is resolved.",
        assumptions=assumptions + ["One missing decision factor could change the component family."],
        evidence=[],
    )
