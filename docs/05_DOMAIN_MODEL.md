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

Replace a simplistic `is_done` recurring model with a real recurrence model.

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

1. Completing a recurring routine records history.
2. Completion does not permanently mark the routine done.
3. Next due date is deterministic.
4. Skip is distinct from complete.
5. Postpone changes current due state without rewriting past history.
6. Routine history is user-owned/private.

## Recipes

Recipe is Wagtail editorial content.

Structured fields should support:
- title;
- intro;
- hero image;
- prep/cook/total time;
- servings;
- difficulty;
- tags;
- ingredients;
- instructions;
- optional tips/storage/substitutions;
- searchable text.

### Ingredient line

Prefer structured ingredient references plus display amount rather than opaque prose when pantry reconciliation is required.

Potential shape:
- Ingredient reference;
- numeric amount optional;
- unit optional;
- preparation note optional;
- optional flag.

Do not block editorial usefulness on perfect nutritional ontology.

## Ingredient identity

Ingredient matching is a domain risk.

MVP approach:
- canonical Ingredient entity;
- explicit recipe references;
- pantry and shopping items may optionally link to Ingredient;
- free-text items remain supported.

Never claim semantic equivalence from fuzzy text without a clear deterministic rule.

## Recipe → pantry reconciliation

States:
- AVAILABLE;
- LOW;
- MISSING;
- UNKNOWN.

Rules must be deterministic and testable.

If units cannot be safely compared:
- fall back to presence/unknown;
- do not invent quantity sufficiency.

## Recipe → shopping

Operation:
`add_missing_ingredients(recipe, household)`

Requirements:
1. determine missing/low ingredients;
2. exclude sufficient ingredients;
3. merge with equivalent open shopping items;
4. perform changes atomically;
5. return a result summary for UI;
6. be safe against duplicate submission.

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

Today is a read model, not necessarily a persisted table.

Candidate signals:
- expired/use-soon pantry;
- due/overdue routines;
- unplanned dinner;
- shopping list readiness;
- optional useful recommendation.

Priority must be deterministic.

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
