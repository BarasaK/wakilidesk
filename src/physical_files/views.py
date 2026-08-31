from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from firms.services import require_firm_permission
from physical_files.forms import CheckinForm, CheckoutForm, PhysicalFileForm, StorageLocationForm
from physical_files.models import StorageLocation
from physical_files.services import (
    checkin_physical_file,
    checkout_physical_file,
    create_physical_file,
    get_physical_file_for_firm_or_404,
    overdue_checkouts_for_firm,
    physical_files_for_firm,
    update_physical_file,
)


@login_required
def physical_file_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_physical_file")
    files = physical_files_for_firm(firm)
    overdue = overdue_checkouts_for_firm(firm)
    return render(request, "physical_files/list.html", {"firm": firm, "files": files, "overdue": overdue})


@login_required
def physical_file_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "create_physical_file")
    if request.method == "POST":
        form = PhysicalFileForm(request.POST, firm=firm)
        if form.is_valid():
            physical_file = create_physical_file(firm=firm, data=form.cleaned_data, request=request)
            messages.success(request, "Physical file created.")
            return redirect("physical_file_detail", physical_file_id=physical_file.id)
    else:
        form = PhysicalFileForm(firm=firm)
    return render(request, "physical_files/form.html", {"firm": firm, "form": form})


@login_required
def physical_file_detail(request, physical_file_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_physical_file")
    physical_file = get_physical_file_for_firm_or_404(firm, physical_file_id)
    return render(request, "physical_files/detail.html", {"firm": firm, "physical_file": physical_file})


@login_required
def physical_file_edit(request, physical_file_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "change_storage_location")
    physical_file = get_physical_file_for_firm_or_404(firm, physical_file_id)
    if request.method == "POST":
        form = PhysicalFileForm(request.POST, firm=firm, instance=physical_file)
        if form.is_valid():
            update_physical_file(physical_file=physical_file, firm=firm, data=form.cleaned_data, request=request)
            messages.success(request, "Physical file updated.")
            return redirect("physical_file_detail", physical_file_id=physical_file.id)
    else:
        form = PhysicalFileForm(firm=firm, instance=physical_file)
    return render(request, "physical_files/form.html", {"firm": firm, "form": form, "physical_file": physical_file})


@login_required
def physical_file_checkout(request, physical_file_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "checkout_physical_file")
    physical_file = get_physical_file_for_firm_or_404(firm, physical_file_id)
    if request.method == "POST":
        form = CheckoutForm(request.POST, firm=firm)
        if form.is_valid():
            try:
                checkout_physical_file(
                    physical_file=physical_file,
                    firm=firm,
                    user=request.user,
                    data=form.cleaned_data,
                    request=request,
                )
                messages.success(request, "Physical file checked out.")
                return redirect("physical_file_detail", physical_file_id=physical_file.id)
            except ValueError as exc:
                form.add_error(None, str(exc))
    else:
        form = CheckoutForm(firm=firm)
    return render(request, "physical_files/checkout.html", {"firm": firm, "physical_file": physical_file, "form": form})


@login_required
def physical_file_checkin(request, physical_file_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "checkin_physical_file")
    physical_file = get_physical_file_for_firm_or_404(firm, physical_file_id)
    if request.method == "POST":
        form = CheckinForm(request.POST)
        if form.is_valid():
            try:
                checkin_physical_file(
                    physical_file=physical_file,
                    firm=firm,
                    user=request.user,
                    notes=form.cleaned_data["notes"],
                    request=request,
                )
                messages.success(request, "Physical file checked in.")
                return redirect("physical_file_detail", physical_file_id=physical_file.id)
            except ValueError as exc:
                form.add_error(None, str(exc))
    else:
        form = CheckinForm()
    return render(request, "physical_files/checkin.html", {"firm": firm, "physical_file": physical_file, "form": form})


@login_required
def storage_location_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "change_storage_location")
    locations = firm.storage_locations.select_related("parent").order_by("name")
    return render(request, "physical_files/location_list.html", {"firm": firm, "locations": locations})


@login_required
def storage_location_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "change_storage_location")
    if request.method == "POST":
        form = StorageLocationForm(request.POST, firm=firm)
        if form.is_valid():
            location = form.save(commit=False)
            location.firm = firm
            location.save()
            messages.success(request, "Storage location created.")
            return redirect("storage_location_list")
    else:
        form = StorageLocationForm(firm=firm)
    return render(request, "physical_files/location_form.html", {"firm": firm, "form": form})


@login_required
def storage_location_edit(request, location_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "change_storage_location")
    location = get_object_or_404(StorageLocation, id=location_id, firm=firm)
    if request.method == "POST":
        form = StorageLocationForm(request.POST, firm=firm, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, "Storage location updated.")
            return redirect("storage_location_list")
    else:
        form = StorageLocationForm(firm=firm, instance=location)
    return render(request, "physical_files/location_form.html", {"firm": firm, "form": form, "location": location})


def _require_current_firm(request):
    return request.current_firm
