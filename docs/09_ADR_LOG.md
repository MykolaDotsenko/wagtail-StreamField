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
