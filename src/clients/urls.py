from django.urls import path

from clients import views


urlpatterns = [
    path("", views.client_list, name="client_list"),
    path("new/", views.client_create, name="client_create"),
    path("<uuid:client_id>/", views.client_detail, name="client_detail"),
    path("<uuid:client_id>/edit/", views.client_edit, name="client_edit"),
]
