# Design-System Adapter

Translate the generic decision into the product's existing component language before proposing new UI.

## Inventory first

1. Search component imports, stories, design-system packages, local documentation, and nearby screens.
2. Confirm behavior, not just names. A `SelectBox` may be a rich radio card while a `Select` may be a compact picker.
3. Reuse the product component when it satisfies the chosen semantics and required states.
4. If no suitable component exists, recommend the generic pattern and name the missing capability. Do not invent a product-specific component name.
5. Preserve tokens, validation, analytics, focus behavior, and data contracts when replacing a mismatched control.

If no repository or product inventory is available, use the generic pattern name and state that no project component inventory was inspected. Do not guess package imports, wrapper names, props, or version-specific APIs.

Project evidence outranks the mapping below. Record a threshold or pattern override when the design system has stronger platform guidance.

## SEED mapping example

| Generic recommendation | Inspect in SEED | Notes |
| --- | --- | --- |
| Radio group | [Field / Radio](https://seed-design.io/components/radio) | Short, visible single selection |
| Radio cards or checkbox cards | [Select Box](https://seed-design.io/components/select-box) | Rich option descriptions; choose the radio or check control |
| Selection chips | [Chip](https://seed-design.io/components/chip) | Short, lightweight immediate filters |
| Compact single selection | [Select](https://seed-design.io/components/select) | Keep a persistent field label |
| Mobile selection sheet | Input Button + [Bottom Sheet](https://seed-design.io/components/bottom-sheet) + Radio/List | Compose a large touch surface instead of shrinking a desktop popup |
| Action menu | Action Button + Menu or Menu Sheet | Commands are actions, not form values |
| View switch | [Segmented Control](https://seed-design.io/components/segmented-control) | Changes the presentation of the same content |
| Peer-section navigation | [Tabs](https://seed-design.io/components/tabs) | Moves between peer content sections |
| Immediate Boolean setting | [Switch](https://seed-design.io/components/switch) | Apply immediately and show feedback |

Verify current component names and APIs in the installed SEED version or project wrapper before implementation.
