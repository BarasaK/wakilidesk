from django.urls import path

from diary import views


urlpatterns = [
    path("", views.diary_event_list, name="diary_event_list"),
    path("calendar/", views.diary_calendar, name="diary_calendar"),
    path("new/", views.diary_event_create, name="diary_event_create"),
    path("<uuid:event_id>/", views.diary_event_detail, name="diary_event_detail"),
    path("<uuid:event_id>/edit/", views.diary_event_edit, name="diary_event_edit"),
    path("<uuid:event_id>/status/<str:status>/", views.diary_event_status, name="diary_event_status"),
    path("<uuid:event_id>/delete/", views.diary_event_delete, name="diary_event_delete"),
]
