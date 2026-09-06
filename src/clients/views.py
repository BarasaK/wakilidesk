from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from clients.forms import ClientForm
from clients.services import (
    create_client,
    get_client_for_firm_or_404,
    get_trashed_client_for_firm_or_404,
    permanently_delete_client,
    restore_trashed_client,
    trash_client,
    trashed_clients_for_firm,
    update_client,
)
from firms.services import require_firm_permission, user_has_firm_permission


@login_required
def client_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_client")
    clients = firm.clients.filter(deleted_at__isnull=True).order_by("name")
    return render(request, "clients/list.html", {"firm": firm, "clients": clients})


@login_required
def client_trash(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_client")
    clients = trashed_clients_for_firm(firm)
    return render(request, "clients/trash.html", {"firm": firm, "clients": clients})


@login_required
def client_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "create_client")
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = create_client(
                firm=firm,
                user=request.user,
                data=form.cleaned_data,
                request=request,
            )
            messages.success(request, "Client created.")
            return redirect("client_detail", client_id=client.id)
    else:
        form = ClientForm()
    return render(request, "clients/form.html", {"firm": firm, "form": form})


@login_required
def client_detail(request, client_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_client")
    client = get_client_for_firm_or_404(firm, client_id)
    matters = client.matters.filter(
        firm=firm,
        deleted_at__isnull=True,
    ).order_by("-opened_date", "matter_number")
    return render(
        request,
        "clients/detail.html",
        {"firm": firm, "client": client, "matters": matters},
    )


@login_required
def client_edit(request, client_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_client")
    client = get_client_for_firm_or_404(firm, client_id)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            update_client(client=client, data=form.cleaned_data, request=request)
            messages.success(request, "Client updated.")
            return redirect("client_detail", client_id=client.id)
    else:
        form = ClientForm(instance=client)
    return render(request, "clients/form.html", {"firm": firm, "client": client, "form": form})


@login_required
def client_trash_move(request, client_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_client")
    client = get_client_for_firm_or_404(firm, client_id)
    if request.method == "POST":
        trash_client(client=client, request=request)
        messages.success(request, "Client moved to trash.")
    return redirect("client_list")


@login_required
def client_trash_restore(request, client_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "restore_client")
    client = get_trashed_client_for_firm_or_404(firm, client_id)
    if request.method == "POST":
        restore_trashed_client(client=client, request=request)
        messages.success(request, "Client restored from trash.")
    return redirect("client_trash")


@login_required
def client_permanent_delete(request, client_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_client")
    if not user_has_firm_permission(request.user, firm, "manage_firm_settings"):
        return redirect("client_trash")
    client = get_trashed_client_for_firm_or_404(firm, client_id)
    if request.method == "POST":
        try:
            permanently_delete_client(client=client, request=request)
            messages.success(request, "Client permanently deleted.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("client_trash")


def _require_current_firm(request):
    if request.current_firm is None:
        return None
    return request.current_firm
