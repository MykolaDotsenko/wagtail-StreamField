# UX Research & User Flows

## UX objective

DomoNest should minimize:
- remembering;
- navigation;
- typing;
- configuration;
- repeated entry;
- ambiguity about current state.

The user should spend time **doing household work**, not maintaining household software.

## UX heuristics

### 1. Action before analytics
Show what the user can do next before totals, charts or historical statistics.

### 2. Progressive disclosure
Ask for the minimum information required to complete the immediate task. Advanced fields appear only when relevant.

### 3. Preserve context
Actions such as "add missing ingredients" should confirm inline/snackbar and keep the user on the current recipe unless navigation is necessary.

### 4. Safe reversibility
Frequent low-risk actions should support Undo rather than repeated confirmation dialogs.

### 5. Human time language
Prefer "Tomorrow", "In 2 days", "2 days overdue" with exact date as secondary context.

### 6. Soft urgency
Use "Needs attention" rather than alarmist language except for genuinely dangerous states.

### 7. Visible system rules
When automation acts, explain the result:
- "Next due Saturday."
- "3 missing ingredients added."
- "Milk grouped under Dairy."

## Primary persona

### Household manager

Characteristics:
- carries a significant share of household planning;
- often uses the product one-handed on mobile;
- frequently interrupted;
- values speed over exhaustive data entry;
- may use it while shopping or cooking;
- does not want a complicated project-management tool.

Important constraint:
- interruption tolerance matters. Partial form input and current context should not disappear unnecessarily.

## Information architecture

### Desktop

- Today
- Plan
- Shopping
- Pantry
- Routines
- Discover
- Search
- Account

### Mobile bottom navigation

- Today
- Plan
- Quick Add
- Home
- Learn

"Home" contains Shopping, Pantry and Routines via local navigation. This keeps the global mobile navigation compact.

## Flow 1 — Today

Entry:
- login redirect;
- primary app route;
- optional home-screen/bookmark entry.

PR6 deterministic priority:
1. overdue routine;
2. expired pantry item;
3. routine due today;
4. pantry use-soon;
5. pantry low stock;
6. active shopping summary.

The visible feed is capped at six actions. Meal planning remains a neutral placeholder until the meal domain exists.

Do not show more than the user can act on. A "View all" path is preferable to a dense wall.

### Today card anatomy

- semantic icon or status;
- short headline;
- concrete context;
- exactly one primary action where possible;
- optional secondary action;
- no decorative metadata.

Example:

```
Milk expires tomorrow
1 L remaining
[Use in a recipe]   [Details]
```

## Flow 2 — Quick Add

Trigger:
- central mobile action;
- keyboard shortcut may be added on desktop later.

Step 1: choose intent:
- Shopping item
- Pantry item
- Routine
- Meal

Step 2:
- focus primary field immediately;
- minimal input;
- smart/default classification where deterministic;
- More options stays collapsed.

Exit:
- success confirmation;
- user returns to previous context;
- no forced redirect.

### Shopping quick add acceptance

A user can add:
- name only;
- in one form submission;
- with sensible quantity/category defaults.

## Flow 3 — Shopping

Primary mode:
- grouped list;
- open items first;
- completed items visually secondary;
- completion is one tap.

Shopping mode:
- hides editing/recommendation noise;
- uses large targets;
- preserves category grouping;
- keeps item count visible.

### Completion behavior

On completion:
1. the server records `COMPLETED` and `completed_at`;
2. the item moves to the Bought section in normal mode;
3. a success message confirms the change;
4. the Bought item can be reopened with the same one-tap control.

In Shopping mode, completed items disappear from the active shopping surface after the redirect so the screen stays focused on what remains.

Never make swipe the only interaction.

### Duplicate behavior

Quick Add uses normalized item identity. Adding an equivalent open item increases its quantity instead of creating a second active row.

Normalization is intentionally conservative:
- Unicode NFKC;
- whitespace collapse;
- case folding.

No fuzzy/semantic matching is claimed.

### Remove and Undo

Remove is distinct from completion.

The initial remove is a soft delete. The redirect carries only the removed item ID, and the server re-resolves that ID through the authenticated user's queryset before showing Undo.

Undo is a POST action. If an equivalent open item was created after removal, Undo merges quantities rather than violating the active-item uniqueness invariant.

### PR3 progressive enhancement decision

The baseline Shopping flow uses ordinary Django forms and redirects. No JavaScript or HTMX is required for add, complete, reopen, remove, Undo or Shopping mode. This establishes correct semantics before optional partial-page enhancement.

## Flow 4 — Pantry

Pantry is **not accounting software**.

PR4 baseline:
- name-only add creates Approximate / Full;
- Stock details is progressive disclosure;
- precise tracking is opt-in;
- Needs attention is derived from current state;
- expiry missing is shown as "Expiry unknown";
- Pantry → Shopping is idempotent.

Two quantity modes are planned:
- precise: 1.5 kg;
- approximate: full / half / low.

Primary sections:
1. Needs attention.
2. Everything else.

Attention reasons:
- expiring soon;
- expired;
- low stock.

Primary actions:
- add to shopping;
- use in recipe;
- update quantity.

## Flow 5 — Meal planning

MVP plans dinner only.

Mobile:
- vertical day list;
- one meal card per day.

Desktop:
- seven-day view may be used if it remains readable.

Meal selection should prioritize:
- pantry readiness;
- time;
- user-relevant tags;
- number of missing ingredients.

Never imply algorithmic intelligence beyond implemented deterministic ranking.

## Flow 6 — Recipe → shopping

Implemented in PR9.

1. User opens RecipePage.
2. Authenticated users get an owner-scoped Pantry comparison.
3. Each ingredient shows one explicit state:
   - At home;
   - Running low;
   - Missing;
   - Check stock.
4. UNKNOWN/"Check stock" is deliberately non-automated: the system does not pretend approximate, expired or incompatible-unit stock is sufficient.
5. Optional missing ingredients are visible but excluded from automatic Shopping demand.
6. User selects "Add N needed items to Shopping".
7. Only MISSING + LOW non-optional ingredients are ensured on the active Shopping list.
8. User sees confirmation and remains on the recipe.

Anonymous readers still get the full public recipe. Pantry comparison remains private behind authentication.

### Duplicate and retry rule

Recipe → Shopping is idempotent. It reuses canonical Ingredient links first and conservative normalized-name identity second. Repeated POSTs do not increase Shopping quantity or create duplicate active demand.

UNKNOWN is never auto-added.

## Flow 7 — Home routines

A routine is a recurring definition; a completion is history.

PR5 names the product surface **Home rhythm**. High-frequency view is split into Due now and Upcoming. Due cards expose Done / Skip / Postpone / Edit; archive lives only in Edit. Postpone is explicitly one-off and does not alter cadence.

Routine card displays:
- title;
- room;
- due state;
- expected effort if available;
- recurrence;
- completion action.

Actions:
- Done.
- Skip this occurrence.
- Postpone.
- Edit routine.

Completion:
- records history;
- calculates next due date;
- confirms next due date.

## Flow 8 — Guide → action

Examples:
- cleaning guide → add routine;
- seasonal checklist → add selected tasks;
- food storage guide → open pantry or add relevant item.

Content should be useful even without an account, but action conversion may require login.

After login, return users to the initiating content/action when feasible.

## Onboarding

No carousel tutorial.

Step 1:
"What would help most today?"
- Shopping
- Meals
- Pantry
- Routines

Step 2:
Take the user directly into a meaningful setup/action.

Step 3:
Show the populated Today state.

Progressive onboarding should continue through contextual suggestions, not a forced wizard.

## Empty states

Every empty state contains:
1. What this area is.
2. Why it is useful.
3. One next action.

Avoid "No data".

## Validation

- Server-side is authoritative.
- Field-level errors appear next to fields.
- After submit failure, focus first invalid field.
- Do not show errors while a user has barely begun typing.
- Preserve submitted values.

## Loading and latency

Django SSR is the baseline.

For progressive enhancement:
- use local button/pending state;
- avoid full-screen spinners;
- disable duplicate submit only while necessary;
- do not optimistically claim persistence before success unless rollback is implemented.

## Error recovery

Messages should state:
- what failed;
- whether user input was preserved;
- what the user can do next.

Example:

"Couldn't add this item. Your entry is still here. Try again."

## Accessibility interaction rules

- All pointer actions have keyboard equivalents.
- Drag-and-drop always has a non-drag alternative.
- Focus must remain visible and not be obscured by sticky UI.
- Status is not communicated by color alone.
- Touch targets should aim for 44×44 CSS px, with WCAG 2.2 AA minimum always met.
- Reduced-motion preference is respected.

See `06_QUALITY_SECURITY_ACCESSIBILITY.md`.

## UX review checklist

For each new flow ask:

1. Can the primary task be completed with fewer steps?
2. Can a default safely remove a field?
3. Does the user understand what changed?
4. Can an accidental action be undone?
5. Does mobile one-handed use work?
6. Does keyboard-only use work?
7. Does the user retain context?
8. Is every visible element actionable or decision-supporting?
9. Is there a clear empty/loading/error state?
10. Does the flow reduce mental load rather than move it into the app?
