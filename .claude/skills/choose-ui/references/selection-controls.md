# Selection Controls

> Generated from `selection-rules.json`. Do not edit this matrix by hand. Run `python3 .claude/skills/choose-ui/scripts/rules_tool.py --write` after changing canonical rules.

Rules are ordered: the first matching row wins. Numeric boundaries are defaults, not laws; product research, content, localization, platform conventions, or an established design system may justify an explicit override.

## Canonical thresholds

| Name | Value |
| --- | ---: |
| `segmented_max` | 4 |
| `tabs_max` | 5 |
| `radio_default_max` | 4 |
| `radio_compare_max` | 6 |
| `mobile_sheet_min` | 6 |
| `visible_multi_max` | 8 |
| `combobox_min` | 12 |

## No choice and Boolean values

| Rule | Match | Choose | Avoid | Why |
| --- | --- | --- | --- | --- |
| `selection-loading` | intent: input / filter / setting; value kind: selection; options ≤ 0; options at credible maximum ≥ 1 | loading selection region | Empty or disabled picker | The current empty set is unresolved; design for the credible option range. |
| `boolean-immediate` | intent: input / setting; value kind: boolean; effect: immediate | switch | Radio group or select | This is an immediate on/off value whose state changes directly. |
| `boolean-submit` | intent: input / setting; value kind: boolean; effect: submit | checkbox | Switch | This independent yes/no answer is committed with the surrounding form. |
| `selection-none` | intent: input / filter / setting; value kind: selection; options at credible maximum ≤ 0 | empty state | Empty dropdown | There is nothing to select. |
| `selection-one-single` | intent: input / filter / setting; value kind: selection; selection: single; options at credible maximum ≥ 1 and ≤ 1 | static value | Disabled or one-item dropdown | One fixed option creates no meaningful choice. |
| `selection-one-multiple` | intent: input / filter / setting; value kind: selection; selection: multiple; options at credible maximum ≥ 1 and ≤ 1 | checkbox | Multi-select | One optional item is an independent include/exclude answer. |

## Actions and navigation

| Rule | Match | Choose | Avoid | Why |
| --- | --- | --- | --- | --- |
| `action-none` | intent: action; options at credible maximum ≤ 0 | no action trigger | Empty menu or disabled overflow button | No command is available, so an action trigger would open an empty surface. |
| `action-one` | intent: action; options at credible maximum ≥ 1 and ≤ 1 | button | One-item action menu | One command needs one direct action, not a disclosure step. |
| `action-many` | intent: action; options at credible maximum ≥ 2 | action menu | Select or combobox | The user is choosing among commands, not entering a value. |
| `navigation-none` | intent: navigation; options at credible maximum ≤ 0 | no navigation control | Empty tabs or navigation menu | No destination is available. |
| `navigation-one` | intent: navigation; options at credible maximum ≥ 1 and ≤ 1 | direct link | One-item menu or tab strip | One destination needs a direct path, not a chooser. |
| `navigation-tabs` | intent: navigation; options at credible maximum ≥ 2 and ≤ 5 (`tabs_max`) | tabs | Segmented control | A short set of peer sections can remain visible as navigation. |
| `navigation-list` | intent: navigation; options at credible maximum > 5 (`tabs_max`) | navigation list | Overfilled tabs or form select | The destination count exceeds a compact tab set. |

## Multiple selection

| Rule | Match | Choose | Avoid | Why |
| --- | --- | --- | --- | --- |
| `multiple-search` | intent: input / filter / setting; selection: multiple; search: yes; options at credible maximum ≥ 2 | multi-select combobox | Chips or unsearchable checklist | Explicit search needs retrieval before any compact visible-filter rule. |
| `input-multiple-rich` | intent: input / setting; selection: multiple; rich option content: yes; options at credible maximum ≥ 2 and ≤ 8 (`visible_multi_max`) | checkbox cards | Closed multi-select | Descriptions must remain visible for comparing independent choices. |
| `input-multiple-compare` | intent: input / setting; selection: multiple; comparison: high; options at credible maximum ≥ 2 and ≤ 8 (`visible_multi_max`) | checkbox comparison group | Closed multi-select | A comparable short set should remain visible while allowing independent choices. |
| `input-multiple-visible` | intent: input / setting; selection: multiple; options at credible maximum ≥ 2 and ≤ 8 (`visible_multi_max`) | checkbox group | Multi-select | The full option set fits as visible independent choices. |
| `input-multiple-mobile` | intent: input / setting; selection: multiple; platform: mobile; options at credible maximum > 8 (`visible_multi_max`) | button opening a checkbox sheet | Dense inline checklist | Many values need a touch-friendly selection surface. |
| `input-multiple-large` | intent: input / setting; selection: multiple; platform: any / desktop; options at credible maximum > 8 (`visible_multi_max`) | multi-select combobox | Native multi-select listbox | The large set benefits from retrieval and visible selected tokens. |

## Single selection

| Rule | Match | Choose | Avoid | Why |
| --- | --- | --- | --- | --- |
| `single-custom` | intent: input / filter / setting; selection: single; custom values: yes; options at credible maximum ≥ 2 | editable combobox | Closed select | Users must enter a value outside the predefined set. |
| `single-search` | intent: input / filter / setting; selection: single; search: yes; options at credible maximum ≥ 2 | combobox | Unsearchable select | Explicit retrieval needs search or type-ahead. |
| `single-large` | intent: input / filter / setting; selection: single; options at credible maximum ≥ 12 (`combobox_min`) | combobox | Unsearchable long select | The option count makes retrieval faster than scanning. |
| `input-single-mobile-rich` | intent: input / setting; selection: single; platform: mobile; rich option content: yes; options at credible maximum ≥ 6 (`mobile_sheet_min`) and < 12 (`combobox_min`) | input button opening a rich comparison sheet | Closed select | Rich option content needs a larger touch-friendly comparison surface. |
| `input-single-mobile-compare` | intent: input / setting; selection: single; platform: mobile; comparison: high; options at credible maximum ≥ 6 (`mobile_sheet_min`) and < 12 (`combobox_min`) | input button opening a comparison sheet | Closed select | Detailed comparison needs more room than an inline control provides. |
| `input-single-mobile` | intent: input / setting; selection: single; platform: mobile; options at credible maximum ≥ 6 (`mobile_sheet_min`) and < 12 (`combobox_min`) | input button opening a selection sheet | Small desktop-style popup | The option count benefits from a touch-friendly scanning surface. |
| `input-single-mobile-rich-visible` | intent: input / setting; selection: single; platform: mobile; rich option content: yes; options at credible maximum ≥ 2 and < 6 (`mobile_sheet_min`) | radio cards | Closed select | The rich set remains small enough for visible mobile comparison. |
| `input-single-mobile-compare-visible` | intent: input / setting; selection: single; platform: mobile; comparison: high; options at credible maximum ≥ 2 and < 6 (`mobile_sheet_min`) | radio group | Closed select | The comparable set remains small enough to keep visible on mobile. |
| `input-single-rich` | intent: input / setting; selection: single; platform: any / desktop; rich option content: yes; options at credible maximum ≥ 2 and ≤ 6 (`radio_compare_max`) | radio cards | Closed select | Descriptions must remain visible for direct comparison. |
| `input-single-compare` | intent: input / setting; selection: single; platform: any / desktop; comparison: high; options at credible maximum ≥ 2 and ≤ 6 (`radio_compare_max`) | radio group | Closed select | A comparable short set should remain visible. |
| `input-single-short` | intent: input / setting; selection: single; options at credible maximum ≥ 2 and ≤ 4 (`radio_default_max`) | radio group | Select | The short set fits as visible single-choice input. |
| `input-single-comparison-list` | intent: input / setting; selection: single; comparison: high; platform: any / desktop; options at credible maximum > 6 (`radio_compare_max`) and < 12 (`combobox_min`) | comparison list with radio selection | Closed select | Detailed comparison remains important despite the longer list. |
| `input-single-compact` | intent: input / setting; selection: single; options at credible maximum > 4 (`radio_default_max`) and < 12 (`combobox_min`) | select | Long radio list | The simple set does not need visible comparison or search. |

## View switches and filters

| Rule | Match | Choose | Avoid | Why |
| --- | --- | --- | --- | --- |
| `view-switch-none` | intent: view-switch; options at credible maximum ≤ 0 | no view control | Empty segmented control or view menu | No alternate view is available. |
| `view-switch-one` | intent: view-switch; options at credible maximum ≥ 1 and ≤ 1 | static view label | One-item segmented control or view menu | One presentation mode is a state label, not a meaningful switch. |
| `view-switch-short` | intent: view-switch; options at credible maximum ≥ 2 and ≤ 4 (`segmented_max`) | segmented control | Tabs | A short set of choices immediately changes the presentation of the same content. |
| `view-switch-mobile-long` | intent: view-switch; platform: mobile; options at credible maximum > 4 (`segmented_max`) | button opening a view sheet | Overfilled segmented control or form select | The view count exceeds a compact segmented control on a touch surface. |
| `view-switch-long` | intent: view-switch; platform: any / desktop; options at credible maximum > 4 (`segmented_max`) | view menu | Radio group or form select | The interaction remains a view-mode command even when the compact control no longer fits. |
| `filter-single-mobile` | intent: filter; selection: single; platform: mobile; options at credible maximum ≥ 6 (`mobile_sheet_min`) and < 12 (`combobox_min`) | button opening a selection sheet | Small desktop-style popup | The filter needs a touch-friendly scanning surface. |
| `filter-single-frequent` | intent: filter; selection: single; frequency: high; options at credible maximum ≥ 2 and ≤ 4 (`segmented_max`) | segmented control | Closed select | A short, frequently changed filter benefits from visible immediate choices. |
| `filter-single-compact` | intent: filter; selection: single; options at credible maximum ≥ 2 and < 12 (`combobox_min`) | select | Radio group for a low-frequency compact filter | One compact, low-frequency filter does not require visible comparison. |
| `filter-multiple-frequent` | intent: filter; selection: multiple; frequency: high; rich option content: no; options at credible maximum ≥ 2 and ≤ 8 (`visible_multi_max`) | selection chips | Closed multi-select | Short keyword filters can remain visible for frequent toggling. |
| `filter-multiple-rich` | intent: filter; selection: multiple; rich option content: yes; options at credible maximum ≥ 2 and ≤ 8 (`visible_multi_max`) | checkbox cards | Selection chips that hide option descriptions | Rich filter details must stay visible next to each independent choice. |
| `filter-multiple-visible` | intent: filter; selection: multiple; options at credible maximum ≥ 2 and ≤ 8 (`visible_multi_max`) | checkbox group | Hidden multi-select | The full filter set fits as visible independent choices. |
| `filter-multiple-mobile` | intent: filter; selection: multiple; platform: mobile; options at credible maximum > 8 (`visible_multi_max`) | button opening a checkbox sheet | Dense inline checklist | The larger surface supports touch scanning and combined application. |
| `filter-multiple-panel` | intent: filter; selection: multiple; platform: any / desktop; options at credible maximum > 8 (`visible_multi_max`) | filter panel with checkboxes | Unsearchable multi-select listbox | Many combined criteria need a dedicated surface and visible active filters. |

## Context beyond the table

Use `decision-factors.md` when a threshold needs an override. Use `design-system-adapter.md` to translate the generic recommendation to components already present in a product. Use `accessibility.md` before implementing a custom widget.
