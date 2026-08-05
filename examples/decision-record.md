# Decision Record Examples

## One shipping method

**Context:** Checkout has one available shipping method. The value is submitted with the order.

```text
Recommendation: static value
Confidence: high
Why: One fixed option creates no meaningful user choice.
Avoid: A disabled or one-item dropdown falsely implies choice.
Required states: loading, resolved, unavailable, long-content
Accessibility: Present the value as readable text and include it in submitted data programmatically.
```

## Four delivery speeds

**Context:** Users compare price and arrival date, then submit one choice.

```text
Recommendation: radio cards
Confidence: high
Why: Four detailed options should remain visible because comparison is important.
Avoid: A closed select forces users to remember hidden alternatives.
Required states: default, focus, selected, disabled, error, long-content
Accessibility: Associate the full card content with its radio and group the choices under one label.
```

## Sort commands disguised as a form field

**Context:** A toolbar dropdown contains Export, Duplicate, Archive, and Delete.

```text
Recommendation: action menu
Confidence: high
Why: The user is choosing among commands, not entering a value.
Avoid: Select and combobox patterns communicate data entry and hide destructive semantics.
Required states: closed, open, focus, disabled
Accessibility: Support Escape, arrow keys, focus return, and explicit command names.
```
