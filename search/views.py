from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from wagtail.models import Page


def search(request):
    search_query = request.GET.get("query")
    search_results = (
        Page.objects.live().search(search_query) if search_query else Page.objects.none()
    )
    paginator = Paginator(search_results, 10)

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": paginator.get_page(request.GET.get("page")),
        },
    )
