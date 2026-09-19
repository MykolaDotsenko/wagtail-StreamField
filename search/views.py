from django.template.response import TemplateResponse

from .selectors import discover_snapshot


def search(request):
    snapshot = discover_snapshot(
        query=request.GET.get("query"),
        kind=request.GET.get("kind"),
        user=request.user,
    )

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "snapshot": snapshot,
            "search_query": snapshot.query,
            "search_kind": snapshot.kind,
        },
    )
