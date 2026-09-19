# Implementation Roadmap

The roadmap is ordered to maximize product coherence and reduce rework.

Each PR should remain reviewable. Avoid "mega PRs" that mix domain redesign, visual redesign and unrelated infrastructure.

## PR 0 — Documentation and guardrails

Scope:
- this handbook;
- PR template;
- README positioning;
- baseline CI plan.

Exit criteria:
- docs are linked from repository root;
- every future PR references handbook sections.

## PR 1 — Foundation cleanup

Goal:
Establish clean project boundaries before expanding features.

Scope:
- normalize app structure;
- remove tutorial comments/dead styles;
- configure DomoNest naming/settings;
- environment configuration;
- lint/format tooling;
- initial CI;
- baseline tests;
- decide Python support;
- confirm Django 5.2 + Wagtail 7.4 LTS compatibility.

No new product feature beyond what is required to stabilize foundation.

## PR 2 — Design system + app shell

Status: implemented on `pr/02-design-system-shell`; final acceptance depends on CI and visual review.

Goal:
Build stable UI primitives once.

Scope:
- design tokens;
- typography;
- responsive layout;
- desktop/mobile navigation;
- buttons;
- form fields;
- item rows;
- status badges;
- empty states;
- snackbar;
- accessible focus/reduced motion;
- login shell.

Acceptance:
- works at 360/390/768/1024/1280 widths;
- keyboard navigable;
- no model-specific business behavior yet.

## PR 3 — Shopping vertical slice

Status: implemented on `pr/03-shopping-vertical-slice`; final acceptance depends on CI.

Goal:
Deliver the first complete high-frequency workflow.

Scope:
- final ShoppingItem model;
- Quick Add;
- category grouping;
- completion/reopen;
- delete + Undo strategy;
- recent/frequent items if justified by existing history;
- shopping mode;
- ownership tests.

Acceptance:
- add item with name only;
- one-tap complete;
- no duplicate submit corruption;
- cross-user access denied;
- mobile shopping experience excellent.

## PR 4 — Pantry vertical slice

Status: implemented on `pr/04-pantry-vertical-slice`; final acceptance depends on CI.

Goal:
Surface low-stock/use-soon value without inventory burden.

Scope:
- precise vs approximate quantity;
- expiry;
- low-stock derived state;
- attention grouping;
- add-to-shopping action;
- forms/validation.

Acceptance:
- incomplete pantry data remains useful;
- unknown expiry is not treated as safe;
- no negative quantities;
- low stock can move to shopping with minimal work.

## PR 5 — Recurring Home Rhythm

Goal:
Replace CRUD chores with a correct recurrence model.

Scope:
- Routine;
- occurrence/completion history;
- daily/weekly/monthly/one-time recurrence;
- done/skip/postpone;
- deterministic next due;
- Today integration.

Acceptance:
- complete records history;
- next due generated correctly;
- skip distinct from complete;
- recurrence unit tests cover boundary dates.

## PR 6 — Today dashboard

Goal:
Create the product's main decision surface.

Scope:
- attention selector/read model;
- pantry signals;
- routine signals;
- shopping state;
- dinner state placeholder;
- compact cards;
- mobile priority ordering.

Acceptance:
- user can understand next actions in <5 seconds;
- no vanity KPI grid dominates;
- Today does not persist duplicated derived state.

## PR 7 — Wagtail content architecture

Goal:
Turn the CMS into a deliberate authoring system.

Scope:
- shared blocks module;
- structured block groups;
- editor help text;
- previews;
- snippets/taxonomy only where appropriate;
- guide content type;
- Wagtail accessibility authoring checks;
- migrate/reframe legacy blog.

Acceptance:
- editor can create useful content without free-form layout breakage;
- block names/descriptions are product-oriented;
- page output accessible.

## PR 8 — Recipe domain + RecipePage

Goal:
Create structured recipe content ready for household actions.

Scope:
- RecipePage;
- canonical Ingredient;
- ingredient lines;
- instructions;
- time/servings/difficulty;
- recipe cards/detail;
- search indexing.

Acceptance:
- ingredient data is structurally queryable;
- editorial experience remains simple;
- responsive recipe detail and cook-friendly reading mode.

## PR 9 — Recipe → Pantry → Shopping

Goal:
Deliver the signature cross-module workflow.

Scope:
- reconciliation service;
- AVAILABLE/LOW/MISSING/UNKNOWN;
- add missing ingredients;
- deduplication/idempotency;
- atomic transaction;
- inline confirmation.

Acceptance:
- double submit does not duplicate items;
- unsupported unit comparison degrades safely;
- user remains on recipe;
- cross-user pantry data never leaks.

## PR 10 — Meal planning

Goal:
Plan dinners and connect them to recipe readiness.

Scope:
- MealPlanEntry;
- one dinner/date constraint;
- mobile weekly list;
- desktop week view;
- recipe selection;
- readiness metadata.

Acceptance:
- one dinner/date invariant;
- meal can be changed/removed;
- selection communicates missing ingredient count accurately.

## PR 11 — Global search / Discover polish

Goal:
Make public knowledge and private home state easy to retrieve.

Scope:
- grouped search results;
- ownership-safe private search;
- recipe/guide filters;
- Discover landing.

Acceptance:
- private results are always owner-scoped;
- public/private result groups visually distinct.

## PR 12 — Production hardening

Scope:
- PostgreSQL CI;
- query optimization;
- health endpoint;
- `check --deploy`;
- static/media production strategy;
- browser E2E;
- axe checks;
- security settings;
- README/screenshots/demo instructions;
- dependency audit.

Acceptance:
- CI fully green;
- no migration drift;
- critical E2E golden journey passes;
- WCAG 2.2 AA issues from automated/manual review resolved or explicitly documented.

## PR sizing rules

A PR should usually change one coherent capability.

Split when:
- more than one unrelated domain invariant changes;
- UI system and domain redesign can be independently reviewed;
- migration risk is large;
- reviewer cannot reasonably explain the change after one pass.

Do not split so aggressively that an intermediate PR leaves broken user behavior.

## Required PR sections

Every PR states:
- User problem.
- Scope.
- Non-goals.
- Handbook references.
- Acceptance criteria.
- Domain invariants.
- Accessibility impact.
- Security/privacy impact.
- Migration impact.
- Tests/evidence.
- Screenshots for UI changes.
- Follow-ups.

## Stop conditions

Do not continue implementation when:
- a core domain invariant is unclear;
- a framework API is being guessed rather than checked in official docs;
- UI adds complexity without user value;
- cross-user authorization is untested;
- migration behavior is uncertain;
- a PR is becoming a multi-feature rewrite.

Resolve the uncertainty or document an ADR first.
