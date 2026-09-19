from django.urls import path

from . import views

app_name = "household"

urlpatterns = [
    path("today/", views.today, name="today"),
    path("routines/", views.routines, name="routines"),
    path("routines/<int:routine_id>/edit/", views.edit_routine, name="edit_routine"),
    path(
        "routines/<int:routine_id>/complete/",
        views.complete_routine_view,
        name="complete_routine",
    ),
    path(
        "routines/<int:routine_id>/skip/",
        views.skip_routine_view,
        name="skip_routine",
    ),
    path(
        "routines/<int:routine_id>/postpone/",
        views.postpone_routine_view,
        name="postpone_routine",
    ),
    path(
        "routines/<int:routine_id>/archive/",
        views.archive_routine_view,
        name="archive_routine",
    ),
    path("pantry/", views.pantry, name="pantry"),
    path("pantry/<int:item_id>/edit/", views.edit_pantry_item, name="edit_pantry_item"),
    path("pantry/<int:item_id>/delete/", views.remove_pantry_item, name="remove_pantry_item"),
    path(
        "pantry/<int:item_id>/add-to-shopping/",
        views.pantry_to_shopping,
        name="pantry_to_shopping",
    ),
    path("shopping/", views.shopping, name="shopping"),
    path("shopping/<int:item_id>/toggle/", views.toggle_item, name="toggle_item"),
    path("shopping/<int:item_id>/delete/", views.delete_item, name="delete_item"),
    path("shopping/<int:item_id>/restore/", views.restore_item, name="restore_item"),
]
