# Research Log

This file captures evidence, unresolved questions and conclusions that may influence future PRs.

It is **not** a second specification. When research changes an intended product/technical rule, update the authoritative handbook document and, when material, add an ADR.

## Research entry format

```
## YYYY-MM-DD — Question

Area: Product | UX | UI | Architecture | Domain | Accessibility | Security | Performance
Status: Open | Validated | Rejected | Needs experiment
Confidence: Low | Medium | High

### Question
What are we trying to learn?

### Evidence
- Official source / observed code / usability evidence.

### Finding
What did we learn?

### Product/engineering impact
What should change, if anything?

### Follow-up
What remains unresolved?
```

---

## 2026-09-19 — Should Wagtail own household transactional state?

Area: Architecture
Status: Rejected
Confidence: High

### Question

Should shopping, pantry, routines and meal planning be represented primarily as Wagtail Pages/Snippets to maximize the Wagtail showcase?

### Evidence

Wagtail Pages are designed around page/content publishing, and Snippets are reusable Django models managed through Wagtail. The household workflows require user ownership, transactional invariants, recurrence and idempotent cross-model writes.

Official references:
- https://docs.wagtail.org/en/7.0/topics/pages.html
- https://docs.wagtail.org/en/7.0/topics/snippets/
- https://docs.djangoproject.com/en/5.2/topics/db/transactions/

### Finding

Using Wagtail as the primary store for transactional household state would optimize for demo novelty rather than correct responsibility boundaries.

### Product/engineering impact

Wagtail owns editorial content; standard Django models/services own private household workflows.

See ADR-001.

---

## 2026-09-19 — How should StreamField be used?

Area: Architecture
Status: Validated
Confidence: High

### Question

Should DomoNest use one large unrestricted StreamField as a page builder?

### Evidence

Wagtail StreamField supports structured block types and custom block behavior. Constrained structured blocks allow editor flexibility without giving up predictable rendering or validation.

Official reference:
- https://docs.wagtail.org/en/7.0/topics/streamfield.html

### Finding

Use a curated block library with product-specific blocks and clear editor descriptions. Avoid unrestricted layout freedom.

### Product/engineering impact

Create shared editorial blocks for ingredients, steps, tips, warnings, checklists and action CTAs. Use previews/help text where they improve author confidence.

---

## 2026-09-19 — Accessibility target for interactions

Area: Accessibility
Status: Validated
Confidence: High

### Question

What baseline should govern keyboard, dragging and touch targets?

### Evidence

WCAG 2.2 defines:
- keyboard requirements;
- visible/non-obscured focus;
- a non-drag alternative for dragging interactions;
- Target Size (Minimum) at AA.

Official reference:
- https://www.w3.org/TR/WCAG22/

Wagtail 7 also includes an Axe-based accessibility checker in supported preview/editing surfaces:
- https://docs.wagtail.org/en/7.0/advanced_topics/accessibility_considerations.html

### Finding

Target WCAG 2.2 AA. Internally aim for 44×44 CSS px on primary mobile controls even when AA permits smaller targets under its rules.

### Product/engineering impact

Accessibility requirements live in `06_QUALITY_SECURITY_ACCESSIBILITY.md` and are mandatory PR review criteria.

---

## 2026-09-19 — Should DomoNest be a SPA?

Area: Architecture
Status: Rejected for MVP
Confidence: High

### Question

Would React/SPA architecture make the product feel more modern?

### Evidence

The current workflows are form/task oriented and are naturally supported by Django's request/form/template stack. A SPA would add client state, API and synchronization complexity without a demonstrated product requirement.

Official references:
- https://docs.djangoproject.com/en/5.2/topics/forms/
- https://docs.djangoproject.com/en/5.2/topics/class-based-views/

### Finding

"Modern" should come from interaction quality and progressive enhancement, not framework count.

### Product/engineering impact

Server-rendered HTML is the baseline. Any HTMX or client-state dependency requires a specific UX justification and ADR.

---

## 2026-09-19 — Pantry precision versus maintenance cost

Area: UX
Status: Needs implementation validation
Confidence: Medium

### Question

Should pantry inventory require exact numeric quantities?

### Evidence

The core product goal is reducing household mental load. Requiring exact stock accounting for every item increases maintenance and conflicts with that goal.

### Finding

Support both precise and approximate quantities. The reconciliation layer must explicitly represent uncertainty instead of pretending approximate stock is exact.

### Product/engineering impact

Domain model plans `PRECISE` and `APPROXIMATE` modes. Usability should be re-evaluated after the pantry vertical slice.

---

## Open research backlog

These questions should be answered only when their PR approaches:

1. Should progressive interactions use minimal vanilla JS or HTMX?
2. What normalized ingredient identity is sufficient for the MVP without creating an ontology project?
3. What is the clearest non-technical Wagtail authoring workflow for RecipePage ingredients?
4. Which recurrence representation keeps daily/weekly/monthly routines simple while remaining migration-friendly?
5. Should shopping purchase history be retained indefinitely or summarized?
6. What exact Today signal priority performs best once all modules exist?
7. What PostgreSQL/search strategy is justified at portfolio/demo scale?
8. What performance budget should become CI-enforced after baseline measurements exist?
