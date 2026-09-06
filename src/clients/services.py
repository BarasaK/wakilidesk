from __future__ import annotations

from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone

from audit.services import record_audit_event
from clients.models import Client


def clients_for_firm(firm):
    return Client.objects.filter(firm=firm, deleted_at__isnull=True)


def trashed_clients_for_firm(firm):
    return Client.objects.filter(firm=firm, deleted_at__isnull=False).order_by("-deleted_at", "name")


def get_client_for_firm_or_404(firm, client_id):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(clients_for_firm(firm), id=client_id)


def get_trashed_client_for_firm_or_404(firm, client_id):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(trashed_clients_for_firm(firm), id=client_id)


@transaction.atomic
def create_client(*, firm, user, data, request=None) -> Client:
    client = Client.objects.create(
        firm=firm,
        created_by=user,
        client_number=next_client_number(firm),
        **data,
    )
    record_audit_event(
        request=request,
        firm=firm,
        user=user,
        action="client_created",
        object_type="Client",
        object_id=client.id,
    )
    return client


@transaction.atomic
def update_client(*, client: Client, data, request=None) -> Client:
    for field, value in data.items():
        setattr(client, field, value)
    client.save()
    record_audit_event(
        request=request,
        firm=client.firm,
        action="client_updated",
        object_type="Client",
        object_id=client.id,
    )
    return client


@transaction.atomic
def trash_client(*, client: Client, request=None) -> Client:
    client.deleted_at = timezone.now()
    client.save(update_fields=["deleted_at", "updated_at"])
    record_audit_event(
        request=request,
        firm=client.firm,
        action="client_moved_to_trash",
        object_type="Client",
        object_id=client.id,
    )
    return client


@transaction.atomic
def restore_trashed_client(*, client: Client, request=None) -> Client:
    client.deleted_at = None
    client.save(update_fields=["deleted_at", "updated_at"])
    record_audit_event(
        request=request,
        firm=client.firm,
        action="client_restored_from_trash",
        object_type="Client",
        object_id=client.id,
    )
    return client


@transaction.atomic
def permanently_delete_client(*, client: Client, request=None) -> None:
    firm = client.firm
    client_id = client.id
    try:
        client.delete()
    except ProtectedError as exc:
        raise ValueError("Client cannot be permanently deleted while linked matters exist.") from exc
    record_audit_event(
        request=request,
        firm=firm,
        action="client_permanently_deleted",
        object_type="Client",
        object_id=client_id,
    )


def next_client_number(firm) -> str:
    count = Client.objects.filter(firm=firm).count() + 1
    return f"CL-{count:05d}"
