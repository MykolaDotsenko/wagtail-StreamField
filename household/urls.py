from django.urls import path

from . import views

app_name = "household"

urlpatterns = [
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
