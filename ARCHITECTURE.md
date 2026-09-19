# DomoNest architecture

DomoNest deliberately separates **editorial content** from **private household state**.

## System shape

```text
                           ┌──────────────────────┐
Editors ── Wagtail admin ─▶│ Pages / StreamField  │
                           │ Snippets / Images     │
                           └──────────┬───────────┘
                                      │
                                      ▼
Browser ───────────────────▶ Public content
   │                         recipes + guides
   │
   └── Django auth ─────────▶ Household planner
                              shopping / pantry
                              chores / meal plan
                                      │
                                      ▼
                                relational models
```

## Dependency rules

- Wagtail owns page composition, publishing, previews, search indexing and editorial images.
- Django models own authenticated household data.
- The planner may reference a published `RecipePage`; editorial pages never depend on a user's private planner state.
- Forms validate write boundaries. Views always scope household mutations to `request.user`.
- Templates remain server-rendered. JavaScript is progressive enhancement only.

## Why this architecture

The project is intentionally not a SPA. Shopping lists and household routines do not require a client state framework, API gateway or distributed backend. Django's request/response model makes ownership checks explicit and keeps the system small enough to inspect in one sitting.

Wagtail is used where its editorial model creates real value:

- reusable StreamField blocks
- grouped block picker
- snippets for household topics
- recipe and guide page types
- image renditions and accessibility-focused ImageBlock
- autosave / preview / revision publishing
- built-in search index integration

## Data model

### Editorial

- `HomePage` — flexible landing page composed from product blocks
- `BlogIndexPage` / `BlogPage` — practical household guide library
- `RecipeIndexPage` / `RecipePage` — structured recipes
- `HouseholdTopic` — reusable snippet taxonomy

The package is still named `blog` to preserve the repository's original migration history, but it now acts as the editorial content domain.

### Household

- `ShoppingItem`
- `PantryItem`
- `Chore`
- `MealPlanEntry`

Every household row belongs to a Django user. Meal slots are unique per user/date/type, so repeated saves update one authoritative slot rather than creating duplicates.

## Security boundaries

- planner routes require authentication
- mutations use POST + CSRF
- object lookup includes `user=request.user`
- production secrets come only from environment variables
- security-sensitive cookie/header defaults live in `settings/production.py`
- local SQLite data and uploaded media are ignored by Git

## UX approach

The UI uses semantic HTML and a small CSS design system instead of a frontend component dependency. Mobile receives persistent high-value shortcuts; desktop preserves more information density. Motion is bounded and disabled when `prefers-reduced-motion` is active.
