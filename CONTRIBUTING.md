# Contributing to DomoNest

DomoNest uses a documentation-led engineering workflow.

Start with [docs/00_INDEX.md](./docs/00_INDEX.md).

## Before coding

1. Identify the user problem.
2. Read the relevant handbook sections.
3. Check version-matched official Django/Wagtail documentation.
4. Define acceptance criteria and domain invariants.
5. Keep the PR scoped to one coherent capability.

## Implementation expectations

- Prefer simple, explicit Python.
- Keep domain rules out of templates.
- Keep views thin.
- Use services for multi-model operations.
- Scope private data at the query boundary.
- Use database constraints for invariants the database can enforce.
- Use transactions for atomic multi-write operations.
- Preserve server-rendered behavior as the baseline.
- Add JavaScript only when it improves the documented UX.
- Accessibility is a functional requirement.

## Before opening a PR

Run the available project checks and complete the repository PR template.

A PR is incomplete when it changes intended behavior without updating the relevant source-of-truth document.

## Review priority

Review in this order:

1. Correctness / data integrity.
2. Security / privacy.
3. Accessibility.
4. User task completion.
5. Simplicity / maintainability.
6. Performance.
7. Visual polish.

## Architectural decisions

Use [docs/09_ADR_LOG.md](./docs/09_ADR_LOG.md) for decisions that:
- affect multiple apps;
- introduce infrastructure/framework dependencies;
- change a core domain model;
- are expensive to reverse;
- intentionally diverge from an established project rule.
