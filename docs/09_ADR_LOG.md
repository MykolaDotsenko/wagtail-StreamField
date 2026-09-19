# Architecture Decision Record Log

This is a lightweight ADR log. Add a numbered entry for material decisions that are expensive to reverse, affect multiple modules, or intentionally reject a plausible alternative.

## ADR format

```
## ADR-XXX — Title

Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD

### Context
What problem or constraint exists?

### Decision
What are we doing?

### Alternatives considered
What realistic alternatives were rejected?

### Consequences
Positive and negative trade-offs.

### References
Official docs / handbook sections / PR.
```

---

## ADR-001 — Split editorial Wagtail content from transactional household state

Status: Accepted

### Context

DomoNest needs both flexible editorial content and private transactional workflows.

### Decision

Wagtail owns public/editorial content. Standard Django domain models/services own private household state.

### Alternatives considered

1. Put all data into Wagtail Page/snippet models.
2. Build all content as ordinary Django models/admin.
3. Separate frontend SPA with Django/Wagtail only as APIs.

### Consequences

Positive:
- framework responsibilities remain natural;
- stronger portfolio demonstration of both Django and Wagtail;
- household invariants remain easy to test;
- editorial teams retain Wagtail workflows.

Negative:
- cross-module actions require explicit service boundaries;
- search must combine public/private result domains carefully.

References:
- `04_ARCHITECTURE.md`
- Wagtail usage guide: https://docs.wagtail.org/en/7.4/topics/

---

## ADR-002 — Server-rendered baseline with progressive enhancement

Status: Accepted

### Context

The app needs fast, accessible household workflows but does not need a SPA to meet its product goals.

### Decision

Use Django/Wagtail server-rendered HTML as the baseline. Add small progressive enhancements only where they measurably improve interaction.

### Alternatives considered

1. React SPA.
2. Large client-side state layer.
3. JavaScript-only interactions.

### Consequences

Positive:
- lower complexity;
- strong accessibility baseline;
- less JavaScript;
- resilient forms/navigation;
- easier Django/Wagtail integration.

Negative:
- some advanced interactions may need carefully designed partial updates later.

---

## ADR-003 — Today is a derived read model, not a dashboard table

Status: Accepted

### Context

Today aggregates pantry, routine, shopping and meal state.

### Decision

Compute/select Today signals from domain state rather than persisting duplicate dashboard rows.

PR6 defines deterministic priority:
1. overdue routine;
2. expired pantry item;
3. routine due today;
4. pantry use-soon;
5. pantry low-stock;
6. active Shopping summary.

The primary feed is capped at six signals. Pantry emits only its strongest reason. Dinner remains a neutral placeholder until meal state exists.

### Consequences

Positive:
- no stale duplicated state;
- clear domain ownership;
- easier correctness.

Negative:
- query design must be intentional as data grows.

---

## ADR-004 — Recurring chores require history, not a boolean

Status: Accepted
Date: 2026-09-19

### Context

A recurring chore cannot be accurately represented by `is_done`.

### Decision

Model a recurring Routine separately from immutable RoutineEvent history.

The Routine keeps the cadence date and optional one-off postponed date separately. Postponement never rewrites cadence. Monthly routines retain an explicit day-of-month anchor so Jan 31 → Feb 28/29 → Mar 31 remains stable.

Terminal actions advance to the first recurrence strictly after today, preventing a long-overdue daily routine from creating a backlog of stale occurrences.

Browser actions include the scheduled occurrence as a stale-action token. The service re-checks it under a row lock before mutation.

### Consequences

Positive:
- correct recurrence;
- skip/postpone semantics;
- useful history;
- better domain signal.

Negative:
- more than one model/table;
- migration from current prototype required.

---

## ADR-005 — Pantry supports low-maintenance approximate quantities

Status: Accepted
Date: 2026-09-19

### Context

Exact inventory accounting creates too much user maintenance for many household items.

### Decision

Support both precise quantities and approximate states (full/half/low).

Approximate mode is the default Quick Add contract. It stores no fake numeric amount. Precise mode is opt-in and requires amount + unit. Expiry is optional, and missing expiry remains explicitly unknown.

Pantry attention is derived at read time. Pantry → Shopping uses an idempotent ensure command rather than manual Quick Add semantics, so repeated clicks do not increase shopping quantity.

### Consequences

Positive:
- lower interaction burden;
- more realistic household usage.

Negative:
- recipe reconciliation must safely handle unknown/approximate sufficiency;
- precise and approximate quantities require explicit branch logic in later reconciliation.

References:
- `docs/05_DOMAIN_MODEL.md`
- `docs/02_UX_RESEARCH_AND_FLOWS.md`


---

## ADR-006 — Shopping uses conservative normalized identity and database-enforced active uniqueness

Status: Accepted
Date: 2026-09-19

### Context

Quick Add must be faster than maintaining a manual note, but naive repeated submissions can create duplicate active shopping rows. Future recipe integration also needs a stable, deterministic way to find an already-open shopping demand.

### Decision

For the MVP, ShoppingItem identity is normalized with Unicode NFKC, whitespace collapse and case folding.

The database enforces at most one non-deleted `OPEN` item per user + normalized identity through a conditional unique constraint.

Equivalent additions merge quantity. We do not use fuzzy matching, embeddings or probabilistic entity resolution.

Removal is separate from completion. Remove first sets `deleted_at` so the immediate UI can offer a POST-based Undo. If Undo would collide with a newer equivalent open item, quantities are merged and the obsolete tombstone is deleted.

### Alternatives considered

1. Allow duplicates and leave cleanup to the user.
2. Case-insensitive matching only in view code.
3. Fuzzy/AI matching for item names.
4. Hard-delete immediately with no Undo.

### Consequences

Positive:
- deterministic behavior;
- retry-friendly Quick Add;
- database protection against conflicting active state;
- reversible common actions;
- future recipe integration has a stable command path.

Negative:
- "milk" and "2% milk" remain distinct until a canonical Ingredient model exists;
- unit-aware merging is deferred;
- soft deletion introduces tombstones that later retention work may clean up.

### References

- `docs/02_UX_RESEARCH_AND_FLOWS.md`
- `docs/05_DOMAIN_MODEL.md`
- `docs/04_ARCHITECTURE.md`


---

## ADR-007 — Keep recipe ingredients relational and machine-readable

Status: Accepted
Date: 2026-09-19

### Context

PR9 must compare recipe requirements with private Pantry state and create missing Shopping demand. Ingredient prose inside StreamField would require text parsing, fuzzy matching or editor conventions that are difficult to validate.

### Decision

Use a canonical `Ingredient` Wagtail snippet plus ordered `RecipeIngredient` inline rows attached to RecipePage with `ParentalKey`.

RecipeIngredient stores amount, unit, note and optional state. Recipe instructions remain a curated StreamField because cooking narrative benefits from editorial flexibility.

For MVP, a canonical Ingredient can occur only once per recipe. Multi-stage use is represented with a note such as "divided".

### Alternatives considered

1. Store all ingredients as free-form text inside StreamField.
2. Use a StructBlock ingredient list inside StreamField.
3. Allow duplicate canonical ingredients and aggregate later.
4. Build a full food/nutrition ontology before recipe delivery.

### Consequences

Positive:
- PR9 gets deterministic relational input;
- editor experience remains native Wagtail via InlinePanel;
- ingredient names become directly searchable;
- no natural-language parsing is required;
- unit uncertainty can be handled explicitly.

Negative:
- one-ingredient-per-recipe is a deliberate MVP constraint;
- additional unit conversion logic is deferred to reconciliation;
- canonical Ingredient maintenance becomes an editorial responsibility.

### References

- `docs/04_ARCHITECTURE.md`
- `docs/05_DOMAIN_MODEL.md`
- Wagtail Page inline models / ParentalKey documentation
- Wagtail snippets documentation
- Wagtail search indexing documentation


---

## ADR-008 — Reconciliation prefers uncertainty over guessed sufficiency

Status: Accepted
Date: 2026-09-19

### Context

Recipe readiness crosses public editorial recipe data and private household Pantry state. Pantry deliberately supports low-maintenance approximate quantities, while recipe units also include measures that Pantry cannot safely compare.

A visually impressive but probabilistic answer would violate the product's trust model.

### Decision

PR9 uses four deterministic states: AVAILABLE, LOW, MISSING and UNKNOWN.

Matching order:
1. canonical Ingredient link;
2. conservative exact normalized-name fallback for unlinked legacy/free-text Pantry rows;
3. no fuzzy or semantic match.

Safe numeric conversion is intentionally limited to item, mass (g/kg) and volume (ml/l). Unsupported or incompatible units become UNKNOWN.

Expired Pantry entries are UNKNOWN. Approximate FULL/HALF with an explicit recipe amount are UNKNOWN. Approximate LOW is LOW.

Only non-optional MISSING + LOW ingredients become automatic Shopping demand. UNKNOWN is never auto-added.

Shopping writes reuse the existing idempotent ensure command, now canonical-Ingredient aware. Schema constraints enforce one linked Pantry row per user/ingredient and one active linked Shopping demand per user/ingredient.

### Alternatives considered

1. Treat approximate FULL as sufficient for any recipe quantity.
2. Convert tsp/tbsp/cup to volume unconditionally.
3. Fuzzy-match free-text ingredient names.
4. Auto-add UNKNOWN items "just in case".
5. Persist readiness rows.

### Consequences

Positive:
- explainable behavior;
- no false precision;
- strong privacy boundary;
- safe retry/double-submit behavior;
- same readiness contract can feed PR10 Meal planning.

Negative:
- some users must manually check uncertain stock;
- ingredient aliasing is deferred;
- richer culinary unit conversions are deferred.

### References

- `docs/02_UX_RESEARCH_AND_FLOWS.md`
- `docs/05_DOMAIN_MODEL.md`
- `docs/04_ARCHITECTURE.md`


---

## ADR-009 — Meal plans store durable intent while readiness stays derived

Status: Accepted
Date: 2026-09-19

### Context

Dinner planning combines private household intent with public editorial recipes and volatile Pantry state. Persisting a recipe-only foreign key would make the private plan fragile if editorial content is later removed. Persisting readiness/missing counts would create duplicated state that becomes stale as Pantry changes.

### Decision

MealPlanEntry stores one durable dinner-name snapshot for every plan plus an optional RecipePage foreign key using SET_NULL.

The database enforces one dinner per user + date. Setting dinner is an upsert.

Recipe readiness is never persisted. The week and Today read models call the PR9 reconciliation contract at read time. Week readiness uses the planned dinner date so expiry is evaluated against when the meal will actually be cooked.

The MVP is dinner-only and therefore does not add a meal-slot field.

### Alternatives considered

1. Store only RecipePage FK for recipe dinners.
2. Persist readiness/missing counts on MealPlanEntry.
3. Add breakfast/lunch/snack slots immediately.
4. Duplicate full recipe data into private state.
5. Build a recommendation engine before basic planning.

### Consequences

Positive:
- private plans survive editorial recipe deletion;
- no stale readiness columns;
- one-dinner invariant is simple and database-enforced;
- same PR9 readiness semantics are reused consistently;
- custom meals remain low-friction.

Negative:
- recipe title snapshot can intentionally differ from a later edited recipe title until the dinner is re-saved;
- read-time readiness has query cost that PR12 should measure and optimize;
- only dinner is represented in MVP.

### References

- `docs/02_UX_RESEARCH_AND_FLOWS.md`
- `docs/04_ARCHITECTURE.md`
- `docs/05_DOMAIN_MODEL.md`
- ADR-003
- ADR-008


---

## ADR-010 — Keep public and private search execution separate

Status: Accepted
Date: 2026-09-19

### Context

Discover must retrieve both published editorial knowledge and user-owned household state. A single combined index would be convenient but would materially increase the blast radius of an authorization/indexing mistake.

### Decision

Use two explicit search paths.

Public Recipes and Guides use Wagtail indexed search on live Page querysets.

Private Shopping, Pantry, Routines and MealPlanEntry search uses bounded Django QuerySets that begin with `user=request.user`. The private branch is not executed for anonymous users.

Results are grouped and labelled separately in the UI.

### Alternatives considered

1. Put private household state into the same Wagtail/global search index as public content.
2. Search all household rows and filter ownership after retrieval.
3. Add Elasticsearch/OpenSearch before product scale requires it.
4. Hide the private/public distinction in one flat result list.

### Consequences

Positive:
- authorization is visible in code structure;
- anonymous requests cannot retrieve private rows;
- easier security testing;
- public search can evolve independently from household search;
- UI makes source/privacy boundaries understandable.

Negative:
- ranking is per-domain rather than one global relevance score;
- private search is simpler substring matching at MVP scale;
- a future dedicated private index would require its own tenant/ownership design.

### References

- `docs/04_ARCHITECTURE.md`
- `docs/06_QUALITY_SECURITY_ACCESSIBILITY.md`
- Wagtail 7.4 search/indexing documentation
