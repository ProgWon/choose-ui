#!/usr/bin/env python3
"""Run Choose UI activation and behavior cases in fresh Claude Code sessions."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = Path(__file__).with_name("skill-cases.json")
SKILL_NAME = "choose-ui"
FIELD_ALIASES = {
    "recommendation": ["recommendation", "추천"],
    "confidence": ["confidence", "확신도", "신뢰도"],
    "why": ["why", "이유"],
    "avoid": ["avoid", "피할", "지양"],
    "required_states": ["required states", "필수 상태", "필요 상태"],
    "accessibility": ["accessibility", "접근성"],
    "assumptions": ["assumptions", "가정"],
    "evidence": ["evidence", "근거"],
}


@dataclass
class Transcript:
    response: str
    invoked_skills: list[str]
    error: str | None


@dataclass
class CaseResult:
    suite: str
    name: str
    passed: bool
    triggered: bool
    expected_trigger: bool
    checks: dict[str, bool]
    response: str
    semantic_checks: list[str]
    error: str | None = None


def load_suite(path: Path = CASES_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 2:
        raise ValueError("skill-cases.json version must be 2")
    return data


def parse_stream(stream: str) -> Transcript:
    skills: list[str] = []
    response = ""
    error: str | None = None
    for raw_line in stream.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for content in event.get("message", {}).get("content", []):
                if content.get("type") != "tool_use" or content.get("name") != "Skill":
                    continue
                tool_input = content.get("input", {})
                skill = tool_input.get("skill") or tool_input.get("name")
                if isinstance(skill, str):
                    skills.append(skill)
        if event.get("type") == "result":
            if isinstance(event.get("result"), str):
                response = event["result"]
            if event.get("is_error"):
                error = response or event.get("subtype") or "Claude Code evaluation failed"
    return Transcript(response=response, invoked_skills=skills, error=error)


def has_field(response: str, field: str) -> bool:
    lowered = response.casefold()
    return any(f"{alias.casefold()}:" in lowered for alias in FIELD_ALIASES[field])


def field_line(response: str, field: str) -> str:
    aliases = [alias.casefold() for alias in FIELD_ALIASES[field]]
    for line in response.splitlines():
        lowered = line.casefold()
        if any(f"{alias}:" in lowered for alias in aliases):
            return line
    return ""


def contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def score_trigger(case: dict[str, Any], transcript: Transcript) -> CaseResult:
    triggered = any(skill == SKILL_NAME or skill.endswith(f":{SKILL_NAME}") for skill in transcript.invoked_skills)
    expected = bool(case["should_trigger"])
    passed = transcript.error is None and triggered == expected
    return CaseResult(
        suite="trigger",
        name=case["name"],
        passed=passed,
        triggered=triggered,
        expected_trigger=expected,
        checks={"activation": triggered == expected},
        response=transcript.response,
        semantic_checks=[],
        error=transcript.error,
    )


def score_behavior(case: dict[str, Any], transcript: Transcript) -> CaseResult:
    triggered = any(skill == SKILL_NAME or skill.endswith(f":{SKILL_NAME}") for skill in transcript.invoked_skills)
    checks: dict[str, bool] = {"activation": triggered}
    response = transcript.response

    recommendation_terms = case.get("recommendation_terms", [])
    if recommendation_terms:
        recommendation = field_line(response, "recommendation") or response
        checks["recommendation"] = contains_any(recommendation, recommendation_terms)

    confidence_terms = case.get("confidence_terms", [])
    if confidence_terms:
        confidence = field_line(response, "confidence") or response
        checks["confidence"] = contains_any(confidence, confidence_terms)

    if case["expected_mode"] == "quick":
        checks["quick_fields"] = has_field(response, "recommendation") and has_field(response, "why")
        checks["quick_is_compact"] = not any(
            has_field(response, field)
            for field in ["confidence", "avoid", "required_states", "accessibility", "assumptions", "evidence"]
        )
    else:
        for field in FIELD_ALIASES:
            checks[f"full_{field}"] = has_field(response, field)

    passed = transcript.error is None and all(checks.values())
    return CaseResult(
        suite="behavior",
        name=case["name"],
        passed=passed,
        triggered=triggered,
        expected_trigger=True,
        checks=checks,
        response=response,
        semantic_checks=case.get("semantic_checks", []),
        error=transcript.error,
    )


def invoke_claude(
    executable: str,
    prompt: str,
    model: str,
    max_budget_usd: float,
    timeout: int,
) -> Transcript:
    command = [
        executable,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--setting-sources",
        "project",
        "--tools=Skill",
        "--model",
        model,
        "--max-budget-usd",
        str(max_budget_usd),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return Transcript(response="", invoked_skills=[], error=f"timed out after {timeout}s")
    transcript = parse_stream(completed.stdout)
    if completed.returncode and not transcript.error:
        transcript.error = completed.stderr.strip() or f"Claude Code exited {completed.returncode}"
    return transcript


def run(args: argparse.Namespace) -> list[CaseResult]:
    suite = load_suite(args.cases)
    executable = shutil.which(args.claude)
    if not executable:
        raise RuntimeError(f"Claude Code executable not found: {args.claude}")

    selected: list[tuple[str, dict[str, Any]]] = []
    if args.suite in {"trigger", "all"}:
        selected.extend(("trigger", case) for case in suite["trigger_cases"])
    if args.suite in {"behavior", "all"}:
        selected.extend(("behavior", case) for case in suite["behavior_cases"])

    results: list[CaseResult] = []
    for suite_name, case in selected:
        for repeat in range(args.repeats):
            transcript = invoke_claude(
                executable,
                case["prompt"],
                args.model,
                args.max_budget_usd,
                args.timeout,
            )
            scored = score_trigger(case, transcript) if suite_name == "trigger" else score_behavior(case, transcript)
            if args.repeats > 1:
                scored.name = f"{scored.name} [run {repeat + 1}]"
            results.append(scored)
            if scored.error and not args.keep_going:
                return results
    return results


def render_human(results: list[CaseResult]) -> str:
    lines: list[str] = []
    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        lines.append(
            f"[{mark}] {result.suite}: {result.name} "
            f"(triggered={result.triggered}, expected={result.expected_trigger})"
        )
        for check, passed in result.checks.items():
            lines.append(f"  {'✓' if passed else '✗'} {check}")
        if result.error:
            lines.append(f"  error: {result.error}")
        for semantic in result.semantic_checks:
            lines.append(f"  manual/LLM judge: {semantic}")

    trigger = [result for result in results if result.suite == "trigger"]
    positives = [result for result in trigger if result.expected_trigger]
    negatives = [result for result in trigger if not result.expected_trigger]
    if positives:
        rate = sum(result.triggered for result in positives) / len(positives)
        lines.append(f"positive activation rate: {rate:.0%} ({sum(result.triggered for result in positives)}/{len(positives)})")
    if negatives:
        false_rate = sum(result.triggered for result in negatives) / len(negatives)
        lines.append(f"negative false-positive rate: {false_rate:.0%} ({sum(result.triggered for result in negatives)}/{len(negatives)})")
    lines.append(f"automatic pass rate: {sum(result.passed for result in results)}/{len(results)}")
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--suite", choices=["trigger", "behavior", "all"], default="trigger")
    cli.add_argument("--cases", type=Path, default=CASES_PATH)
    cli.add_argument("--claude", default="claude")
    cli.add_argument("--model", default="sonnet")
    cli.add_argument("--repeats", type=int, default=1)
    cli.add_argument("--max-budget-usd", type=float, default=0.10, help="Per fresh session.")
    cli.add_argument("--timeout", type=int, default=120, help="Seconds per fresh session.")
    cli.add_argument("--keep-going", action="store_true", help="Continue after a session error.")
    cli.add_argument("--json", action="store_true")
    cli.add_argument("--output", type=Path, help="Also write the complete result as JSON.")
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.repeats < 1:
        print("error: repeats must be at least 1", file=sys.stderr)
        return 2
    try:
        results = run(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    payload = {
        "skill": SKILL_NAME,
        "results": [asdict(result) for result in results],
        "automatic_passes": sum(result.passed for result in results),
        "total": len(results),
    }
    if args.output:
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_human(results))
    if any(result.error for result in results):
        return 2
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
