# Domain Model

This document defines intended business entities and invariants. Implementation may evolve, but changes to these rules require explicit documentation/ADR updates.

## Terminology

### Household
Logical owner of private household data.

MVP may map this 1:1 to a Django user. Future family sharing may introduce an explicit Household aggregate.

### Shopping item
An intended purchase that is open or completed.

### Pantry item
A tracked household stock item with optional quantity/expiry information.

### Routine
A reusable recurring or one-off household responsibility.

### Routine occurrence/completion
A dated instance/history record for a routine.

### Meal plan entry
A planned recipe/meal on a date.

### Recipe
Public/editorial Wagtail content with structured ingredient data.

### Ingredient
Canonical ingredient identity usable by recipes and pantry/shopping reconciliation.

## Shopping

Implemented in PR3:
- direct user ownership for the MVP;
- display name;
- normalized item identity;
- integer quantity;
- category;
- `OPEN / COMPLETED` state;
- `completed_at`;
- `deleted_at` for reversible removal;
- created/updated timestamps.

Unit-aware quantities are intentionally deferred until pantry/recipe integration creates a real need.

### Invariants

1. Quantity is at least 1.
2. Normalized identity cannot be empty.
3. User cannot mutate another user's item.
4. At most one non-deleted `OPEN` item exists per user + normalized identity.
5. `OPEN` requires `completed_at IS NULL`.
6. `COMPLETED` requires `completed_at IS NOT NULL`.
7. Equivalent Quick Add requests merge quantity rather than create active duplicates.
8. Completing an item is reversible.
9. Reopening into an already-existing equivalent open item merges quantities.
10. Completed items are not used as active shopping demand.
11. Removal is distinct from completion and is initially soft-deleted so it can be undone.

Database constraints protect invariants 1–6 where applicable.

### State

```
OPEN → COMPLETED
COMPLETED → OPEN   (undo/reopen)
```

Deletion is separate from completion.

## Pantry

Implemented in PR4:
- direct user ownership for the MVP;
- normalized unique pantry identity per user;
- category aligned with Shopping categories;
- approximate or precise quantity mode;
- optional expiry date;
- optional low-stock threshold for precise mode;
- derived attention state only — no persisted "expired" / "low" flags.

Quantity mode:

```
PRECISE | APPROXIMATE
```

Precise:
- amount;
- unit.

Approximate:
- FULL;
- HALF;
- LOW.

Optional:
- expires_on;
- low_stock_threshold;
- category.

### Derived states

`is_expired`
- expires_on < today.

`expires_soon`
- configurable deterministic horizon; MVP default 3 days.

`is_low_stock`
- threshold comparison for precise quantities;
- LOW for approximate quantity.

### Invariants

1. Pantry identity is normalized deterministically and cannot be empty.
2. A user has at most one pantry row per normalized identity.
3. Precise quantity cannot be negative.
4. Precise mode requires amount + unit and may optionally define a non-negative low-stock threshold.
5. Approximate mode stores only FULL / HALF / LOW and clears precise-only fields.
6. Missing expiry date means "unknown", not "safe".
7. LOW is derived directly from approximate state; precise low-stock is derived from amount <= threshold.
8. Expired / use-soon / low-stock states are not separately persisted.
9. Pantry mutations and reads are owner-scoped.
10. "Add to Shopping" ensures active shopping demand exists but is idempotent; repeated clicks do not inflate quantity.

Database constraints protect identity, uniqueness, non-negative precise values and quantity-mode consistency.

## Routines

Implemented in PR5 as a real recurrence model rather than an `is_done` task.

Routine:
- title;
- room/category;
- recurrence rule;
- active;
- expected_duration optional;
- start/due anchor;
- owner.

Occurrence/completion:
- routine;
- scheduled_for;
- outcome: completed / skipped / postponed;
- completed_at;
- optional note.

### MVP recurrence

Support:
- one-time;
- daily;
- weekly;
- monthly.

Do not add arbitrary cron/RRULE UI until justified.

### Invariants

1. Routine stores the current recurrence rule and cadence date; RoutineEvent stores immutable action history.
2. Completing or skipping records a terminal history event for the current scheduled occurrence.
3. A scheduled occurrence can have at most one terminal outcome.
4. Completion does not permanently mark a recurring routine done.
5. One-time completion/skip deactivates the routine but preserves history.
6. Daily/weekly/monthly next due dates are deterministic and advance to the first cadence strictly after today, collapsing stale backlog.
7. Monthly routines preserve their original day-of-month anchor across short months.
8. Postpone changes only the effective due date, not the recurrence anchor/cadence date.
9. Repeated/stale browser submissions cannot accidentally act on the newly advanced occurrence.
10. Skip is distinct from complete.
11. Archive stops future due dates while preserving history.
12. Routine state/history is user-owned/private.

## Recipes

Implemented in PR8 as Wagtail editorial content.

RecipePage stores:
- title / intro;
- optional hero image + context-specific alt text;
- prep minutes;
- cook minutes;
- servings;
- difficulty;
- tags;
- structured ingredient rows;
- curated instruction StreamField;
- searchable ingredient-name text.

`total_minutes` is derived from prep + cook time rather than persisted.

### Ingredient line

RecipeIngredient is an `Orderable` inline relation so editors can manage structured rows inside the RecipePage editing experience.

Fields:
- canonical Ingredient reference;
- numeric amount optional;
- unit optional;
- preparation note optional;
- optional flag.

Supported structured units:
- item;
- g / kg;
- ml / l;
- tsp / tbsp;
- cup.

### Recipe invariants

1. Recipe ingredient quantities are either:
   - unspecified with no unit; or
   - positive numeric amount + explicit unit.
2. One canonical Ingredient can appear at most once per recipe.
3. Repeated-stage use should use a note such as "divided" rather than duplicate ingredient rows.
4. Ingredient rows are editorial source data, not parsed from prose.
5. Total time is derived, not duplicated state.
6. Recipe pages are leaf pages under a Recipe library.
7. Hero images require context-specific alt text in the recipe model.
8. Ingredient names are indexed as recipe search text through a deterministic callable.

The one-ingredient-per-recipe constraint is deliberately an MVP simplification that makes PR9 reconciliation deterministic.

## Ingredient identity

Ingredient matching is a domain risk.

MVP approach:
- canonical Ingredient entity;
- explicit recipe references;
- PantryItem and ShoppingItem have optional canonical Ingredient links;
- free-text items remain supported;
- exact normalized-name fallback preserves legacy/free-text compatibility;
- no fuzzy aliases or semantic matching.

Database invariants:
- at most one Pantry row per user + canonical Ingredient when linked;
- at most one non-deleted OPEN Shopping row per user + canonical Ingredient when linked.

Never claim semantic equivalence from fuzzy text without a clear deterministic rule.

## Recipe → pantry reconciliation

Implemented in PR9 as an owner-scoped derived read model. No readiness rows are persisted.

States:
- AVAILABLE;
- LOW;
- MISSING;
- UNKNOWN.

Deterministic rules:
1. Canonical Ingredient link is the primary match.
2. When no canonical Pantry link exists, exact normalized-name fallback is allowed.
3. Another user's Pantry state is never considered.
4. Expired Pantry state is UNKNOWN, not AVAILABLE or MISSING.
5. Approximate LOW is LOW.
6. Approximate FULL/HALF:
   - AVAILABLE when the recipe has no required numeric amount;
   - UNKNOWN when the recipe requires a numeric amount.
7. Precise quantities compare only inside safe unit families:
   - item ↔ item;
   - g ↔ kg;
   - ml ↔ l.
8. tsp / tbsp / cup and incompatible unit families degrade to UNKNOWN.
9. When precise stock is below recipe need, state is LOW.
10. UNKNOWN never becomes automatic Shopping demand.
11. Optional ingredients never become automatic Shopping demand.

## Recipe → shopping

Operation:
`add_needed_recipe_ingredients(recipe, user)`

Requirements:
1. determine MISSING / LOW / AVAILABLE / UNKNOWN;
2. auto-add only non-optional MISSING + LOW ingredients;
3. exclude AVAILABLE, UNKNOWN and optional ingredients;
4. ensure equivalent open Shopping demand idempotently;
5. preserve canonical Ingredient link where available;
6. backfill canonical Ingredient onto an equivalent free-text open Shopping row when safe;
7. perform writes atomically;
8. return created/reused counts for UI;
9. repeated submission must not increase quantity.

The recipe action is POST-only, CSRF-protected and returns the user to the same RecipePage.

## Meal plan

MealPlanEntry:
- household;
- date;
- meal slot (MVP: dinner);
- recipe optional;
- free-text meal fallback optional.

Invariant:
- at most one dinner entry per household/date in MVP.

## Today attention feed

Implemented in PR6 as a derived read model. No Today table is persisted.

Candidate signals:
- expired/use-soon pantry;
- due/overdue routines;
- unplanned dinner;
- shopping list readiness;
- optional useful recommendation.

PR6 priority is deterministic:
1. overdue routine;
2. expired pantry;
3. routine due today;
4. pantry use-soon;
5. pantry low-stock;
6. shopping summary.

The feed is capped at six visible signals; total attention count is retained separately.

Avoid scoring systems that look intelligent but are arbitrary.

## Search/privacy

Public:
- recipes;
- guides.

Private:
- only current household's shopping/pantry/routines/meal plan.

Never merge private indexed results without ownership filtering.

## Data deletion

When a user-owned object is deleted:
- use database cascade only where child data has no independent audit value;
- preserve routine completion history if product semantics require it, or explicitly document cascade;
- never orphan private state.

## Model review checklist

For each new model/field:
1. What user decision/action requires it?
2. Is it source data or derived state?
3. Can it be computed instead of stored?
4. What invariant protects it?
5. Who owns it?
6. What happens on retry?
7. What happens on deletion?
8. How does it migrate?
9. How is it displayed accessibly?
10. Does it create unnecessary maintenance for the user?
