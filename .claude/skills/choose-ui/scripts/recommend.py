#!/usr/bin/env python3
"""Return a deterministic baseline UI recommendation from product constraints."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).resolve().parent.parent / "references" / "selection-rules.json"


@dataclass(frozen=True)
class Decision:
    recommendation: str
    confidence: str
    why: list[str]
    avoid: list[str]
    required_states: list[str]
    accessibility: list[str]
    assumptions: list[str]


def load_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    context = {
        "intent": payload.get("intent", "input"),
        "options": payload.get("options"),
        "selection": payload.get("selection", "single"),
        "comparison": payload.get("comparison", "low"),
        "platform": payload.get("platform", "any"),
        "effect": payload.get("effect", "submit"),
        "search": bool(payload.get("search", False)),
        "custom_value": bool(payload.get("custom_value", False)),
        "dynamic": bool(payload.get("dynamic", False)),
        "rich_options": bool(payload.get("rich_options", False)),
    }

    allowed = {
        "intent": {"input", "filter", "view-switch", "action", "navigation", "setting"},
        "selection": {"single", "multiple"},
        "comparison": {"low", "high"},
        "platform": {"any", "mobile", "desktop"},
        "effect": {"submit", "immediate"},
    }
    for field, values in allowed.items():
        if context[field] not in values:
            raise ValueError(f"{field} must be one of: {', '.join(sorted(values))}")

    if context["options"] is None:
        raise ValueError("options is required")
    if not isinstance(context["options"], int) or isinstance(context["options"], bool):
        raise ValueError("options must be an integer")
    if context["options"] < 0:
        raise ValueError("options cannot be negative")
    return context


def choose_ui(payload: dict[str, Any], rules: dict[str, Any] | None = None) -> Decision:
    context = normalize(payload)
    rules = rules or load_rules()
    thresholds = rules["thresholds"]
    count = context["options"]
    intent = context["intent"]
    selection = context["selection"]
    platform = context["platform"]
    compare = context["comparison"] == "high"
    assumptions: list[str] = []

    if context["dynamic"]:
        assumptions.append("The recommendation targets the credible upper-bound option count, not a loading snapshot.")

    if count == 0:
        if intent == "action":
            return decision(
                "no action trigger",
                "high",
                ["No command is available, so an action trigger would open an empty surface."],
                ["Do not show an empty menu or a disabled overflow button without a user-relevant explanation."],
                ["permission-loading", "hidden", "permission-error"],
                ["Remove unavailable actions from the accessibility tree; explain missing capabilities elsewhere only when users need that information."],
                assumptions,
            )
        if intent == "navigation":
            return decision(
                "no navigation control",
                "high",
                ["No destination is available, so there is no navigation choice to expose."],
                ["Do not render empty tabs or an empty navigation menu."],
                ["loading", "hidden", "error"],
                ["Do not leave an unlabeled or disabled navigation trigger in the accessibility tree."],
                assumptions,
            )
        return decision(
            "empty state",
            "high",
            ["No option is available, so the user cannot make a selection."],
            ["Do not render an empty dropdown or disabled picker without explanation."],
            ["loading", "empty", "error", "recovery"],
            ["Announce the empty-state message and provide an accessible recovery action when one exists."],
            assumptions,
        )

    if intent == "action":
        if count == 1:
            return decision(
                "button",
                "high",
                ["The user is executing one command, not selecting a value."],
                ["Avoid a dropdown because it adds a disclosure step without adding choice."],
                ["default", "focus", "pressed", "disabled", "loading", "error"],
                ["Use a native button with an action-oriented accessible name."],
                assumptions,
            )
        return decision(
            "action menu",
            "high",
            [f"The user is choosing among {count} commands."],
            ["Avoid select and combobox controls because they communicate data entry."],
            ["closed", "open", "focus", "disabled", "in-progress", "success", "error"],
            ["Support Escape, arrow keys, focus return, and clear menu-item names."],
            assumptions,
        )

    if intent == "navigation":
        if count == 1:
            return decision(
                "direct link",
                "high",
                ["There is one destination, so no navigation chooser is needed."],
                ["Avoid a one-item menu or tab strip."],
                ["default", "focus", "visited"],
                ["Use a descriptive link name that identifies the destination."],
                assumptions,
            )
        if count <= thresholds["tabs_max"]:
            return decision(
                "tabs",
                "medium",
                [f"There are {count} peer destinations that can remain visible."],
                ["Avoid a segmented control unless the same content is being manipulated in place."],
                ["default", "focus", "selected", "disabled", "overflow"],
                ["Use tablist, tab, and tabpanel semantics with predictable arrow-key behavior."],
                assumptions + ["The destinations are peer sections, not unrelated pages."],
            )
        return decision(
            "navigation list",
            "medium",
            [f"There are {count} destinations, which exceeds a compact tab set."],
            ["Avoid squeezing destinations into tabs or a form select by default."],
            ["default", "focus", "current", "collapsed", "expanded"],
            ["Expose the current destination and preserve normal link behavior."],
            assumptions + ["The destinations can be organized into a visible or disclosed navigation structure."],
        )

    if count == 1:
        if intent == "setting" and context["effect"] == "immediate":
            return decision(
                "switch",
                "high",
                ["This is one immediate on/off setting whose state changes directly."],
                ["Avoid a radio group or select for a Boolean setting."],
                ["on", "off", "focus", "disabled", "loading", "error"],
                ["Expose the switch role, label, and current checked state."],
                assumptions,
            )
        if selection == "multiple":
            return decision(
                "checkbox",
                "medium",
                ["A single independent option is a Boolean form answer."],
                ["Avoid multi-select controls for one opt-in."],
                ["checked", "unchecked", "focus", "disabled", "error"],
                ["Associate the label with the checkbox and keep the full label clickable."],
                assumptions + ["The option may be accepted or declined; it is not forced."],
            )
        return decision(
            "static value",
            "high",
            ["One fixed option creates no meaningful user choice."],
            ["Avoid a disabled or one-item dropdown because it falsely implies choice."],
            ["loading", "resolved", "unavailable", "long-content"],
            ["Present the value as readable text and include it in submitted data programmatically when needed."],
            assumptions,
        )

    if selection == "multiple":
        if intent == "filter" and count <= thresholds["visible_multi_max"] and not context["rich_options"]:
            return decision(
                "selection chips",
                "high",
                [f"{count} short filters can remain visible for frequent toggling."],
                ["Avoid hiding a small active filter set in a closed multi-select."],
                ["default", "focus", "selected", "disabled", "overflow"],
                ["Expose each chip's pressed or checked state and do not rely on color alone."],
                assumptions,
            )
        if context["search"] or count >= thresholds["combobox_min"]:
            return decision(
                "multi-select combobox",
                "high" if context["search"] else "medium",
                [f"{count} options make retrieval and visible selected tokens useful."],
                ["Avoid a native multi-select listbox and an unsearchable long checklist in a small surface."],
                ["closed", "open", "query", "results", "selected", "no-results", "error"],
                ["Follow an established combobox pattern and announce results and token removal."],
                assumptions,
            )
        if platform == "mobile" and count > thresholds["visible_multi_max"]:
            return decision(
                "button opening checkbox sheet",
                "high",
                [f"{count} options need a touch-friendly scanning surface."],
                ["Avoid a dense inline checklist or desktop-sized popup."],
                ["closed", "open", "selected", "apply", "cancel", "error"],
                ["Trap focus only when modal, restore it on close, and expose the selected count."],
                assumptions,
            )
        return decision(
            "checkbox group",
            "high",
            [f"{count} options can remain visible for direct comparison and multiple selection."],
            ["Avoid a multi-select when the full set fits comfortably."],
            ["checked", "unchecked", "focus", "disabled", "error", "long-content"],
            ["Use a group label and make each text label part of its checkbox target."],
            assumptions,
        )

    if context["custom_value"] or context["search"] or count >= thresholds["combobox_min"]:
        return decision(
            "combobox",
            "high" if context["custom_value"] or context["search"] else "medium",
            [
                "Users need text retrieval or a value outside the predefined set."
                if context["custom_value"]
                else f"{count} options make search or type-ahead materially useful."
            ],
            ["Avoid an unsearchable long select and do not add search to a short list."],
            ["closed", "open", "query", "results", "selected", "no-results", "error"],
            ["Follow an established combobox keyboard pattern and announce result changes."],
            assumptions,
        )

    if context["rich_options"] or compare:
        if count <= thresholds["radio_max"]:
            return decision(
                "radio group" if not context["rich_options"] else "radio cards",
                "high",
                [f"{count} options should remain visible because comparison is important."],
                ["Avoid a closed select that forces users to remember hidden alternatives."],
                ["default", "focus", "selected", "disabled", "error", "long-content"],
                ["Use a group label and include each full card or text label in the activation target."],
                assumptions,
            )
        if platform == "mobile":
            return decision(
                "input button opening a comparison sheet",
                "medium",
                [f"{count} detailed options need more room than an inline control provides."],
                ["Avoid hiding rich descriptions in a simple select."],
                ["closed", "open", "selected", "apply", "cancel", "error", "long-content"],
                ["Use a labeled trigger, accessible dialog semantics, and predictable focus restoration."],
                assumptions,
            )
        return decision(
            "comparison list with radio selection",
            "medium",
            [f"{count} detailed options require visible comparison despite the longer list."],
            ["Avoid a closed select that removes descriptive context."],
            ["default", "focus", "selected", "disabled", "error", "long-content"],
            ["Use a group label and keep option details associated with each radio."],
            assumptions,
        )

    if intent == "view-switch" and count <= thresholds["segmented_max"]:
        return decision(
            "segmented control",
            "high",
            [f"{count} choices immediately change the presentation of the same content."],
            ["Avoid tabs when the user is manipulating one view rather than navigating sections."],
            ["default", "focus", "selected", "disabled", "loading", "error", "overflow", "long-content"],
            ["Expose selection programmatically and support keyboard movement consistently."],
            assumptions,
        )

    if count <= thresholds["radio_max"]:
        return decision(
            "radio group",
            "high",
            [f"{count} single-choice form options fit as a visible group."],
            ["Avoid a select because it hides a short list behind an extra interaction."],
            ["default", "focus", "selected", "disabled", "error", "long-content"],
            ["Use a fieldset and legend on the web and keep labels clickable."],
            assumptions,
        )

    if platform == "mobile":
        return decision(
            "input button opening a selection sheet",
            "high",
            [f"{count} options benefit from a touch-friendly list surface."],
            ["Avoid a small custom popup optimized for pointer input."],
            ["closed", "open", "selected", "apply", "cancel", "error"],
            ["Use an accessible trigger and dialog or sheet behavior with focus restoration."],
            assumptions,
        )

    return decision(
        "select",
        "medium",
        [f"{count} simple options do not need comparison or search."],
        ["Avoid an expanded radio list unless user research shows comparison is important."],
        ["default", "focus", "selected", "disabled", "error", "long-content"],
        ["Prefer the native select when its behavior is sufficient and provide a persistent label."],
        assumptions,
    )


def decision(
    recommendation: str,
    confidence: str,
    why: list[str],
    avoid: list[str],
    required_states: list[str],
    accessibility: list[str],
    assumptions: list[str],
) -> Decision:
    return Decision(
        recommendation=recommendation,
        confidence=confidence,
        why=why,
        avoid=avoid,
        required_states=required_states,
        accessibility=accessibility,
        assumptions=assumptions,
    )


def render_text(result: Decision) -> str:
    assumptions = "; ".join(result.assumptions) if result.assumptions else "None"
    return "\n".join(
        [
            f"Recommendation: {result.recommendation}",
            f"Confidence: {result.confidence}",
            f"Why: {' '.join(result.why)}",
            f"Avoid: {' '.join(result.avoid)}",
            f"Required states: {', '.join(result.required_states)}",
            f"Accessibility: {' '.join(result.accessibility)}",
            f"Assumptions: {assumptions}",
        ]
    )


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", type=Path, help="Read constraints from a JSON object.")
    cli.add_argument("--intent", choices=["input", "filter", "view-switch", "action", "navigation", "setting"])
    cli.add_argument("--options", type=int)
    cli.add_argument("--selection", choices=["single", "multiple"], default="single")
    cli.add_argument("--comparison", choices=["low", "high"], default="low")
    cli.add_argument("--platform", choices=["any", "mobile", "desktop"], default="any")
    cli.add_argument("--effect", choices=["submit", "immediate"], default="submit")
    cli.add_argument("--search", action="store_true")
    cli.add_argument("--custom-value", action="store_true")
    cli.add_argument("--dynamic", action="store_true")
    cli.add_argument("--rich-options", action="store_true")
    cli.add_argument("--format", choices=["text", "json"], default="text")
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.input:
        with args.input.open(encoding="utf-8") as source:
            payload = json.load(source)
        if not isinstance(payload, dict):
            print("error: input JSON must be an object", file=sys.stderr)
            return 2
    else:
        payload = {
            "intent": args.intent or "input",
            "options": args.options,
            "selection": args.selection,
            "comparison": args.comparison,
            "platform": args.platform,
            "effect": args.effect,
            "search": args.search,
            "custom_value": args.custom_value,
            "dynamic": args.dynamic,
            "rich_options": args.rich_options,
        }

    try:
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
