# DomoNest — Django + Wagtail Household Hub

**A modern household organizer that demonstrates how Django product logic and Wagtail editorial tooling can live in one deliberately simple system.**

DomoNest turns the original Wagtail tutorial repository into a portfolio case study with two clear responsibilities:

- **private household planning** — meals, shopping, pantry stock and recurring home routines;
- **editor-curated knowledge** — flexible home guides and structured recipes built in Wagtail.

## Why this project exists

A useful household app should reduce mental load, not create another dashboard to maintain. The product is therefore designed around short, high-frequency flows: add an item, mark a chore done, plan one meal, notice food that needs attention.

The engineering follows the same rule: use Wagtail where editorial flexibility matters, Django models where private relational state matters, and avoid a frontend framework when server-rendered HTML already solves the product.

## Product capabilities

### Household planner

- 7-day meal plan with one authoritative breakfast/lunch/dinner slot
- recipes from Wagtail or lightweight custom meals
- shopping list with quantities, categories and completion state
- pantry inventory with expiry and low-stock signals
- recurring / one-off home routines organised by room
- user ownership enforced on every planner mutation
- built-in Django authentication and self-service signup

### Wagtail content studio

- Wagtail **7.4 LTS**
- grouped StreamField page builder for the homepage
- flexible guide blocks: checklist, steps, tip callouts, rich text, embeds and images
- accessibility-focused Wagtail `ImageBlock` for new editorial media
- structured recipe page type with ingredients, steps, timings, servings and meal type
- reusable `HouseholdTopic` snippets
- featured content curation
- Wagtail revisions, preview, publishing and autosave
- integrated content search

### Frontend

- responsive, mobile-first household dashboard
- compact mobile action dock
- calm warm/sage visual system
- semantic landmarks and native controls
- visible keyboard focus
- reduced-motion and forced-colors support
- no frontend runtime dependency

## Stack

- Python 3.12
- **Django 5.2.17 LTS**
- **Wagtail 7.4.3 LTS**
- SQLite for local evaluation
- WhiteNoise + Gunicorn production baseline
- semantic Django templates + modern CSS
- Django TestCase / SimpleTestCase
- Ruff
- Coverage.py
- GitHub Actions

## Architecture

```text
Wagtail admin
   ↓
Pages + StreamField + Snippets ──────▶ public recipes / guides
                                             │
                                             │ selectable recipe
                                             ▼
Django auth ──▶ planner views ──▶ household models
                              user-scoped writes
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the boundaries and trade-offs.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python manage.py migrate
python manage.py bootstrap_demo
python manage.py createsuperuser
python manage.py runserver
```

Open:

- product: `http://127.0.0.1:8000/`
- household planner: `http://127.0.0.1:8000/planner/`
- Wagtail editor: `http://127.0.0.1:8000/admin/`

`bootstrap_demo` is idempotent. It creates the DomoNest page tree plus one practical guide and one recipe without overwriting an editor's existing StreamField homepage content.

## Quality gate

```bash
ruff check .
python manage.py makemigrations --check --dry-run
python manage.py check
coverage run manage.py test
coverage report
python manage.py collectstatic --noinput
```

The same gate runs in GitHub Actions on pull requests and feature branches.

## Important implementation decisions

### Keep the old HomePage field instead of destructively converting it

The original tutorial stored homepage content in `RichTextField`. DomoNest keeps that field for data compatibility and adds a new StreamField page-builder field. Editors see the modern field; old databases do not require risky content conversion.

### Keep the historical `blog` package name

The editorial domain is no longer a generic blog, but renaming a Django app with existing migration history adds complexity without user value. Public concepts are now guides, recipes and household topics; the internal package name remains stable.

### Household data does not live in Wagtail pages

Shopping items, chores and meal slots are private user data with different ownership and lifecycle rules from editorial content. They are plain Django models and cannot accidentally enter the public page tree.

## Scope

DomoNest is a portfolio product, not a commercial multi-household collaboration platform. A production SaaS would additionally need email verification, password-reset delivery, shared household membership/roles, observability, PostgreSQL, background reminders, audit events and deployment-specific backup/restore.

The current scope is intentionally chosen to demonstrate **modern Wagtail, solid Django boundaries, useful product logic and high-ROI UI/UX without architectural theatre**.
