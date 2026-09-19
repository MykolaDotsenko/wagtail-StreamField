from django.urls import path

from . import views

app_name = "household"

urlpatterns = [
    path("shopping/", views.shopping, name="shopping"),
    path("shopping/<int:item_id>/toggle/", views.toggle_item, name="toggle_item"),
    path("shopping/<int:item_id>/delete/", views.delete_item, name="delete_item"),
    path("shopping/<int:item_id>/restore/", views.restore_item, name="restore_item"),
]
