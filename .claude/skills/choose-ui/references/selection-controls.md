# Selection Controls

Use this matrix after classifying intent. Start with the first matching row, then apply content, platform, and accessibility constraints.

## Single selection

| Situation | Default pattern | Avoid | Reason |
| --- | --- | --- | --- |
| No available option | Empty state | Empty dropdown | There is nothing to select |
| One fixed option | Static value, auto-applied | Disabled dropdown | A control falsely implies choice |
| One immediate on/off setting | Switch | Radio group | The setting changes directly |
| One submitted yes/no answer | Checkbox when phrased independently | Switch | The value is committed with the form |
| 2–4 submitted options | Radio group | Select | Visible choices support comparison |
| 2–4 views of the same content | Segmented control | Tabs for unrelated pages | The control manipulates the current view |
| 2–5 peer sections | Tabs | Segmented control | The user navigates between sections |
| 5–11 simple options, low comparison need | Select | Long radio list | Compact scanning is sufficient |
| 6+ options on mobile | Input button opening a list or sheet | Tiny custom desktop dropdown | A larger picker improves touch and scanning |
| 12+ options or search materially helps | Combobox | Unsearchable long select | Retrieval is faster than scanning |
| Custom value allowed | Editable combobox | Closed select | Users must enter values outside the set |

## Multiple selection

| Situation | Default pattern | Avoid | Reason |
| --- | --- | --- | --- |
| One independent opt-in | Checkbox | Multi-select | It is a Boolean answer |
| 2–8 comparable options | Checkbox group | Multi-select | All choices remain visible |
| Short keyword filters | Selection chips | Checkboxes in a dense toolbar | Chips support lightweight toggling |
| Many options on mobile | Button opening checkbox list or sheet | Dense inline list | The larger surface supports scanning |
| Many searchable options | Multi-select combobox with removable tokens | Native multi-select listbox | Search and visible selections reduce recall |

## Intent overrides

### Action

- Use one button for one action.
- Use an action menu for several secondary actions when space is constrained.
- Keep destructive actions explicit and visually distinct.
- Do not disguise actions as selectable values.

### Navigation

- Use links, navigation lists, tabs, or a command palette depending on hierarchy and scale.
- Use tabs only for peer sections whose content can be understood independently.
- Do not use a select solely to move between a few destinations unless severe space constraints and platform convention justify it.

### Filter

- Prefer chips or visible checkboxes for a short, frequently changed set.
- Prefer a select for one compact, low-frequency filter.
- Prefer a filter panel or sheet when several criteria must be combined.
- Show active filters outside a closed surface so users can understand the current result set.

## Edge cases

- If data is still loading, show loading state rather than a one-option control that later changes shape.
- When the option set resolves and the control changes shape, preserve any still-valid selection and user focus. Announce newly available options without moving focus or silently switching to a more expensive or consequential value.
- If an option is fixed by permission, policy, inventory, or prior answers, explain the constraint next to a static value.
- If options contain descriptions users must compare, use radio cards or select boxes rather than hiding descriptions in a dropdown.
- If labels localize to long text, favor vertical layouts and larger surfaces.
- If the option count crosses a threshold only occasionally, choose the pattern that handles the realistic upper bound without degrading the common case.
