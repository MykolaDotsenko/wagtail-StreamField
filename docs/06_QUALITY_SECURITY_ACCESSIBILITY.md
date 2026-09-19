# Quality, Security & Accessibility

## Definition of Done

A feature is not done when it renders. It is done when:
- behavior matches acceptance criteria;
- domain invariants are tested;
- authorization is tested;
- accessible keyboard/mobile behavior is verified;
- error/empty states exist;
- migrations are safe;
- documentation is updated;
- CI is green.

## Test pyramid

### Domain/unit
Fast tests for:
- recurrence;
- pantry derived states;
- ingredient reconciliation;
- shopping deduplication/idempotency;
- selectors/read models.

### Django integration
Test:
- authentication;
- ownership boundaries;
- forms;
- POST workflows;
- redirects/messages;
- database writes;
- transaction behavior.

### Wagtail
Test:
- Page model validity;
- StreamField block validation;
- page rendering;
- search fields;
- editor-facing constraints where practical.

### Browser/E2E
Critical golden flows:
1. login;
2. Quick Add shopping;
3. complete/reopen shopping item;
4. pantry attention state;
5. routine completion → next due;
6. recipe → add missing ingredients;
7. meal plan;
8. keyboard navigation;
9. mobile viewport.

Keep E2E focused; do not duplicate every unit assertion.

## CI target

At minimum:
- supported Python version(s);
- dependency install;
- `python manage.py check`;
- `python manage.py makemigrations --check`;
- tests;
- lint/format;
- template/static checks where applicable;
- accessibility smoke checks when browser suite is added.

Before production-readiness:
- run CI with PostgreSQL.

## Coverage

Coverage is a signal, not the goal.

Target:
- high coverage of domain services and invariants;
- no requirement to test framework internals merely to reach a number.

A global threshold can be introduced once the suite is stable.

## Security rules

### Authentication
- use Django authentication primitives;
- secure cookie/settings configuration in production;
- no custom password storage.

### Authorization
- scope private objects to authenticated owner/household before mutation;
- tests must prove cross-user access fails.

### CSRF
- all state-changing browser forms use POST and CSRF protection;
- never mutate on GET.

### Input
- server-side validation is mandatory;
- treat client-side validation as UX only;
- constrain uploads/content types if uploads are introduced.

### Output
- rely on Django template auto-escaping;
- do not mark user-controlled HTML safe;
- rich text comes through controlled Wagtail mechanisms.

### Secrets
- environment variables;
- never committed;
- example env contains names, not real values.

### Deployment
Before deployment run:
- `python manage.py check --deploy`;
- TLS;
- secure cookies;
- allowed hosts;
- production secret key;
- correct static/media strategy.

## Privacy

Private household data:
- shopping;
- pantry;
- meal plans;
- routines/history.

Rules:
- no public exposure;
- no cross-account search leakage;
- no secrets/private values in logs;
- no analytics collection unless intentionally documented.

Do not make privacy claims that exceed implementation.

## Accessibility target

**WCAG 2.2 AA** as baseline.

Internal enhancements:
- aim for 44×44 CSS px primary touch targets;
- strong visible focus;
- reduced-motion support;
- accessible empty/error states;
- semantic landmarks and headings.

## Accessibility requirements

### Keyboard
- all features usable without mouse;
- logical focus order;
- no keyboard traps except correctly implemented modal focus containment;
- Escape closes dismissible modal/sheet.

### Focus
- `:focus-visible` is clearly visible;
- sticky header/bottom navigation must not hide focused elements.

### Pointer
- WCAG 2.2 target-size minimum;
- drag features always have non-drag alternative.

### Forms
- persistent labels;
- help text associated programmatically;
- errors associated with controls;
- first invalid field focus after failed submit;
- autocomplete attributes where useful.

### Status
Never rely on:
- color alone;
- icon alone.

Use visible text.

### Motion
Respect:
`prefers-reduced-motion: reduce`.

### Images
For Wagtail content:
- editors can provide context-specific alt text or mark decorative images appropriately;
- do not derive alt text blindly from filename.

## Wagtail authoring quality

Use:
- help_text;
- block descriptions;
- constrained heading choices;
- block previews where valuable;
- Wagtail's built-in accessibility checker in preview/editor workflow.

The editor should prevent common content-quality errors rather than merely documenting them.

## Performance quality

Budgets are directional until measured:
- minimal custom JS;
- no large animation framework without justified need;
- responsive image renditions;
- avoid N+1 queries;
- avoid unbounded lists;
- no unnecessary third-party scripts.

## Manual review matrix

Critical UI PRs:
- Chrome desktop;
- Firefox desktop;
- one WebKit/Safari path in automated suite when available;
- 360×800;
- 390×844;
- tablet;
- keyboard-only;
- reduced motion;
- 200% zoom;
- high contrast/forced colors where feasible.

## Pull-request evidence

UI PR should include:
- screenshots for key breakpoints;
- states tested;
- accessibility notes;
- test commands/results.

Domain PR should include:
- invariants covered;
- migration impact;
- retry/idempotency behavior where relevant.

## Security/accessibility reference

See [08_REFERENCE.md](./08_REFERENCE.md) for official documentation.
