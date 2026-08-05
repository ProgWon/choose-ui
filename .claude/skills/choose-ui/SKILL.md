---
name: choose-ui
description: Choose and justify UI components from user intent, option cardinality, interaction timing, comparison needs, platform constraints, and accessibility requirements. Use when designing, implementing, or reviewing forms, filters, settings, navigation, menus, tabs, selection controls, dropdowns, radios, checkboxes, segmented controls, comboboxes, or bottom-sheet pickers; when a user asks which component or UX pattern to use; or when auditing an interface for mismatched controls and unnecessary interaction.
---

# Choose UI

Choose the smallest interaction that truthfully represents the user's task. Treat component choice as a product decision, not a styling preference.

## Workflow

1. Classify the intent before naming a component:
   - **input**: collect a value for later submission
   - **filter**: change the visible dataset
   - **view switch**: change how the same content is presented
   - **action**: execute a command
   - **navigation**: move to another destination
2. Capture the constraints that can change the decision:
   - option count now and expected growth
   - single or multiple selection
   - immediate or submit-time effect
   - whether users must compare options
   - whether search, custom values, or rich descriptions are needed
   - mobile, desktop, or cross-platform context
   - reversibility and cost of a wrong choice
3. Apply the hard rules below.
4. Read [references/selection-controls.md](references/selection-controls.md) for the detailed selection matrix. Read [references/decision-factors.md](references/decision-factors.md) when context creates a trade-off. Read [references/accessibility.md](references/accessibility.md) before implementing custom controls.
5. Return a decision record. If implementation was requested, implement the recommendation and all required states. If review was requested, report violations by user impact and propose the smallest correction.

## Hard Rules

- Do not render a selection control when there is no choice. For one fixed option, apply it automatically and show it as readable text when users need confirmation.
- Do not use select, dropdown, or combobox patterns for commands. Use a button or action menu.
- Do not use tabs or segmented controls for unrelated destinations. Use navigation.
- Prefer visible options when comparison is important and the list is short enough to scan.
- Use search only when recognition or retrieval is materially faster than scanning.
- Distinguish immediate settings from submitted answers. Use a switch for an immediate binary setting; use a checkbox for a submitted independent yes/no answer.
- Do not preserve an unsuitable control merely for visual consistency. Preserve the design system's tokens and primitives while choosing the correct interaction pattern.
- Account for loading, empty, error, disabled, selected, focus, and long-content states that can occur in the real data.
- Treat numeric thresholds as defaults, not laws. Override them when user research, platform convention, content complexity, localization, or an established product design system provides stronger evidence. State the override.

## Deterministic Recommendation

Run the bundled recommender when the request provides structured constraints or when comparing many flows:

```bash
python3 scripts/recommend.py \
  --intent input \
  --options 4 \
  --selection single \
  --comparison high \
  --platform mobile
```

Use `--format json` for automation. Treat the result as a baseline, then apply product context using the workflow above.

## Decision Record

Return this compact structure:

```text
Recommendation: <component or pattern>
Confidence: <high | medium | low>
Why: <intent and constraints that drove the choice>
Avoid: <closest rejected alternative and why>
Required states: <states the design or implementation must support>
Accessibility: <keyboard, labeling, focus, and announcement requirements>
Assumptions: <only consequential assumptions>
Evidence: <relevant source or product-system guidance>
```

Do not list multiple components without choosing one. When information is genuinely insufficient, select a provisional recommendation, lower confidence, and name the one missing fact that would change it.

## Audit Mode

For each questionable control:

1. Identify the user's actual task.
2. State the mismatch in behavioral terms.
3. Rate impact as `critical`, `major`, `moderate`, or `minor`.
4. Recommend the smallest viable replacement.
5. Preserve data, validation, analytics, and accessibility behavior during replacement.

Prioritize task failure, accidental action, inaccessible interaction, and hidden choices above aesthetic inconsistency.

## Evidence

Use [references/sources.md](references/sources.md) to cite original design-system guidance. Paraphrase and synthesize; do not imply that a source endorses every threshold in this skill.
