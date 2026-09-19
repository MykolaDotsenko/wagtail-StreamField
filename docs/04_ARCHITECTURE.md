# Architecture

## Architecture objective

DomoNest should demonstrate production-minded Django + Wagtail architecture with clear responsibility boundaries and minimal accidental complexity.

## High-level split

### Wagtail owns editorial content

Examples:
- landing pages;
- recipes;
- cleaning/home guides;
- flexible content sections;
- reusable editorial taxonomy/snippets;
- preview/draft/publish workflow;
- editorial search.

### Django owns private household state and workflows

Examples:
- shopping;
- pantry;
- meal plan;
- routines/completions;
- user-specific actions;
- domain services;
- authentication/authorization.

This boundary is intentional.

## Why this split

Wagtail is strongest when editors need flexible structured content and publishing workflows. Django models/services are stronger for transactional user-owned state, invariants and lifecycle logic.

Do not force transactional data into Page/StreamField models simply to demonstrate Wagtail.

Do not recreate CMS behavior in custom Django models where Wagtail already solves it well.

## Application boundaries

Target apps:

```
home/          public landing pages / StreamField
content/       shared Wagtail blocks and editorial primitives
recipes/       RecipePage and recipe-specific editorial model
household/     shopping, pantry, routines, meal planning
search/        cross-surface search orchestration
accounts/      add only when account-specific behavior justifies separation
```

Existing legacy `blog/` should be migrated or reframed, not allowed to remain a parallel conflicting content model indefinitely.

## Layering

### Models
Persist state and enforce simple local invariants.

### Domain services
Contain multi-model business operations, for example:
- compare recipe ingredients with pantry;
- add missing ingredients idempotently to shopping;
- complete recurring routine and schedule next occurrence.

### Queries/selectors
Encapsulate non-trivial read models:
- Today attention feed;
- meal readiness;
- low-stock/use-soon sets.

### Views
Orchestrate request/response:
- permission check;
- form/input validation;
- call service/query;
- render/redirect.

Views must not become business-logic containers.

### Templates
Render already-understood state.
Templates must not implement domain rules.

## Service transaction rule

Any multi-write operation that must succeed atomically uses `transaction.atomic()`.

Examples:
- routine completion + next occurrence;
- adding several missing ingredients;
- updating shopping/pantry state together if future behavior requires it.

## Ownership and authorization

Every private household object is scoped to its owner/household before mutation.

Never:
1. fetch globally by primary key;
2. mutate;
3. then check ownership.

Use scoped queries first.

## Household abstraction

MVP may begin with direct user ownership if it keeps delivery simple.

Before family sharing is introduced, add an ADR deciding whether to migrate ownership to a `Household` aggregate.

Do not prematurely introduce complex membership/role models.

## Cross-module integration

Cross-module behavior must use stable service interfaces rather than importing view logic.

Example:

```
recipes → household.services.add_missing_recipe_ingredients(...)
```

not:

```
recipes view → manually creates ShoppingItem in a loop
```

## Idempotency

Actions that users may submit twice due to retries/refresh should be idempotent where reasonable.

Critical case:
- recipe missing ingredients → shopping.

Equivalent open shopping items should be merged/deduplicated according to normalized identity rules.

## Progressive enhancement

Baseline:
- server-rendered Django/Wagtail HTML;
- forms work without JavaScript where practical.

Enhancement:
- small JS or HTMX may improve Quick Add, drawers, inline toggles and partial updates.

No framework is added solely for novelty.

Any HTMX adoption requires an ADR and official documentation review.

## Wagtail modeling

Use:
- Page models for URL-addressable editorial content;
- StreamField for intentionally flexible mixed content;
- snippets for reusable non-page editorial entities;
- structured blocks rather than free-form HTML;
- editor help text and previews where useful.

Avoid:
- giant unconstrained StreamFields for transactional data;
- using snippets merely because a model exists;
- duplicate content taxonomies.

## Search

Search should distinguish result domains:
- user's private household state;
- public recipes;
- public guides.

Do not leak another user's private data into search indexes/results.

Wagtail database search is acceptable for MVP content scale.

## Caching

Do not add caching until a measured need exists.

If caching is introduced:
- define invalidation;
- never cache private user data under a shared key;
- test cache isolation.

## Database

Development:
- SQLite acceptable for ease of setup.

Production-minded CI/deployment target:
- PostgreSQL preferred before project is declared production-ready.

Database-specific behavior must be covered by appropriate CI if adopted.

## Migrations

Rules:
- migrations are committed;
- `makemigrations --check` in CI;
- destructive migrations require explicit migration plan;
- data migrations must be reversible where practical;
- StreamField block changes must consider stored historical JSON.

## Settings

Configuration via environment for deployment-sensitive values.

Never commit:
- secret key;
- OAuth secrets;
- database credentials;
- API keys.

Use secure production settings rather than relying on development defaults.

## Observability

Minimum production-minded hooks:
- structured application logging;
- clear error logging;
- health endpoint before deployment;
- no sensitive values in logs.

Sentry-like external tooling is optional and should not be added without deployment need.

## Performance principles

1. Prevent N+1 queries.
2. Use `select_related/prefetch_related` intentionally.
3. Avoid querying per StreamField block in templates.
4. Paginate large editorial/search collections.
5. Keep frontend JS small.
6. Serve appropriately sized Wagtail image renditions.

Performance optimization must be evidence-based.

## Architecture review checklist

Before merge:
- Is the behavior in the correct app?
- Is Wagtail being used for editorial rather than transactional concerns?
- Is business logic outside templates/views?
- Are writes atomic where necessary?
- Is object ownership enforced at query boundary?
- Are actions idempotent where retry is plausible?
- Are migrations safe?
- Are queries bounded and efficient?
- Is framework customization using documented extension points?
