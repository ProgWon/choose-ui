# Decision Factors

Resolve component trade-offs in this order.

## 1. Semantic truth

Match the control to the task:

- button or menu for actions
- link or tabs for navigation
- radio, checkbox, select, or combobox for data entry
- segmented control for immediate switching within one view

Visual similarity does not make these patterns interchangeable.

## 2. Consequence timing

- Use controls with an immediate-setting convention only when changes apply immediately and feedback is visible.
- Keep form controls neutral until the user submits when changes require confirmation, validation, or a transaction.
- Add explicit Apply or Save actions when several choices form one decision.

## 3. Comparison cost

Keep options visible when users need to compare price, timing, risk, or descriptive details. Compact controls save space by charging users memory and interaction cost; make that trade only when comparison is unimportant.

## 4. Cardinality and growth

Design for the credible range, not a sample fixture. Ask whether an option set is fixed, localized, permission-dependent, or expected to grow. Avoid a component that works for three demo values but fails with twelve production values.

## 5. Frequency and expertise

- Optimize frequent expert workflows for speed, keyboard use, and stable ordering.
- Optimize infrequent workflows for recognition, explanations, and safe defaults.
- Do not hide essential choices merely because experts know where to find them.

## 6. Error cost and reversibility

- Prefer explicit, visible choices when a wrong selection is expensive.
- Preserve context and input after recoverable errors.
- Prefer undo for reversible actions; reserve confirmation for consequential, hard-to-reverse actions.

## 7. Platform and input method

- Favor native controls when they provide reliable accessibility and mobile behavior.
- Use large list surfaces on touch devices when options need scanning.
- Preserve keyboard navigation, focus visibility, and screen-reader semantics for custom controls.

## 8. Adaptive state transitions

- Model loading, resolved, and updated option sets as one coherent region.
- Preserve a still-valid user selection when new options arrive.
- Do not silently switch to a costlier or more consequential option.
- Preserve focus when the visual control changes shape and announce meaningful availability changes without forcing navigation.

## Confidence

- **High**: intent and all decision-changing constraints are known.
- **Medium**: one constraint is assumed but the recommendation is robust across likely values.
- **Low**: a missing fact could change the component family. Name that fact.
