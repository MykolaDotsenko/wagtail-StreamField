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
- https://docs.wagtail.org/en/7.4/topics/pages.html
- https://docs.wagtail.org/en/7.4/topics/snippets/
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
- https://docs.wagtail.org/en/7.4/topics/streamfield.html

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
- https://docs.wagtail.org/en/7.4/advanced_topics/accessibility_considerations.html

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
Status: Validated in PR4
Confidence: High

### Question

Should pantry inventory require exact numeric quantities?

### Evidence

The core product goal is reducing household mental load. Requiring exact stock accounting for every item increases maintenance and conflicts with that goal.

### Finding

Support both precise and approximate quantities. The reconciliation layer must explicitly represent uncertainty instead of pretending approximate stock is exact.

### Product/engineering impact

PR4 implements both modes. Approximate/Full is the name-only default; precise tracking is opt-in. Unknown expiry remains explicit. Recipe reconciliation must preserve uncertainty rather than invent sufficiency from approximate stock.

---

## 2026-09-19 — Should navigation expose planned-but-unimplemented modules?

Area: UX
Status: Validated
Confidence: High

### Question

Should PR2 render the complete future navigation structure even though Plan, Shopping, Pantry, Routines and Quick Add do not exist yet?

### Evidence

The product UX objective is to minimize navigation ambiguity and preserve trust. A visible navigation item implies a working destination. Placeholder routes or dead links would increase noise without helping a current user complete a task.

### Finding

Navigation should reveal capabilities progressively. PR2 exposes only real destinations: Today, Discover and authentication/content utilities.

### Product/engineering impact

Future vertical slices add their navigation destinations in the same PR that makes the route useful. The design system already reserves the responsive shell patterns, so this does not require a visual redesign.

### Follow-up

Re-evaluate the mobile five-slot navigation once Plan, Home modules and Quick Add all exist.

---

## 2026-09-19 — How much intelligence should Quick Add use?

Area: UX / Domain
Status: Validated for PR3
Confidence: High

### Question

Should Quick Add use fuzzy matching or AI to prevent duplicates and categorize shopping items?

### Evidence

The MVP requirement is fast capture with predictable behavior. Fuzzy matching can silently merge distinct products, while a small deterministic category dictionary can reduce common input effort without claiming semantic understanding.

### Finding

Use conservative normalized identity for duplicate detection and a transparent deterministic category inference for common exact item names. Unknown items fall back to Other. Users can override category in progressive details.

### Product/engineering impact

- Unicode NFKC + whitespace collapse + casefold for identity.
- Conditional database uniqueness for active items.
- No fuzzy matching.
- No AI.
- Category suggestions remain editable.

---

## 2026-09-19 — How should Shopping removal support Undo without client state?

Area: UX / Architecture
Status: Validated for PR3
Confidence: High

### Question

Can safe Undo be delivered without adding JavaScript state management?

### Evidence

Django redirects and owner-scoped server state are sufficient: mark the row deleted, redirect with its ID, re-resolve through the authenticated user, and submit a CSRF-protected POST to restore.

### Finding

Use server-side soft delete plus a POST restore action. A query-string ID is a presentation hint, not authorization.

### Product/engineering impact

The view never trusts the ID by itself. Both display and restore operations scope by authenticated user. A restore collision merges into the newer equivalent open item.

---

## 2026-09-19 — Should Pantry → Shopping increment quantity on repeated clicks?

Area: Domain / UX
Status: Validated
Confidence: High

### Question

Should repeated "Add to Shopping" actions behave like repeated manual Quick Add?

### Evidence

Manual Quick Add represents explicit repeated demand and can reasonably increase quantity. Pantry low-stock action represents one unresolved replenishment intent; repeated submission can happen through double-click, refresh or retry.

### Finding

Pantry → Shopping must be idempotent. It ensures one equivalent active ShoppingItem exists without increasing quantity when it already exists.

### Product/engineering impact

PR4 introduces `ensure_shopping_item()` as a stable idempotent command boundary. PR9 Recipe → Shopping should reuse this semantic instead of manual Quick Add.

---

## 2026-09-19 — How should recurring routines preserve cadence?

Area: Domain / UX
Status: Validated in PR5
Confidence: High

### Question

Should completing or postponing a routine reschedule from the action date, or preserve its intended cadence?

### Evidence

Rescheduling from every action causes drift: a monthly 31st routine postponed to the 2nd would silently become a 2nd-of-month routine. Repeated stale submissions can also accidentally process a newly advanced occurrence if the current schedule is not revalidated.

### Finding

Store the cadence date separately from a one-off postponed date. Monthly recurrence carries an explicit anchor day. Terminal actions advance from cadence, but overdue backlog collapses to the first future recurrence. Browser mutations include an expected scheduled occurrence and are rejected when stale.

### Product/engineering impact

PR5 implements Routine + RoutineEvent, stale-action checks under transaction locks, and calendar-safe month arithmetic.

---

## 2026-09-19 — What priority should Today use?

Area: Product / UX
Status: Validated in PR6
Confidence: High

### Finding

Use deterministic, explainable urgency rather than a synthetic score:
overdue routine → expired pantry → routine due today → use soon → low stock → shopping summary.

Cap the visible action feed at six. One Pantry item emits only its strongest reason.

### Product/engineering impact

`today_snapshot()` composes existing owner-scoped selectors. No Today rows or scores are persisted.

---

## 2026-09-19 — How should the tutorial blog evolve into the guide system?

Area: Architecture / Wagtail
Status: Validated in PR7
Confidence: High

### Question

Should the existing BlogPage hierarchy be renamed/rebuilt immediately, or incrementally reframed into the DomoNest guide authoring system?

### Evidence

The existing page types already contain live-content-compatible StreamField data and page-tree relationships. Wagtail supports reusable structured blocks, block groups, editor descriptions and previews. Wagtail 7.4 also provides ImageBlock as the accessibility-focused image block with contextual alt/decorative authoring support.

Official references:
- https://docs.wagtail.org/en/stable-7.4.x/reference/streamfield/blocks.html
- https://docs.wagtail.org/en/stable-7.4.x/topics/snippets/

### Finding

Reframe the existing BlogIndexPage / BlogPage schema in place for PR7 instead of creating a risky duplicate content tree or destructive rename migration. Editor-facing names become Guide library / Home guide. A shared `content.blocks` module provides the reusable authoring vocabulary.

Keep the legacy ImageChooserBlock only so existing StreamField values remain compatible; new guide authors receive a separate accessibility-first ImageBlock.

### Product/engineering impact

PR8 RecipePage can reuse shared content blocks without coupling recipe structure to the legacy blog internals. A future internal app/model rename is optional cleanup, not a product prerequisite.

---

## 2026-09-19 — Where should recipe ingredient structure live?

Area: Architecture / Domain / Wagtail
Status: Validated in PR8
Confidence: High

### Question

Should recipe ingredients be a StreamField block, free text, or relational inline rows?

### Evidence

Wagtail inline models use `ParentalKey` and optionally `Orderable` for repeated page-owned structured data that participates in page revisions. Wagtail snippets are intended for reusable non-page entities. Wagtail search can index callables/related values.

Official references:
- https://docs.wagtail.org/en/stable-7.4.x/topics/pages.html
- https://docs.wagtail.org/en/stable-7.4.x/topics/snippets/
- https://docs.wagtail.org/en/stable/topics/search/indexing.html

### Finding

Use a reusable Ingredient snippet plus ordered relational RecipeIngredient rows. Keep narrative cooking instructions in a constrained StreamField.

For MVP, normalized ingredient identity uses Unicode NFKC + whitespace collapse + casefold and one canonical Ingredient is allowed once per recipe. No fuzzy aliases or food ontology are introduced.

### Product/engineering impact

PR9 can reconcile by canonical Ingredient identity and degrade unsupported unit comparisons to UNKNOWN instead of parsing prose or guessing semantic equivalence.

---

## Open research backlog

These questions should be answered only when their PR approaches:

1. Should progressive interactions use minimal vanilla JS or HTMX?
2. [Resolved PR8] Canonical Ingredient uses NFKC + whitespace collapse + casefold; no fuzzy ontology.
3. [Resolved PR8] Ingredient snippet + ordered InlinePanel rows; narrative remains StreamField.
4. [Resolved PR5] Use a Routine cadence row + immutable RoutineEvent history; keep postponed_until separate from due_on and retain a monthly anchor day.
5. Should shopping purchase history be retained indefinitely or summarized?
6. [Resolved PR6 baseline] Re-evaluate Today priority only after real meal-plan signals exist.
7. What PostgreSQL/search strategy is justified at portfolio/demo scale?
8. What performance budget should become CI-enforced after baseline measurements exist?
