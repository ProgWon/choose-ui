# Contributing to Choose UI

Choose UI improves through falsifiable product cases, not larger lists of opinions.

## Propose a rule or correction

Include:

1. The user's intent.
2. The realistic option range and platform.
3. Whether the effect is immediate or submitted.
4. Whether comparison, search, custom values, or rich content matters.
5. The current and expected recommendation.
6. The user harm caused by the wrong pattern.
7. A primary design-system, accessibility, research, or platform source when available.

Avoid copying source text. Paraphrase the principle and link to the original.

## Change the decision engine

1. Add a failing scenario to `evals/cases.json`.
2. Update `.claude/skills/choose-ui/scripts/recommend.py` or its thresholds.
3. Update the relevant reference file when the human-readable guidance changes.
4. Run the complete test suite.

```bash
python3 -m unittest discover -s tests -v
```

Keep recommendations deterministic for the same structured input. If the correct choice depends on missing context, return medium or low confidence and state the assumption that matters.

## Extend the skill

Keep `SKILL.md` concise and route detailed guidance to one-level-deep reference files. Add scripts only for deterministic or repeatedly executed work. Do not add framework boilerplate until a real evaluation case requires it.

## Pull request checklist

- The change solves a concrete user problem.
- At least one evaluation case covers the change.
- Existing evaluations still pass or their changed expectation is justified.
- Accessibility behavior is specified for a new custom interaction.
- Sources are primary and linked.
- No source documentation is copied wholesale.
- `SKILL.md` remains under 500 lines.
