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

### Context

A recurring chore cannot be accurately represented by `is_done`.

### Decision

Model a recurring Routine separately from occurrence/completion history.

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

### Context

Exact inventory accounting creates too much user maintenance for many household items.

### Decision

Support both precise quantities and approximate states (full/half/low).

### Consequences

Positive:
- lower interaction burden;
- more realistic household usage.

Negative:
- recipe reconciliation must safely handle unknown/approximate sufficiency.
