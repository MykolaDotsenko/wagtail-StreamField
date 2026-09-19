## User problem

<!-- What user problem / job-to-be-done does this PR solve? -->

## Scope

<!-- What changes are intentionally included? -->

## Non-goals

<!-- What is intentionally excluded? -->

## Handbook references

<!-- Link relevant docs/sections, e.g. docs/02_UX_RESEARCH_AND_FLOWS.md#flow-3--shopping -->

- Product:
- UX:
- UI:
- Architecture:
- Domain:
- Quality:
- Official docs:

## Acceptance criteria

- [ ] User-visible behavior matches the documented flow.
- [ ] Empty/loading/error states are defined where applicable.
- [ ] Mobile and keyboard behavior are covered where applicable.

## Domain invariants

<!-- State the invariants touched. If none, explain why. -->

## Security / privacy

- [ ] Private objects are owner/household scoped.
- [ ] State-changing browser actions use POST + CSRF.
- [ ] No secrets/private data are exposed or logged.
- [ ] Authorization behavior is tested where relevant.

## Accessibility

- [ ] Keyboard path verified.
- [ ] Focus behavior verified.
- [ ] Status is not color-only.
- [ ] Target sizes meet project/WCAG requirements.
- [ ] Reduced motion considered.
- [ ] Form labels/errors are programmatically associated.

## Data / migrations

- [ ] Migration impact reviewed.
- [ ] `makemigrations --check` passes.
- [ ] Backward/data migration behavior is documented where applicable.

## Tests

<!-- Commands + scenarios -->

- [ ] Domain/unit tests.
- [ ] Django integration tests.
- [ ] Wagtail tests where applicable.
- [ ] Browser/E2E for critical user flow where applicable.

## UI evidence

<!-- Add before/after or responsive screenshots for UI changes. -->

## Performance

<!-- Query count/N+1, JS/CSS weight, image behavior, or explain why impact is negligible. -->

## Documentation / ADR

- [ ] Handbook remains accurate.
- [ ] ADR added/updated for material decisions, or not required.

## Review checklist

- [ ] No business logic in templates.
- [ ] Views remain orchestration-focused.
- [ ] Multi-write invariants use transactions where needed.
- [ ] Retry/double-submit behavior considered.
- [ ] Official version-matched framework docs were checked.
- [ ] Scope remains reviewable and coherent.
