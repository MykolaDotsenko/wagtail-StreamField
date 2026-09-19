# DomoNest

**DomoNest** is a production-minded Django + Wagtail portfolio project exploring how a household operating system can reduce mental load across shopping, pantry awareness, meal planning, recurring home routines and actionable editorial content.

The project is being rebuilt from a small Wagtail StreamField exercise into a cohesive product and engineering case study.

## Product idea

> Less to remember. More room to live.

DomoNest connects workflows instead of shipping isolated CRUD modules:

```
Recipe → Pantry check → Missing ingredients → Shopping
Guide → Home routine → Completion → Next recurrence
Today → Next useful action
```

## Stack direction

- Python 3.12–3.14 (CI matrix)\n- Django 5.2.17 LTS line\n- Wagtail 7.4.3 LTS
- Server-rendered HTML with progressive enhancement
- PostgreSQL target for production-minded CI/deployment
- WCAG 2.2 AA accessibility baseline

## Engineering handbook

The project is documentation-led. Start here:

**[docs/00_INDEX.md](./docs/00_INDEX.md)**

Key documents:
- [Product specification](./docs/01_PRODUCT_SPEC.md)
- [UX research and user flows](./docs/02_UX_RESEARCH_AND_FLOWS.md)
- [UI design system](./docs/03_UI_DESIGN_SYSTEM.md)
- [Architecture](./docs/04_ARCHITECTURE.md)
- [Domain model](./docs/05_DOMAIN_MODEL.md)
- [Quality, security and accessibility](./docs/06_QUALITY_SECURITY_ACCESSIBILITY.md)
- [PR implementation roadmap](./docs/07_IMPLEMENTATION_ROADMAP.md)
- [Official references](./docs/08_REFERENCE.md)
- [Architecture decision log](./docs/09_ADR_LOG.md)
- [Research log](./docs/10_RESEARCH_LOG.md)

## Contribution workflow

See [CONTRIBUTING.md](./CONTRIBUTING.md).

Every non-trivial PR should:
1. reference the relevant handbook sections;
2. state its user problem and acceptance criteria;
3. identify domain/security/accessibility impact;
4. verify version-matched official framework documentation;
5. update the handbook or ADR log when a decision changes.

The repository includes a pull-request template to enforce this workflow.

## Current delivery plan

Implementation proceeds as bounded vertical slices:

1. foundation cleanup;
2. design system and app shell;
3. shopping;
4. pantry;
5. recurring Home Rhythm;
6. Today dashboard;
7. Wagtail content architecture;
8. RecipePage;
9. Recipe → Pantry → Shopping;
10. meal planning;
11. search / Discover;
12. production hardening.

See [docs/07_IMPLEMENTATION_ROADMAP.md](./docs/07_IMPLEMENTATION_ROADMAP.md) for acceptance criteria and sequencing.
