# Accessibility Requirements

Prefer native HTML controls unless a custom interaction provides necessary product value and can reproduce the expected semantics and keyboard behavior.

## All interactive controls

- Provide an accessible name that describes the purpose, not only the current value.
- Keep a visible focus indicator.
- Support keyboard operation without requiring pointer, hover, drag, or precise movement.
- Meet the product's target-size standard and provide adequate spacing between targets.
- Communicate disabled, required, invalid, expanded, and selected states programmatically.
- Do not use color as the only indicator.
- Preserve zoom, text resizing, high contrast, reduced motion, and long translated labels.

## Radio and checkbox groups

- Group related controls with `fieldset` and `legend` on the web.
- Make the label part of the activation target.
- State whether users may choose one or many when context is not obvious.
- Avoid disabling unavailable options without explaining why.

## Select and combobox

- Use native `select` when its behavior is sufficient.
- Follow an established ARIA combobox pattern for custom searchable controls.
- Announce result count and no-result states without moving focus unexpectedly.
- Preserve typed input when validation fails.
- Keep the selected value perceivable when the popup is closed.

## Segmented controls and tabs

- Use tab semantics only for actual tab panels.
- Use radio-group or pressed-button semantics for view switches according to the implementation pattern.
- Support arrow-key movement where the selected pattern convention requires it.
- Associate each tab with its panel and manage focus predictably.

## Menus

- Use menu semantics for commands, not ordinary site navigation or form choices.
- Return focus to the trigger when the menu closes.
- Support Escape and expected arrow-key navigation.

## Verification

Test with keyboard only, browser zoom, long labels, and at least one screen reader appropriate to the target platform. Automated checks are necessary but not sufficient.
