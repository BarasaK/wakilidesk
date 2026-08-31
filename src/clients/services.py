from __future__ import annotations

from django.db import transaction

from audit.services import record_audit_event
from clients.models import Client


def clients_for_firm(firm):
    return Client.objects.filter(firm=firm)


def get_client_for_firm_or_404(firm, client_id):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(Client, id=client_id, firm=firm)


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


def next_client_number(firm) -> str:
    count = Client.objects.filter(firm=firm).count() + 1
    return f"CL-{count:05d}"
