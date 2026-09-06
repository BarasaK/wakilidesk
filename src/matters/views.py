from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from documents.services import documents_visible_to_user
from firms.services import require_firm_permission, user_has_firm_permission
from matters.forms import MatterForm, MatterPartyForm, PracticeAreaForm
from matters.models import PracticeArea
from matters.services import (
    create_matter,
    create_matter_party,
    get_matter_for_user_or_404,
    get_trashed_matter_for_firm_or_404,
    matters_visible_to_user,
    permanently_delete_matter,
    restore_trashed_matter,
    trash_matter,
    trashed_matters_for_firm,
    update_matter,
)


@login_required
def matter_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_matter")
    matters = matters_visible_to_user(firm=firm, user=request.user)
    return render(request, "matters/list.html", {"firm": firm, "matters": matters})


@login_required
def matter_trash(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_matter")
    matters = trashed_matters_for_firm(firm)
    return render(request, "matters/trash.html", {"firm": firm, "matters": matters})


@login_required
def matter_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "create_matter")
    if request.method == "POST":
        form = MatterForm(request.POST, firm=firm)
        if form.is_valid():
            matter = create_matter(
                firm=firm,
                user=request.user,
                data=form.cleaned_data,
                request=request,
            )
            messages.success(request, "Matter created.")
            return redirect("matter_detail", matter_id=matter.id)
    else:
        form = MatterForm(firm=firm)
    return render(request, "matters/form.html", {"firm": firm, "form": form})


@login_required
def matter_detail(request, matter_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_matter")
    matter = get_matter_for_user_or_404(firm=firm, user=request.user, matter_id=matter_id)
    documents = (
        documents_visible_to_user(firm=firm, user=request.user).filter(matter=matter)
        if user_has_firm_permission(request.user, firm, "view_document")
        else []
    )
    return render(
        request,
        "matters/detail.html",
        {"firm": firm, "matter": matter, "documents": documents},
    )


@login_required
def matter_edit(request, matter_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_matter")
    matter = get_matter_for_user_or_404(firm=firm, user=request.user, matter_id=matter_id)
    if request.method == "POST":
        form = MatterForm(request.POST, firm=firm, instance=matter)
        if form.is_valid():
            update_matter(matter=matter, data=form.cleaned_data, request=request)
            messages.success(request, "Matter updated.")
            return redirect("matter_detail", matter_id=matter.id)
    else:
        form = MatterForm(firm=firm, instance=matter)
    return render(request, "matters/form.html", {"firm": firm, "matter": matter, "form": form})


@login_required
def matter_trash_move(request, matter_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_matter")
    matter = get_matter_for_user_or_404(firm=firm, user=request.user, matter_id=matter_id)
    if request.method == "POST":
        trash_matter(matter=matter, request=request)
        messages.success(request, "Matter moved to trash.")
    return redirect("matter_list")


@login_required
def matter_trash_restore(request, matter_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "restore_matter")
    matter = get_trashed_matter_for_firm_or_404(firm, matter_id)
    if request.method == "POST":
        try:
            restore_trashed_matter(matter=matter, request=request)
            messages.success(request, "Matter restored from trash.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("matter_trash")


@login_required
def matter_permanent_delete(request, matter_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_matter")
    if not user_has_firm_permission(request.user, firm, "manage_firm_settings"):
        return redirect("matter_trash")
    matter = get_trashed_matter_for_firm_or_404(firm, matter_id)
    if request.method == "POST":
        try:
            permanently_delete_matter(matter=matter, request=request)
            messages.success(request, "Matter permanently deleted.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("matter_trash")


@login_required
def matter_party_create(request, matter_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_matter")
    matter = get_matter_for_user_or_404(firm=firm, user=request.user, matter_id=matter_id)
    if request.method == "POST":
        form = MatterPartyForm(request.POST)
        if form.is_valid():
            create_matter_party(
                firm=firm,
                matter=matter,
                data=form.cleaned_data,
                request=request,
            )
            messages.success(request, "Matter party added.")
            return redirect("matter_detail", matter_id=matter.id)
    else:
        form = MatterPartyForm()
    return render(request, "matters/party_form.html", {"firm": firm, "matter": matter, "form": form})


@login_required
def practice_area_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    areas = firm.practice_areas.order_by("name")
    return render(request, "matters/practice_area_list.html", {"firm": firm, "areas": areas})


@login_required
def practice_area_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    if request.method == "POST":
        form = PracticeAreaForm(request.POST)
        if form.is_valid():
            area = form.save(commit=False)
            area.firm = firm
            area.save()
            messages.success(request, "Practice area created.")
            return redirect("practice_area_list")
    else:
        form = PracticeAreaForm()
    return render(request, "matters/practice_area_form.html", {"firm": firm, "form": form})


@login_required
def practice_area_edit(request, area_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    area = get_object_or_404(PracticeArea, id=area_id, firm=firm)
    if request.method == "POST":
        form = PracticeAreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, "Practice area updated.")
            return redirect("practice_area_list")
    else:
        form = PracticeAreaForm(instance=area)
    return render(
        request,
        "matters/practice_area_form.html",
        {"firm": firm, "form": form, "area": area},
    )


def _require_current_firm(request):
    if request.current_firm is None:
        return None
    return request.current_firm
