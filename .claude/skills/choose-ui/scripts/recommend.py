#!/usr/bin/env python3
"""Return a deterministic Choose UI baseline from canonical declarative rules."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from rule_engine import Decision, choose_ui


def render_text(result: Decision) -> str:
    assumptions = "; ".join(result.assumptions) if result.assumptions else "None"
    evidence = ", ".join(result.evidence) if result.evidence else "None"
    return "\n".join(
        [
            f"Recommendation: {result.recommendation}",
            f"Confidence: {result.confidence}",
            f"Why: {result.why}",
            f"Avoid: {result.avoid}",
            f"Required states: {', '.join(result.required_states)}",
            f"Accessibility: {result.accessibility}",
            f"Assumptions: {assumptions}",
            f"Evidence: {evidence}",
            f"Rule: {result.rule_id}",
        ]
    )


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", type=Path, help="Read constraints from a JSON object.")
    cli.add_argument("--intent", choices=["input", "filter", "view-switch", "action", "navigation", "setting"])
    cli.add_argument("--options", type=int)
    cli.add_argument("--expected-max-options", type=int)
    cli.add_argument("--value-kind", choices=["selection", "boolean"])
    cli.add_argument("--selection", choices=["single", "multiple"], default="single")
    cli.add_argument("--comparison", choices=["low", "high"], default="low")
    cli.add_argument("--platform", choices=["any", "mobile", "desktop"], default="any")
    cli.add_argument("--effect", choices=["submit", "immediate"])
    cli.add_argument("--frequency", choices=["low", "high"], default="low")
    cli.add_argument("--search", action="store_true")
    cli.add_argument("--custom-value", action="store_true")
    cli.add_argument("--rich-options", action="store_true")
    cli.add_argument("--format", choices=["text", "json"], default="text")
    return cli


def payload_from_args(args: argparse.Namespace) -> dict[str, object]:
    payload: dict[str, object] = {
        "intent": args.intent or "input",
        "options": args.options,
        "selection": args.selection,
        "comparison": args.comparison,
        "platform": args.platform,
        "frequency": args.frequency,
        "search": args.search,
        "custom_value": args.custom_value,
        "rich_options": args.rich_options,
    }
    optional = {
        "expected_max_options": args.expected_max_options,
        "value_kind": args.value_kind,
        "effect": args.effect,
    }
    payload.update({key: value for key, value in optional.items() if value is not None})
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.input:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("input JSON must be an object")
        else:
            payload = payload_from_args(args)
        result = choose_ui(payload)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
