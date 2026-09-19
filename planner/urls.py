from django.urls import path

from . import views

app_name = "planner"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("toggle/<str:kind>/<int:pk>/", views.toggle_item, name="toggle_item"),
    path("delete/<str:kind>/<int:pk>/", views.delete_item, name="delete_item"),
]
