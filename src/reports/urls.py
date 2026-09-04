from django.urls import path

from reports import views


urlpatterns = [
    path("", views.report_index, name="report_index"),
    path("export/", views.report_export, name="report_export"),
]
