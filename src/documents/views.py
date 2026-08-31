from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    documents_for_firm,
    get_document_for_firm_or_404,
    restore_document,
    update_document_metadata,
)
from firms.services import require_firm_permission


@login_required
def document_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_document")
    documents = documents_for_firm(firm)
    return render(request, "documents/list.html", {"firm": firm, "documents": documents})


@login_required
def document_upload(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "upload_document")
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES, firm=firm)
        if form.is_valid():
            document = create_document_with_version(
                firm=firm,
                user=request.user,
                data=form.cleaned_data,
                uploaded_file=form.cleaned_data["file"],
                request=request,
            )
            messages.success(request, "Document uploaded.")
            return redirect("document_detail", document_id=document.id)
    else:
        form = DocumentUploadForm(firm=firm)
    return render(request, "documents/upload.html", {"firm": firm, "form": form})


@login_required
def document_detail(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_document")
    document = get_document_for_firm_or_404(firm, document_id)
    return render(request, "documents/detail.html", {"firm": firm, "document": document})


@login_required
def document_edit(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_document_metadata")
    document = get_document_for_firm_or_404(firm, document_id)
    if request.method == "POST":
        form = DocumentMetadataForm(request.POST, firm=firm, instance=document)
        if form.is_valid():
            update_document_metadata(document=document, firm=firm, data=form.cleaned_data, request=request)
            messages.success(request, "Document metadata updated.")
            return redirect("document_detail", document_id=document.id)
    else:
        form = DocumentMetadataForm(firm=firm, instance=document)
    return render(request, "documents/edit.html", {"firm": firm, "document": document, "form": form})


@login_required
def document_version_upload(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "create_document_version")
    document = get_document_for_firm_or_404(firm, document_id)
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
    document = get_document_for_firm_or_404(firm, document_id)
    return document_file_response(document=document, firm=firm, request=request)


@login_required
def document_archive(request, document_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "archive_document")
    document = get_document_for_firm_or_404(firm, document_id)
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
    document = get_document_for_firm_or_404(firm, document_id)
    if request.method == "POST":
        restore_document(document=document, firm=firm, request=request)
        messages.success(request, "Document restored.")
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
