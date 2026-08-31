from django.urls import path

from documents import views


urlpatterns = [
    path("", views.document_list, name="document_list"),
    path("upload/", views.document_upload, name="document_upload"),
    path("categories/", views.category_list, name="document_category_list"),
    path("categories/new/", views.category_create, name="document_category_create"),
    path("categories/<uuid:category_id>/edit/", views.category_edit, name="document_category_edit"),
    path("<uuid:document_id>/", views.document_detail, name="document_detail"),
    path("<uuid:document_id>/edit/", views.document_edit, name="document_edit"),
    path("<uuid:document_id>/versions/new/", views.document_version_upload, name="document_version_upload"),
    path("<uuid:document_id>/download/", views.document_download, name="document_download"),
    path("<uuid:document_id>/archive/", views.document_archive, name="document_archive"),
    path("<uuid:document_id>/restore/", views.document_restore, name="document_restore"),
]
