# UI Design System

## Design direction

**Calm Household Intelligence**

The interface should feel:
- warm;
- quiet;
- trustworthy;
- modern;
- highly practical.

Visual polish supports task completion. It does not compete with it.

## Anti-goals

Avoid:
- neon gradients;
- decorative glassmorphism everywhere;
- dashboard chart overload;
- oversized hero sections inside the authenticated app;
- constant motion;
- multiple competing accent colors;
- tiny icon-only controls;
- card-for-everything layouts.

## Layout

### Content widths

- App shell max width: 1200–1280 px.
- Editorial reading width: 680–760 px.
- Mobile side gutters: 16–20 px.
- Desktop section gaps: 32–48 px.

### Breakpoint behavior

- <640px: single column + bottom navigation.
- 640–899px: spacious single column / selective two-column.
- 900–1199px: desktop two-column layouts where useful.
- ≥1200px: constrained workspace, never stretch content indefinitely.

Breakpoints are driven by content needs, not device names.

## Spacing scale

Use a small token scale:

```
4, 8, 12, 16, 24, 32, 48, 64
```

Avoid one-off spacing values unless documented.

## Color roles

Do not hard-code semantic meaning to a specific color name in component logic.

Roles:
- canvas: warm off-white;
- surface: white / warm white;
- primary: deep sage;
- primary-subtle: pale sage;
- text-primary: charcoal;
- text-secondary: muted gray/olive;
- attention: restrained amber;
- danger: restrained brick;
- border: warm neutral.

Color must never be the sole state indicator.

## Typography

Prefer a robust system sans stack for the product UI.

Suggested scale:
- Marketing hero: 48–64 desktop, 36–42 mobile.
- App H1: 30–36.
- H2: 24–28.
- H3: 18–20.
- Body: 16.
- Small/meta: 13–14.

Body copy should not drop below 16px on mobile unless there is a specific reason.

Editorial pages may introduce one complementary serif display face only if loading/performance cost is justified.

## Elevation and radius

- Major cards: 16–20px radius.
- Controls: 10–14px radius.
- Shadows: subtle, low elevation.
- Prefer borders/tonal separation over heavy shadow stacks.

## Component rules

### Buttons

Primary:
- one dominant task per region;
- high contrast;
- descriptive verb.

Secondary:
- important alternate path;
- lower visual weight.

Tertiary:
- text/icon action for edit/remove/navigation.

Destructive actions:
- not visually dominant by default;
- Undo preferred for reversible low-risk deletion;
- confirmation reserved for meaningful irreversible impact.

### ItemRow

Used for shopping/pantry lists.

Contains:
- state control/icon;
- primary label;
- concise metadata;
- optional trailing action.

Do not convert every row into a floating card.

### AttentionCard

Used on Today.

Contains:
- reason for attention;
- concrete object;
- single next-best action;
- optional secondary action.

No charts inside attention cards.

### StatusBadge

Text label is mandatory.
Examples:
- Low stock
- Use today
- Due tomorrow

### Snackbar

Use for:
- saved;
- added;
- completed;
- removed + Undo.

Do not use as the only place for critical errors.

### Bottom sheet

Preferred mobile pattern for:
- Quick Add;
- compact selection;
- contextual actions.

Must:
- trap focus while modal;
- close with Escape;
- provide visible close control;
- return focus to trigger.

## App navigation

### Mobile

```
Today | Plan | + | Home | Learn
```

The central quick-add action is distinct but not oversized.

### Desktop

```
Today | Plan | Shopping | Pantry | Routines | Discover
```

Search/account are utility actions.

## Today visual hierarchy

Above the fold should prioritize:
1. date/context;
2. 2–3 actionable signals;
3. current plan.

Avoid giant greetings and decorative art.

## Forms

Do not use `{{ form.as_div }}` in final high-value product flows.

Render fields deliberately:
- label;
- control;
- optional help text;
- error.

Requirements:
- clear required/optional behavior;
- auto-complete where appropriate;
- correct input types;
- no placeholder-only labels;
- preserve values after validation errors.

## Motion

Default:
- 150–200ms for state changes;
- subtle easing;
- no permanent motion.

Allowed:
- item completion;
- bottom-sheet entrance;
- snackbar;
- small insert/remove transition.

Always respect `prefers-reduced-motion`.

## Focus

Every interactive component must have a strong `:focus-visible` treatment.

No `outline: none` without an accessible replacement.

Sticky headers/bottom nav must not obscure focused content.

## Pointer targets

Internal target:
- aim for at least 44×44 CSS px for primary mobile controls.

Minimum conformance:
- WCAG 2.2 AA Target Size (Minimum), including documented exceptions.

## Content density

A visible element must support at least one:
- understand;
- decide;
- act;
- recover.

If it does none, remove it unless it carries essential brand/context value.

## Responsive behavior acceptance

Every primary flow is manually checked at:
- 360px;
- 390px;
- 768px;
- 1024px;
- 1280px.

No horizontal scrolling except deliberately scrollable content.

## Wagtail editor design

Block chooser groups:

**Essentials**
- Hero
- Rich text
- Image
- Feature grid

**Home knowledge**
- Ingredients
- Steps
- Tip
- Warning
- Checklist
- Storage advice

**Actions**
- Shopping action
- Routine action
- Related recipes

Editor principles:
- short block names;
- useful descriptions;
- constrained content;
- preview where it improves author confidence;
- help text for accessibility/content rules;
- no unrestricted HTML escape hatch.

## Design review checklist

1. Is hierarchy obvious at a glance?
2. Is there exactly one dominant action where appropriate?
3. Does the layout work at 360px?
4. Are tap targets generous?
5. Is focus visible?
6. Is state understandable without color?
7. Are empty/error/loading states designed?
8. Is typography readable?
9. Is motion optional/reduced?
10. Does every card exist for a semantic reason?
11. Are labels and microcopy user-oriented rather than model-oriented?
12. Can visual polish be removed without harming the workflow? If yes, ensure it is lightweight.


## PR2 implementation contract

The first production UI primitives are implemented in `mysite/static/css/mysite.css` using cascade layers and semantic design tokens.

Stable primitives:
- `.shell` — constrained responsive workspace;
- `.button` with primary/secondary/ghost variants;
- `.field`, `.field__label`, `.field__control`, `.field__error`;
- `.item-list` / `.item-row`;
- `.status-badge`;
- `.attention-card`;
- `.empty-state`;
- `.snackbar`;
- `.surface-panel`;
- `.page-heading`, `.eyebrow`, `.lede`;
- desktop and mobile navigation shells.

Implementation rules:
- system fonts only; no font-request dependency;
- no JavaScript required for baseline navigation/layout;
- only real destinations appear in navigation;
- mobile primary navigation targets meet the internal 44px target;
- semantic state names are used in markup instead of color names;
- new product modules extend these primitives before creating one-off component styles;
- link-row click expansion is scoped only to `.item-row--link`, preserving future nested controls in transactional rows.

The current navigation intentionally exposes only Today, Discover and authentication/content destinations. Plan, Shopping, Pantry, Routines and Quick Add must be introduced when their routes/workflows exist, not as dead links.
