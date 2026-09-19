# DomoNest Engineering & Product Handbook

This directory is the source of truth for DomoNest product, UX, design, architecture, domain, quality and delivery decisions.

## Why this exists

DomoNest is intentionally designed as a production-minded Django + Wagtail case study, not a tutorial CRUD application. Every pull request should preserve the same product model, interaction model and engineering standards.

The documentation is split by responsibility to avoid duplicated or conflicting rules.

## Source-of-truth map

| Area | Authoritative document | Questions it answers |
| --- | --- | --- |
| Product | [01_PRODUCT_SPEC.md](./01_PRODUCT_SPEC.md) | Why are we building this? What creates user/business value? |
| UX / user journeys | [02_UX_RESEARCH_AND_FLOWS.md](./02_UX_RESEARCH_AND_FLOWS.md) | Who uses it? What are the jobs, flows and friction rules? |
| UI / visual design | [03_UI_DESIGN_SYSTEM.md](./03_UI_DESIGN_SYSTEM.md) | How should it look and behave? |
| Architecture | [04_ARCHITECTURE.md](./04_ARCHITECTURE.md) | Where should logic live? How do Django and Wagtail interact? |
| Domain model | [05_DOMAIN_MODEL.md](./05_DOMAIN_MODEL.md) | What entities, invariants and state transitions exist? |
| Quality / security / accessibility | [06_QUALITY_SECURITY_ACCESSIBILITY.md](./06_QUALITY_SECURITY_ACCESSIBILITY.md) | What must be tested and protected before merge? |
| Delivery | [07_IMPLEMENTATION_ROADMAP.md](./07_IMPLEMENTATION_ROADMAP.md) | In what PR order do we build the product? |
| Official references | [08_REFERENCE.md](./08_REFERENCE.md) | Which official documentation governs implementation choices? |
| Decisions | [09_ADR_LOG.md](./09_ADR_LOG.md) | Which architectural/product decisions are locked and why? |
| Deployment | [11_DEPLOYMENT_RUNBOOK.md](./11_DEPLOYMENT_RUNBOOK.md) | How is the production baseline configured, verified and operated? |

## Mandatory workflow for every PR

Before implementation:

1. Read the relevant sections of this handbook.
2. Confirm the PR maps to one user problem and one bounded technical change.
3. Check the official references for framework APIs touched by the PR.
4. Write or update acceptance criteria before implementation.
5. Identify domain invariants and failure states.
6. Identify accessibility requirements.
7. Identify migration/backward-compatibility impact.

Before merge:

1. Verify all acceptance criteria.
2. Run the quality gates defined in `06_QUALITY_SECURITY_ACCESSIBILITY.md`.
3. Confirm the UI matches `03_UI_DESIGN_SYSTEM.md`.
4. Confirm the behavior matches `02_UX_RESEARCH_AND_FLOWS.md`.
5. Confirm business rules do not leak into templates/views.
6. Update docs if the PR intentionally changes a documented decision.
7. Add an ADR entry for material architectural/product decisions.
8. Complete the pull-request template without "N/A" unless genuinely not applicable.

## Decision hierarchy

When documents disagree, use this order:

1. Security, privacy, data integrity.
2. Domain invariants.
3. Accessibility.
4. User value / user task completion.
5. Simplicity and maintainability.
6. Visual polish.
7. Novelty / wow factor.

A visually impressive change must never override a higher-ranked concern.

## Product principle

> Do not make the user manage the organizer. Make the organizer remove work from the user.

## Engineering principle

> Prefer the smallest design that fully preserves the domain invariant, user workflow, accessibility and observability requirements.

## Documentation policy

- Documents describe current intended behavior, not historical implementation.
- Historical rationale belongs in the ADR log.
- Do not copy requirements between files; link to the authoritative section.
- If implementation and documentation diverge, the PR must either fix the implementation or explicitly update the documented decision.
- Every non-trivial feature PR should reference the relevant document sections in its description.
