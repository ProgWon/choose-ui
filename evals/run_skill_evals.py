#!/usr/bin/env python3
"""Run Choose UI activation and behavior cases in fresh Claude Code sessions."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = Path(__file__).with_name("skill-cases.json")
SKILL_NAME = "choose-ui"
TRIGGER_TOOLS = ["Skill", "Read", "Grep", "Glob"]
FIELD_ALIASES = {
    "recommendation": ["recommendation", "추천", "권장"],
    "confidence": ["confidence", "확신도", "신뢰도"],
    "why": ["why", "이유"],
    "avoid": ["avoid", "피할", "피해야", "지양"],
    "required_states": ["required states", "필수 상태", "필요 상태", "필요한 상태"],
    "accessibility": ["accessibility", "접근성"],
    "assumptions": ["assumptions", "가정", "전제"],
    "evidence": ["evidence", "근거", "출처"],
}
REQUIRED_CLAUDE_FLAGS = [
    "--output-format",
    "--no-session-persistence",
    "--permission-mode",
    "--setting-sources",
    "--tools",
    "--model",
    "--max-budget-usd",
]


@dataclass
class Transcript:
    response: str
    invoked_skills: list[str]
    error: str | None
    cost_usd: float = 0.0


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
    cost_usd: float = 0.0


def load_suite(path: Path = CASES_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 2:
        raise ValueError("skill-cases.json version must be 2")
    return data


def parse_stream(stream: str) -> Transcript:
    skills: list[str] = []
    response = ""
    error: str | None = None
    cost_usd = 0.0
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
            if isinstance(event.get("total_cost_usd"), (int, float)):
                cost_usd = float(event["total_cost_usd"])
    return Transcript(response=response, invoked_skills=skills, error=error, cost_usd=cost_usd)


def line_label(line: str) -> str:
    if ":" not in line:
        return ""
    return line.split(":", 1)[0].casefold().strip(" \t#*-_`")


def has_field(response: str, field: str) -> bool:
    aliases = [alias.casefold() for alias in FIELD_ALIASES[field]]
    return any(any(alias in line_label(line) for alias in aliases) for line in response.splitlines())


def field_line(response: str, field: str) -> str:
    aliases = [alias.casefold() for alias in FIELD_ALIASES[field]]
    for line in response.splitlines():
        if any(alias in line_label(line) for alias in aliases):
            return line
    return ""


def field_block(response: str, field: str) -> str:
    aliases = [alias.casefold() for alias in FIELD_ALIASES[field]]
    collected: list[str] = []
    collecting = False
    all_aliases = [alias.casefold() for values in FIELD_ALIASES.values() for alias in values]
    for line in response.splitlines():
        label = line_label(line)
        if not collecting:
            if any(alias in label for alias in aliases):
                collecting = True
                collected.append(line)
            continue
        if label and any(alias in label for alias in all_aliases):
            break
        collected.append(line)
    return "\n".join(collected)


def contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def contains_all_groups(text: str, groups: list[list[str]]) -> bool:
    return all(contains_any(text, group) for group in groups)


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
        cost_usd=transcript.cost_usd,
    )


def score_behavior(case: dict[str, Any], transcript: Transcript) -> CaseResult:
    triggered = any(skill == SKILL_NAME or skill.endswith(f":{SKILL_NAME}") for skill in transcript.invoked_skills)
    checks: dict[str, bool] = {"activation": triggered}
    response = transcript.response

    recommendation_terms = case.get("recommendation_terms", [])
    recommendation_groups = case.get("recommendation_term_groups", [])
    if recommendation_terms or recommendation_groups:
        recommendation = field_block(response, "recommendation") or response
        checks["recommendation"] = (
            contains_any(recommendation, recommendation_terms) if recommendation_terms else False
        ) or (
            contains_all_groups(recommendation, recommendation_groups)
            if recommendation_groups
            else False
        )

    confidence_terms = case.get("confidence_terms", [])
    if confidence_terms:
        confidence = field_block(response, "confidence") or response
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
        cost_usd=transcript.cost_usd,
    )


def invoke_claude(
    command_prefix: list[str],
    prompt: str,
    model: str,
    max_budget_usd: float,
    timeout: int,
    tools: list[str],
    settings: str | None,
) -> Transcript:
    command = [
        *command_prefix,
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
    ]
    if settings:
        command.extend(["--settings", settings])
    command.extend(
        [
            f"--tools={','.join(tools)}",
            "--model",
            model,
            "--max-budget-usd",
            str(max_budget_usd),
        ]
    )
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


def validate_claude_cli(command_prefix: list[str]) -> str:
    help_result = subprocess.run(
        [*command_prefix, "--help"], capture_output=True, text=True, timeout=30, check=False
    )
    if help_result.returncode:
        raise RuntimeError(help_result.stderr.strip() or "could not read Claude Code help")
    missing = [flag for flag in REQUIRED_CLAUDE_FLAGS if flag not in help_result.stdout]
    if missing:
        raise RuntimeError(f"Claude Code does not support required flags: {', '.join(missing)}")
    version_result = subprocess.run(
        [*command_prefix, "--version"], capture_output=True, text=True, timeout=30, check=False
    )
    return version_result.stdout.strip() or "unknown"


def isolated_plugin_settings() -> str:
    settings_path = Path.home() / ".claude" / "settings.json"
    try:
        user_settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        user_settings = {}
    plugins = user_settings.get("enabledPlugins", {})
    disabled = {name: False for name in plugins if isinstance(name, str)}
    return json.dumps({"enabledPlugins": disabled}, separators=(",", ":"))


def run(args: argparse.Namespace) -> tuple[list[CaseResult], str]:
    suite = load_suite(args.cases)
    direct_path = Path(args.claude).expanduser()
    command_prefix = [str(direct_path)] if direct_path.is_file() else shlex.split(args.claude)
    if not command_prefix:
        raise RuntimeError("Claude Code command cannot be empty")
    executable = shutil.which(command_prefix[0])
    if not executable:
        raise RuntimeError(f"Claude Code executable not found: {command_prefix[0]}")
    command_prefix[0] = executable
    claude_version = validate_claude_cli(command_prefix)

    selected: list[tuple[str, dict[str, Any]]] = []
    if args.suite in {"trigger", "all"}:
        selected.extend(("trigger", case) for case in suite["trigger_cases"])
    if args.suite in {"behavior", "all"}:
        selected.extend(("behavior", case) for case in suite["behavior_cases"])
    if args.case:
        needles = [needle.casefold() for needle in args.case]
        selected = [
            item for item in selected if any(needle in item[1]["name"].casefold() for needle in needles)
        ]
        if not selected:
            raise RuntimeError(f"no evaluation case matched: {', '.join(args.case)}")

    tasks: list[tuple[str, dict[str, Any], int]] = []
    for suite_name, case in selected:
        for repeat in range(args.repeats):
            tasks.append((suite_name, case, repeat))

    settings = None if args.keep_user_plugins else isolated_plugin_settings()

    def evaluate(indexed_task: tuple[int, tuple[str, dict[str, Any], int]]) -> tuple[int, CaseResult]:
        index, task = indexed_task
        suite_name, case, repeat = task
        transcript = invoke_claude(
            command_prefix,
            case["prompt"],
            args.model,
            args.max_budget_usd,
            args.timeout,
            case.get("tools", TRIGGER_TOOLS if suite_name == "trigger" else ["Skill"]),
            settings,
        )
        scored = score_trigger(case, transcript) if suite_name == "trigger" else score_behavior(case, transcript)
        if args.repeats > 1:
            scored.name = f"{scored.name} [run {repeat + 1}]"
        return index, scored

    results: list[CaseResult] = []
    indexed_tasks = list(enumerate(tasks))
    if args.jobs == 1:
        for indexed_task in indexed_tasks:
            _, scored = evaluate(indexed_task)
            results.append(scored)
            if args.progress:
                print(render_case(scored), flush=True)
            if scored.error and not args.keep_going:
                break
    else:
        completed: dict[int, CaseResult] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = [executor.submit(evaluate, task) for task in indexed_tasks]
            for future in concurrent.futures.as_completed(futures):
                index, scored = future.result()
                completed[index] = scored
                if args.progress:
                    print(render_case(scored), flush=True)
        results = [completed[index] for index in sorted(completed)]
    return results, claude_version


def render_case(result: CaseResult) -> str:
    mark = "PASS" if result.passed else "FAIL"
    lines = [
        f"[{mark}] {result.suite}: {result.name} "
        f"(triggered={result.triggered}, expected={result.expected_trigger})"
    ]
    for check, passed in result.checks.items():
        lines.append(f"  {'✓' if passed else '✗'} {check}")
    if result.error:
        lines.append(f"  error: {result.error}")
    lines.append(f"  cost: ${result.cost_usd:.4f}")
    for semantic in result.semantic_checks:
        lines.append(f"  manual/LLM judge: {semantic}")
    return "\n".join(lines)


def render_human(results: list[CaseResult]) -> str:
    lines = [render_case(result) for result in results]

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
    lines.append(f"total model cost: ${sum(result.cost_usd for result in results):.4f}")
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--suite", choices=["trigger", "behavior", "all"], default="trigger")
    cli.add_argument("--case", action="append", help="Run case names containing this text; repeatable.")
    cli.add_argument("--cases", type=Path, default=CASES_PATH)
    cli.add_argument(
        "--claude",
        default="claude",
        help='Claude Code command prefix, for example "npx -y @anthropic-ai/claude-code@2.1.222".',
    )
    cli.add_argument("--model", default="sonnet")
    cli.add_argument("--repeats", type=int, default=1)
    cli.add_argument("--max-budget-usd", type=float, default=0.10, help="Per fresh session.")
    cli.add_argument("--timeout", type=int, default=120, help="Seconds per fresh session.")
    cli.add_argument("--jobs", type=int, default=1, help="Concurrent fresh sessions.")
    cli.add_argument("--progress", action="store_true", help="Print each case as it completes.")
    cli.add_argument("--keep-going", action="store_true", help="Continue after a session error.")
    cli.add_argument("--keep-user-plugins", action="store_true", help="Do not disable plugins enabled in user settings.")
    cli.add_argument("--json", action="store_true")
    cli.add_argument("--output", type=Path, help="Also write the complete result as JSON.")
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.repeats < 1:
        print("error: repeats must be at least 1", file=sys.stderr)
        return 2
    if args.jobs < 1:
        print("error: jobs must be at least 1", file=sys.stderr)
        return 2
    try:
        results, claude_version = run(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    payload = {
        "skill": SKILL_NAME,
        "claude_version": claude_version,
        "results": [asdict(result) for result in results],
        "automatic_passes": sum(result.passed for result in results),
        "total": len(results),
        "total_cost_usd": sum(result.cost_usd for result in results),
    }
    if args.output:
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_human(results))
    if any(result.error for result in results):
        return 2
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
