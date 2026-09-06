from django.urls import path

from clients import views


urlpatterns = [
    path("", views.client_list, name="client_list"),
    path("trash/", views.client_trash, name="client_trash"),
    path("new/", views.client_create, name="client_create"),
    path("<uuid:client_id>/", views.client_detail, name="client_detail"),
    path("<uuid:client_id>/edit/", views.client_edit, name="client_edit"),
    path("<uuid:client_id>/trash/", views.client_trash_move, name="client_trash_move"),
    path("<uuid:client_id>/trash/restore/", views.client_trash_restore, name="client_trash_restore"),
    path("<uuid:client_id>/trash/delete/", views.client_permanent_delete, name="client_permanent_delete"),
]
