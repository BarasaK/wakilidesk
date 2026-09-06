from django.urls import path

from matters import views


urlpatterns = [
    path("", views.matter_list, name="matter_list"),
    path("trash/", views.matter_trash, name="matter_trash"),
    path("new/", views.matter_create, name="matter_create"),
    path("practice-areas/", views.practice_area_list, name="practice_area_list"),
    path("practice-areas/new/", views.practice_area_create, name="practice_area_create"),
    path("practice-areas/<uuid:area_id>/edit/", views.practice_area_edit, name="practice_area_edit"),
    path("<uuid:matter_id>/", views.matter_detail, name="matter_detail"),
    path("<uuid:matter_id>/edit/", views.matter_edit, name="matter_edit"),
    path("<uuid:matter_id>/trash/", views.matter_trash_move, name="matter_trash_move"),
    path("<uuid:matter_id>/trash/restore/", views.matter_trash_restore, name="matter_trash_restore"),
    path("<uuid:matter_id>/trash/delete/", views.matter_permanent_delete, name="matter_permanent_delete"),
    path("<uuid:matter_id>/parties/new/", views.matter_party_create, name="matter_party_create"),
]
