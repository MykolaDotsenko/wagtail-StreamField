from dataclasses import dataclass
from datetime import date

from django.urls import reverse
from django.utils import timezone

from blog.models import BlogPage
from household.models import MealPlanEntry, PantryItem, Routine, ShoppingItem
from recipes.models import RecipePage


SEARCH_KINDS = {"all", "recipes", "guides", "home"}
SEARCH_LIMIT_PER_GROUP = 8
DISCOVER_LIMIT_PER_GROUP = 6


@dataclass(frozen=True)
class PublicSearchResult:
    title: str
    summary: str
    href: str
    kind: str
    meta: str


@dataclass(frozen=True)
class HomeSearchResult:
    title: str
    detail: str
    href: str
    kind: str


@dataclass(frozen=True)
class DiscoverSnapshot:
    query: str
    kind: str
    recipe_results: tuple[PublicSearchResult, ...]
    guide_results: tuple[PublicSearchResult, ...]
    home_results: tuple[HomeSearchResult, ...]
    latest_recipes: tuple[PublicSearchResult, ...]
    latest_guides: tuple[PublicSearchResult, ...]

    @property
    def has_query(self) -> bool:
        return bool(self.query)

    @property
    def result_count(self) -> int:
        return len(self.recipe_results) + len(self.guide_results) + len(self.home_results)


def normalize_search_query(value: str | None) -> str:
    return " ".join((value or "").split())[:120]


def normalize_search_kind(value: str | None) -> str:
    return value if value in SEARCH_KINDS else "all"


def _recipe_result(recipe: RecipePage) -> PublicSearchResult:
    return PublicSearchResult(
        title=recipe.title,
        summary=recipe.intro,
        href=recipe.url,
        kind="Recipe",
        meta=f"{recipe.total_minutes} min · {recipe.get_difficulty_display()}",
    )


def _guide_result(guide: BlogPage) -> PublicSearchResult:
    return PublicSearchResult(
        title=guide.title,
        summary=guide.intro,
        href=guide.url,
        kind="Guide",
        meta=guide.get_guide_type_display(),
    )


def _public_recipe_search(query: str) -> tuple[PublicSearchResult, ...]:
    results = RecipePage.objects.live().search(query)[:SEARCH_LIMIT_PER_GROUP]
    return tuple(_recipe_result(recipe) for recipe in results)


def _public_guide_search(query: str) -> tuple[PublicSearchResult, ...]:
    results = BlogPage.objects.live().search(query)[:SEARCH_LIMIT_PER_GROUP]
    return tuple(_guide_result(guide) for guide in results)


def _latest_recipes() -> tuple[PublicSearchResult, ...]:
    recipes = RecipePage.objects.live().order_by("-first_published_at", "-pk")[
        :DISCOVER_LIMIT_PER_GROUP
    ]
    return tuple(_recipe_result(recipe) for recipe in recipes)


def _latest_guides() -> tuple[PublicSearchResult, ...]:
    guides = BlogPage.objects.live().order_by("-first_published_at", "-pk")[
        :DISCOVER_LIMIT_PER_GROUP
    ]
    return tuple(_guide_result(guide) for guide in guides)


def _home_search(*, user, query: str, today: date) -> tuple[HomeSearchResult, ...]:
    if user is None or not user.is_authenticated:
        return ()

    results = []

    shopping_items = ShoppingItem.objects.filter(
        user=user,
        status=ShoppingItem.Status.OPEN,
        deleted_at__isnull=True,
        name__icontains=query,
    ).order_by("name", "pk")[:SEARCH_LIMIT_PER_GROUP]
    for item in shopping_items:
        results.append(
            HomeSearchResult(
                title=item.name,
                detail=f"Shopping · {item.quantity} on your active list",
                href=reverse("household:shopping"),
                kind="Shopping",
            )
        )

    pantry_items = PantryItem.objects.filter(
        user=user,
        name__icontains=query,
    ).order_by("name", "pk")[:SEARCH_LIMIT_PER_GROUP]
    for item in pantry_items:
        expiry = (
            f"expires {item.expires_on:%b %d}"
            if item.expires_on is not None
            else "expiry unknown"
        )
        results.append(
            HomeSearchResult(
                title=item.name,
                detail=f"Pantry · {item.quantity_label} · {expiry}",
                href=reverse("household:pantry"),
                kind="Pantry",
            )
        )

    routines = Routine.objects.filter(
        user=user,
        active=True,
        title__icontains=query,
    ).order_by("due_on", "title", "pk")[:SEARCH_LIMIT_PER_GROUP]
    for routine in routines:
        results.append(
            HomeSearchResult(
                title=routine.title,
                detail=f"Home rhythm · due {routine.effective_due_on:%b %d}",
                href=reverse("household:routines"),
                kind="Routine",
            )
        )

    meals = MealPlanEntry.objects.filter(
        user=user,
        date__gte=today,
        name__icontains=query,
    ).order_by("date", "pk")[:SEARCH_LIMIT_PER_GROUP]
    for meal in meals:
        results.append(
            HomeSearchResult(
                title=meal.name,
                detail=f"Dinner plan · {meal.date:%a, %b %d}",
                href=f"{reverse('household:plan')}?week={meal.date:%Y-%m-%d}",
                kind="Dinner",
            )
        )

    normalized_query = query.casefold()
    results.sort(
        key=lambda result: (
            not result.title.casefold().startswith(normalized_query),
            result.title.casefold(),
            result.kind,
        )
    )
    return tuple(results[:SEARCH_LIMIT_PER_GROUP])


def discover_snapshot(*, query=None, kind=None, user=None, today=None) -> DiscoverSnapshot:
    query = normalize_search_query(query)
    kind = normalize_search_kind(kind)
    today = today or timezone.localdate()

    if not query:
        return DiscoverSnapshot(
            query="",
            kind=kind,
            recipe_results=(),
            guide_results=(),
            home_results=(),
            latest_recipes=_latest_recipes(),
            latest_guides=_latest_guides(),
        )

    recipes = _public_recipe_search(query) if kind in {"all", "recipes"} else ()
    guides = _public_guide_search(query) if kind in {"all", "guides"} else ()
    home = _home_search(user=user, query=query, today=today) if kind in {"all", "home"} else ()

    return DiscoverSnapshot(
        query=query,
        kind=kind,
        recipe_results=recipes,
        guide_results=guides,
        home_results=home,
        latest_recipes=(),
        latest_guides=(),
    )
