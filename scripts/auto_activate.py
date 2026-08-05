#!/usr/bin/env python3
"""Nudge Claude to load Choose UI for broad product-building prompts."""

from __future__ import annotations

import json
import sys
from typing import Any


BUILD_TERMS = (
    "build",
    "create",
    "develop",
    "design",
    "implement",
    "make",
    "prototype",
    "개발",
    "만들",
    "구현",
    "설계",
    "제작",
    "프로토타입",
)

PRODUCT_TERMS = (
    "admin",
    "app",
    "application",
    "dashboard",
    "e-commerce",
    "ecommerce",
    "frontend",
    "form",
    "interface",
    "page",
    "portal",
    "product",
    "saas",
    "service",
    "screen",
    "ui",
    "ux",
    "website",
    "web app",
    "관리자",
    "대시보드",
    "서비스",
    "인터페이스",
    "쇼핑몰",
    "어드민",
    "어플",
    "앱",
    "웹사이트",
    "웹앱",
    "페이지",
    "화면",
    "폼",
    "제품",
    "포털",
    "프론트엔드",
)

BACKEND_TERMS = (
    "api only",
    "backend only",
    "database only",
    "server only",
    "api-only",
    "backend-only",
    "database-only",
    "server-only",
    "server-side only",
    "api만",
    "db만",
    "데이터베이스만",
    "백엔드만",
    "서버만",
    "서버 사이드만",
)


def should_nudge(prompt: str) -> bool:
    normalized = " ".join(prompt.casefold().split())
    if any(term in normalized for term in BACKEND_TERMS):
        return False
    return any(term in normalized for term in BUILD_TERMS) and any(
        term in normalized for term in PRODUCT_TERMS
    )


def hook_output(prompt: str) -> dict[str, Any] | None:
    if not should_nudge(prompt):
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                "Choose UI auto-activation: this appears to be an end-to-end product or "
                "frontend build. Before choosing or implementing interactive UI patterns, "
                "invoke the available choose-ui skill and apply its decisions throughout the "
                "task. Do not invoke it for backend-only work or visual-only styling."
            ),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        return 0
    output = hook_output(prompt)
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
