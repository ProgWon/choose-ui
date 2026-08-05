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
2. Update the canonical `.claude/skills/choose-ui/references/selection-rules.json` rule or threshold.
3. Regenerate the human-readable matrix; do not edit it by hand.
4. Run the rule check and complete test suite.

```bash
python3 .claude/skills/choose-ui/scripts/rules_tool.py --write
python3 .claude/skills/choose-ui/scripts/rules_tool.py --check
python3 -m unittest discover -s tests -v
```

When changing skill activation or output instructions, run the authenticated live trigger suite locally:

```bash
python3 evals/run_skill_evals.py --suite trigger
```

Do not add live model calls to CI. Record model/version, repeat count, and raw JSON output when publishing activation-rate claims.

Keep recommendations deterministic for the same structured input. If the correct choice depends on missing context, return medium or low confidence and state the assumption that matters.

## Extend the skill

Keep `SKILL.md` concise and route detailed guidance to one-level-deep reference files. Add scripts only for deterministic or repeatedly executed work. Do not add framework boilerplate until a real evaluation case requires it.

Design-system adapters are especially welcome. Good first adapters include Material 3, shadcn/ui, Radix, Ant Design, and Carbon. Start with the `Add a design-system adapter` issue template, map generic interaction families to documented component names, and add at least one evaluation case that proves the mapping changes a recommendation or its wording.

## Pull request checklist

- The change solves a concrete user problem.
- At least one evaluation case covers the change.
- Existing evaluations still pass or their changed expectation is justified.
- The generated matrix matches the canonical rulebook.
- Accessibility behavior is specified for a new custom interaction.
- Sources are primary and linked.
- No source documentation is copied wholesale.
- `SKILL.md` remains under 500 lines.
