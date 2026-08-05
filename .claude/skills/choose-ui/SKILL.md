---
name: choose-ui
description: Select and justify UI interaction patterns from user intent, real constraints, accessibility, and product context. Use proactively while planning, designing, implementing, or reviewing an end-to-end service, app, website, dashboard, admin, ecommerce, SaaS, or frontend—even when the user only asks to build the service and does not name components—whenever the work will introduce or choose interactive UI for input, selection, filtering, view switching, actions, navigation, or settings. Also use for explicit control comparisons and behavioral UX audits where replacement is allowed. Do not use for backend-only, API-only, or database-only work; visual-only styling or token changes; or implementation where the interaction pattern is already fixed and review is explicitly out of scope.
---

# Choose UI

Choose the smallest interaction that truthfully represents the user's task. Treat component choice as a product decision, not a styling preference.

For a broad end-to-end product build, apply this workflow during planning before committing to interactive components. Do not wait for the user to name a dropdown, tab, filter, or other control.

## Workflow

1. Classify intent before naming a component:
   - **input**: collect a value for later submission
   - **filter**: change the visible dataset
   - **view switch**: change how the same content is presented
   - **action**: execute a command
   - **navigation**: move to another destination
   - **setting**: persist a product or account preference
2. Capture decision-changing constraints:
   - option count now and the credible maximum
   - single or multiple selection; Boolean or selection value
   - immediate or submit-time effect
   - comparison need, frequency, search, custom values, and rich descriptions
   - mobile, desktop, or cross-platform context
   - reversibility and cost of a wrong choice
3. Inspect the project's existing design-system inventory, component imports, and local usage. Read [references/design-system-adapter.md](references/design-system-adapter.md). If a suitable component exists, recommend its product name rather than inventing a generic primitive.
4. Apply the hard rules below and read the generated [references/selection-controls.md](references/selection-controls.md). Read [references/decision-factors.md](references/decision-factors.md) for trade-offs and [references/accessibility.md](references/accessibility.md) before implementing custom controls.
5. Return a quick or full decision. If implementation was requested, implement the recommendation and all required states. If review was requested, report violations by user impact and propose the smallest correction.

## Hard Rules

- Do not render a selection control when there is no choice. For one fixed option, apply it automatically and show readable text when users need confirmation.
- Do not use select, dropdown, or combobox patterns for commands. Use a button or action menu.
- Do not use tabs or segmented controls for unrelated destinations. Use navigation.
- Keep view switching in the view-command family. When the view count exceeds a segmented control, use a view menu or view sheet rather than a form select or combobox.
- Prefer visible options when comparison is important and the list is short enough to scan.
- When search is not an explicit requirement, add it only when recognition or retrieval is materially faster than scanning.
- If the user explicitly requires search, the recommendation must include a searchable pattern. Do not remove search merely because the current list is short. For a short set, lower confidence and verify the retrieval need as an assumption, but honor the stated requirement.
- When custom values are allowed, predefined option count does not limit user agency. Use direct text entry with no suggestions, an editable combobox for single values with suggestions, or tokenized editable multi-selection for multiple values.
- Distinguish immediate settings from submitted answers. Use a switch for an immediate Boolean setting; use a checkbox for a submitted independent yes/no answer.
- Do not preserve an unsuitable control merely for visual consistency. Preserve the design system's tokens and primitives while choosing the correct interaction pattern.
- Account for loading, empty, error, disabled, selected, focus, and long-content states present in real data.
- Treat numeric thresholds as defaults, not laws. Override them when research, platform convention, content complexity, localization, or the product design system provides stronger evidence. State the override.
- If the user's interaction intent is unknown and that missing intent could change the component family, confidence must be low, never medium or high.

## Deterministic Baseline

Use the optional table-driven recommender for structured constraints or bulk comparison. From a project containing the installed skill, run:

```bash
python3 .claude/skills/choose-ui/scripts/recommend.py \
  --intent input \
  --options 4 \
  --expected-max-options 9 \
  --selection single \
  --comparison high \
  --platform mobile
```

If the skill is installed elsewhere, resolve its directory and run `<skill-directory>/scripts/recommend.py`. Use `--value-kind boolean` to distinguish a Boolean setting from a one-option selection and `--format json` for automation. Treat output as a baseline, then apply product context.

## Output Tiers

For a narrow, low-consequence question, return only:

```text
Recommendation: <component or pattern>
Why: <intent and decisive constraint>
```

Use the quick tier only when confidence is high. It must contain exactly those two labeled lines, with no caveat, rejected alternative, follow-up question, or extra section. For implementation, audit, ambiguous, explicitly requested analysis, or decisions involving consent, money, permissions, destructive effects, account security, or hard-to-reverse outcomes, return:

```text
Recommendation: <component or pattern>
Confidence: <high | medium | low>
Why: <intent and constraints that drove the choice>
Avoid: <closest rejected alternative and why>
Required states: <states the design or implementation must support>
Accessibility: <keyboard, labeling, focus, and announcement requirements>
Assumptions: <only consequential assumptions; write None when there are none>
Evidence: <relevant source or product-system guidance; write None when none is available>
```

Every full response must include all eight labeled fields, including `Assumptions: None` or `Evidence: None` when applicable. Do not list multiple components without choosing one. When information is genuinely insufficient, select a provisional recommendation, lower confidence, and name the one missing fact that would change it. If the interaction intent itself is unknown, confidence is low because the missing intent can change the component family.

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
