from django.urls import path

from physical_files import views


urlpatterns = [
    path("", views.physical_file_list, name="physical_file_list"),
    path("new/", views.physical_file_create, name="physical_file_create"),
    path("locations/", views.storage_location_list, name="storage_location_list"),
    path("locations/new/", views.storage_location_create, name="storage_location_create"),
    path("locations/<uuid:location_id>/edit/", views.storage_location_edit, name="storage_location_edit"),
    path("<uuid:physical_file_id>/", views.physical_file_detail, name="physical_file_detail"),
    path("<uuid:physical_file_id>/edit/", views.physical_file_edit, name="physical_file_edit"),
    path("<uuid:physical_file_id>/checkout/", views.physical_file_checkout, name="physical_file_checkout"),
    path("<uuid:physical_file_id>/checkin/", views.physical_file_checkin, name="physical_file_checkin"),
]
