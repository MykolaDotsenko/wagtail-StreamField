from django.urls import path

from . import views

app_name = "household"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("shopping/<int:pk>/toggle/", views.toggle_shopping, name="toggle_shopping"),
    path("chores/<int:pk>/toggle/", views.toggle_chore, name="toggle_chore"),
    path("<str:kind>/<int:pk>/delete/", views.delete_item, name="delete_item"),
]
