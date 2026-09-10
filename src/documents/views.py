from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from documents.forms import (
    DocumentCategoryForm,
    DocumentMetadataForm,
    DocumentUploadForm,
    DocumentVersionUploadForm,
)
from documents.models import DocumentCategory
from documents.services import (
    archive_document,
    create_document_version,
    create_document_with_version,
    document_file_response,
    documents_visible_to_user,
    get_document_for_user_or_404,
    get_trashed_document_for_user_or_404,
    permanently_delete_document,
    restore_document,
    restore_trashed_document,
    schedule_text_extraction,
    trash_document,
    trashed_documents_visible_to_user,
    update_document_metadata,
)
from firms.services import require_firm_permission


@login_required
def document_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_document")
    documents = documents_visible_to_user(firm=firm, user=request.user)
    return render(request, "documents/list.html", {"firm": firm, "documents": documents})


@login_required
def document_trash(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_document")
    documents = trashed_documents_visible_to_user(firm=firm, user=request.user)
    return render(request, "documents/trash.html", {"firm": firm, "documents": documents})


@login_required
def document_upload(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "upload_document")
    navigation = _document_upload_navigation(request)
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES, firm=firm, user=request.user)
        if form.is_valid():
            try:
                document = create_document_with_version(
                    firm=firm,
                    user=request.user,
                    data=form.cleaned_data,
                    uploaded_file=form.cleaned_data["file"],
                    request=request,
                )
                messages.success(request, "Document uploaded.")
                if navigation["return_to"] == "matter":
                    return redirect("matter_detail", matter_id=document.matter_id)
                return redirect("document_detail", document_id=document.id)
            except ValueError as exc:
                form.add_error(None, str(exc))
    else:
        form = DocumentUploadForm(
            firm=firm,
            user=request.user,
            initial={"matter": navigation["matter_id"]} if navigation["matter_id"] else None,
        )
    return render(
        request,
        "documents/upload.html",
        {"firm": firm, "form": form, **navigation},
    )


@login_required
def document_detail(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_document")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    return render(request, "documents/detail.html", {"firm": firm, "document": document})


@login_required
def document_edit(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_document_metadata")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        form = DocumentMetadataForm(request.POST, firm=firm, instance=document)
        if form.is_valid():
            try:
                update_document_metadata(document=document, firm=firm, data=form.cleaned_data, request=request)
                messages.success(request, "Document metadata updated.")
                return redirect("document_detail", document_id=document.id)
            except ValueError as exc:
                form.add_error(None, str(exc))
    else:
        form = DocumentMetadataForm(firm=firm, instance=document)
    return render(request, "documents/edit.html", {"firm": firm, "document": document, "form": form})


@login_required
def document_version_upload(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "create_document_version")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        form = DocumentVersionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            create_document_version(
                document=document,
                firm=firm,
                user=request.user,
                uploaded_file=form.cleaned_data["file"],
                request=request,
            )
            messages.success(request, "New document version uploaded.")
            return redirect("document_detail", document_id=document.id)
    else:
        form = DocumentVersionUploadForm()
    return render(request, "documents/version_upload.html", {"firm": firm, "document": document, "form": form})


@login_required
def document_download(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "download_document")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    return document_file_response(document=document, firm=firm, request=request)


@login_required
def document_archive(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "archive_document")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        archive_document(document=document, firm=firm, request=request)
        messages.success(request, "Document archived.")
    return redirect("document_detail", document_id=document.id)


@login_required
def document_restore(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "restore_document")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        restore_document(document=document, firm=firm, request=request)
        messages.success(request, "Document restored.")
    return redirect("document_detail", document_id=document.id)


@login_required
def document_trash_move(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_document")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        trash_document(document=document, firm=firm, request=request)
        messages.success(request, "Document moved to trash.")
        return redirect("document_list")
    return redirect("document_detail", document_id=document.id)


@login_required
def document_trash_restore(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "restore_document")
    document = get_trashed_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        restore_trashed_document(document=document, firm=firm, request=request)
        messages.success(request, "Document restored from trash.")
    return redirect("document_trash")


@login_required
def document_permanent_delete(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_document")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    document = get_trashed_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST":
        permanently_delete_document(document=document, firm=firm, request=request)
        messages.success(request, "Document permanently deleted.")
    return redirect("document_trash")


@login_required
def document_reprocess_ocr(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_document_metadata")
    document = get_document_for_user_or_404(firm=firm, user=request.user, document_id=document_id)
    if request.method == "POST" and document.current_version_id:
        schedule_text_extraction(document.current_version)
        messages.success(request, "Document text extraction queued.")
    return redirect("document_detail", document_id=document.id)


@login_required
def category_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    categories = firm.document_categories.order_by("name")
    return render(request, "documents/category_list.html", {"firm": firm, "categories": categories})


@login_required
def category_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    if request.method == "POST":
        form = DocumentCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.firm = firm
            category.save()
            messages.success(request, "Document category created.")
            return redirect("document_category_list")
    else:
        form = DocumentCategoryForm()
    return render(request, "documents/category_form.html", {"firm": firm, "form": form})


@login_required
def category_edit(request, category_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    category = get_object_or_404(DocumentCategory, id=category_id, firm=firm)
    if request.method == "POST":
        form = DocumentCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Document category updated.")
            return redirect("document_category_list")
    else:
        form = DocumentCategoryForm(instance=category)
    return render(request, "documents/category_form.html", {"firm": firm, "form": form, "category": category})


def _require_current_firm(request):
    return request.current_firm


def _document_upload_navigation(request):
    matter_id = request.POST.get("matter") or request.GET.get("matter")
    return_to = request.POST.get("return_to") or request.GET.get("return_to")
    if return_to == "matter" and matter_id:
        return {
            "return_to": "matter",
            "matter_id": matter_id,
            "back_url": reverse("matter_detail", args=[matter_id]),
            "back_label": "Back to matter",
        }
    return {
        "return_to": "documents",
        "matter_id": matter_id,
        "back_url": reverse("document_list"),
        "back_label": "Back to documents",
    }
