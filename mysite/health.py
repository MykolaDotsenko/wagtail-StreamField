from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


@require_safe
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            ready = cursor.fetchone() == (1,)
    except DatabaseError:
        ready = False

    response = JsonResponse(
        {"status": "ok" if ready else "unavailable"},
        status=200 if ready else 503,
    )
    response["Cache-Control"] = "no-store"
    return response
