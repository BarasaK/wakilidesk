from django.urls import path

from documents import views


urlpatterns = [
    path("", views.document_list, name="document_list"),
    path("upload/", views.document_upload, name="document_upload"),
    path("trash/", views.document_trash, name="document_trash"),
    path("categories/", views.category_list, name="document_category_list"),
    path("categories/new/", views.category_create, name="document_category_create"),
    path("categories/<uuid:category_id>/edit/", views.category_edit, name="document_category_edit"),
    path("<uuid:document_id>/", views.document_detail, name="document_detail"),
    path("<uuid:document_id>/edit/", views.document_edit, name="document_edit"),
    path("<uuid:document_id>/versions/new/", views.document_version_upload, name="document_version_upload"),
    path("<uuid:document_id>/download/", views.document_download, name="document_download"),
    path("<uuid:document_id>/archive/", views.document_archive, name="document_archive"),
    path("<uuid:document_id>/restore/", views.document_restore, name="document_restore"),
    path("<uuid:document_id>/trash/", views.document_trash_move, name="document_trash_move"),
    path("<uuid:document_id>/trash/restore/", views.document_trash_restore, name="document_trash_restore"),
    path("<uuid:document_id>/trash/delete/", views.document_permanent_delete, name="document_permanent_delete"),
    path("<uuid:document_id>/reprocess-ocr/", views.document_reprocess_ocr, name="document_reprocess_ocr"),
]
