# Live Claude Code comparison

This comparison uses the same prompt, Claude Code version, model alias, and fresh-session setting. The outputs below are unedited except for Markdown block quoting.

## Run conditions

- Date: 2026-08-05
- Claude Code: `2.1.222`
- Model alias: `sonnet` (resolved by Claude Code to `claude-sonnet-5`)
- Session persistence: disabled
- Baseline: safe mode, slash commands disabled, no tools
- Choose UI: project skill available, only the `Skill` tool enabled
- A repeated stream trace confirmed a `Skill` tool call with `skill: choose-ui` for this prompt.

Model output is nondeterministic. This is a transparent example, not a claim that every baseline run fails or every skilled run is identical.

## Prompt

> We are implementing the checkout shipping-method UI. Exactly one shipping option is currently available, and its value must be submitted with the order. Review which component we should use across desktop and mobile, and write the answer so an implementation team can act on it.

## Without Choose UI

> **Recommendation: single pre-selected radio button inside a radiogroup — same component on desktop and mobile.**
>
> - Use a `role="radiogroup"` / `<fieldset>` with one `<input type="radio" checked>`, not a checkbox (implies optional) or a dropdown (implies more choices to browse). This keeps the same markup pattern if a second shipping option is ever added, so there's no special-casing for "exactly one" vs "many."
> - Do **not** set `disabled` — disabled inputs are excluded from form submission, so the value wouldn't post. Leave it enabled and checked; since it's the only option, re-selecting it is a no-op for the user.
> - Label it with the shipping method name and price, same as you would for a multi-option list, so visual treatment doesn't need to branch based on option count.
> - This markup/behavior is identical across desktop and mobile — no separate mobile-specific component needed; just ensure normal responsive styling (radio + label tap target ≥44px on mobile).
>
> Net: one shared `<ShippingOptionRadio>`-style component, always rendered as a radiogroup even with a single item, value submitted via the checked radio's `name`/`value` pair.

## With Choose UI

> **Recommendation:** No selection control. Render the single shipping method as read-only confirmation text (label + name + price), and submit its value via a hidden field / pre-set form value rather than a form control the user interacts with. This applies identically on desktop and mobile — no responsive variant needed.
>
> **Confidence:** high
>
> **Why:** The interaction intent is *input* (a value must reach the order payload), but there is no actual choice to make — one option, no credible near-term second option implied by the ask. Rendering a select, radio group, or dropdown for a single item asks the user to "choose" something that isn't a choice, which is misleading and adds a pointless interaction step at the point of payment. The correct pattern is to auto-apply the value and simply *display* it for confirmation.
>
> **Avoid:** A disabled/pre-selected radio button or a single-item `<select>`. Both imply "there could be more here" and invite users to hunt for alternatives that don't exist; a disabled radio also reads as broken/loading to screen reader and sighted users alike, and disabled controls are frequently excluded from focus and value serialization in some frameworks, risking the value silently not being submitted.
>
> **Required states:**
> - Normal: shipping method name, delivery estimate, and price shown as static text/row (e.g., "Standard Shipping — $X, arrives in Y days").
> - Loading: skeleton/placeholder while the (single) rate is fetched, since "exactly one option" may still depend on an async rates call.
> - Error: if the rate fetch fails, show an inline error and block order submission — do not silently submit a stale or default value.
> - Multi-option future-proofing: if a second method can appear later (e.g., regional or promo-based rates), the underlying data model should already support a list so this text block can be swapped for a real selection control without a rework; that's a data-layer note, not a reason to build a selector now.
>
> **Accessibility:** The shipping cost/method text should be programmatically associated with the order summary (e.g., a labelled `dt`/`dd` pair or a row with `aria-label="Shipping method"`), not an interactive control, so it isn't exposed to assistive tech as a disabled/unusable input. The value submitted to the backend should come from a hidden input or from client state set at page load — not from a focusable form element — so no tab stop is wasted on a non-interactive item. If the fetched rate updates asynchronously, announce the update via a polite live region so screen reader users aren't left with stale pricing.
>
> **Assumptions:** The single option is a temporary/current-catalog state rather than a permanent one-and-only method for the business (i.e., the backend's shipping-rates response is a list that currently has length 1, not a hardcoded singleton) — this affects whether the "future-proofing" data-model note above is worth flagging to the team. If shipping method is genuinely and permanently singular for this business, the recommendation is unchanged but the future-proofing note can be dropped.
>
> **Evidence:** This follows the general "don't present a choice when there isn't one" convention used across major checkout UIs (e.g., Shopify and Stripe Checkout both auto-apply a single available shipping rate and show it as a line item rather than a selectable list, only surfacing a picker once ≥2 rates exist).

## Reproduce it

Baseline:

```bash
claude -p "<prompt above>" \
  --safe-mode \
  --disable-slash-commands \
  --tools "" \
  --model sonnet \
  --no-session-persistence
```

With Choose UI, run from a checkout containing this repository or an installed copy of the skill:

```bash
claude -p "<prompt above>" \
  --setting-sources project \
  --tools Skill \
  --model sonnet \
  --no-session-persistence
```
