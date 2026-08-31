from django.urls import path

from matters import views


urlpatterns = [
    path("", views.matter_list, name="matter_list"),
    path("new/", views.matter_create, name="matter_create"),
    path("practice-areas/", views.practice_area_list, name="practice_area_list"),
    path("practice-areas/new/", views.practice_area_create, name="practice_area_create"),
    path("practice-areas/<uuid:area_id>/edit/", views.practice_area_edit, name="practice_area_edit"),
    path("<uuid:matter_id>/", views.matter_detail, name="matter_detail"),
    path("<uuid:matter_id>/edit/", views.matter_edit, name="matter_edit"),
    path("<uuid:matter_id>/parties/new/", views.matter_party_create, name="matter_party_create"),
]
