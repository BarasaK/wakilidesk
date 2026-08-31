from django.urls import path

from notifications import views


urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("<uuid:notification_id>/read/", views.notification_mark_read, name="notification_mark_read"),
]
